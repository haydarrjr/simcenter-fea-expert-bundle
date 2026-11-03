"""Config-driven bundle build tool. All bundle values live in bundle.config.json."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import importlib.util
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable

try:
    from scripts.harden_integration import transform as harden_skill, transform_recipe, POLICY_VERSION
except ModuleNotFoundError:
    from harden_integration import transform as harden_skill, transform_recipe, POLICY_VERSION

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "bundle.config.json"
CFG: dict[str, Any] = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
LOCK_PATH = ROOT / "source.lock.json"
MANIFEST_PATH = ROOT / ".sim-ai-agents.toml"
WORK_DIR = ROOT / ".work"
HOOK_PATH = ROOT / "scripts" / "stage_skills.py"

BUNDLE_ID: str = CFG["bundle"]["id"]
BUNDLE_NAME: str = CFG["bundle"]["name"]
BUNDLE_VERSION: str = CFG["bundle"]["version"]
SIDECAR_NAME: str = CFG["sidecar_name"]
ARTIFACT_NAME: str = CFG["artifact_name"]
ARTIFACT_REL = Path("dist") / BUNDLE_ID / BUNDLE_VERSION / ARTIFACT_NAME
ALLOWED_SOURCE_SUFFIXES = set(CFG["allowed_suffixes"])
FORBIDDEN_SUFFIXES = set(CFG["forbidden_suffixes"])
CREDENTIAL_RE = re.compile(CFG["credential_re"])
LOCAL_PATH_RE = re.compile(CFG["local_path_re"])
TRAINING_ID_RE = re.compile(CFG["training_id_re"])
COPYRIGHT_RE = re.compile(CFG["copyright_re"])
ALLOWLIST_RES = [re.compile(p) for p in CFG.get("scan_allowlist", [])]


def fail(message: str) -> None:
    raise RuntimeError(message)


# ---- config-derived paths (dynamic so tests can repoint ROOT) -------------
def recipe_path() -> Path:
    return ROOT / CFG["recipe"]


def subrecipes_dir() -> Path:
    return ROOT / CFG["subrecipes_dir"]


def subrecipe_paths() -> list[Path]:
    return [subrecipes_dir() / n for n in CFG["subrecipes"]]


def readme_path() -> Path:
    return ROOT / CFG["readme_dir"] / CFG["readme_file"]


def overlay_dir() -> Path:
    return ROOT / CFG["overlay_dir"]


def integration_files() -> dict[str, Path]:
    """Return only pinned official files; fail on missing/tampered or extra payloads."""
    rel = CFG.get("integration_receipt")
    if not rel:
        return {}
    receipt_path = ROOT / rel
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    base = ROOT / CFG["integration_root"]
    expected = receipt["files"]
    actual = {p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file() and p != receipt_path}
    if actual != set(expected):
        fail("Official integration file set mismatch")
    files = {}
    for name, sha in expected.items():
        if ".." in PurePosixPath(name).parts or PurePosixPath(name).is_absolute():
            fail("Unsafe integration path")
        path = base / name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            fail(f"Official integration SHA256 mismatch: {name}")
        files[name] = path
    return files


def archive_payload_map() -> dict[str, Path]:
    """Archive name -> source file for all non-skill payloads."""
    mapping = {f"recipes/{recipe_path().name}": recipe_path()}
    for p in subrecipe_paths():
        mapping[f"recipes/subrecipes/{p.name}"] = p
    mapping[f"readme/{CFG['readme_file']}"] = readme_path()
    for name, path in integration_files().items():
        if name.startswith("recipes/"):
            mapping[name] = path
        elif name.startswith("mcps/"):
            mapping[CFG["integration_mcp_map"][name]] = path
    return mapping


def payload_bytes(name: str, path: Path) -> bytes:
    data = path.read_bytes()
    if CFG.get("integration_root") and path.is_relative_to(ROOT / CFG["integration_root"]):
        return transform_recipe(name, data)
    return data


def integration_evidence() -> dict[str, Any]:
    source = integration_files()
    return {"policy_version": POLICY_VERSION, "files": {
        name: {"source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
               "packaged_sha256": hashlib.sha256(harden_skill(name, transform_recipe(name, path.read_bytes()))).hexdigest()}
        for name, path in source.items()}}


def run(command: list[str], *, env: dict[str, str] | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd or ROOT, env=env, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        detail = (result.stdout + "\n" + result.stderr).strip()
        fail(f"Command failed ({result.returncode}): {command[0]} {command[1:]}\n{detail}")
    return result


def git(*args: str, cwd: Path | None = None, strip: bool = True) -> str:
    output = run(["git", "-C", str(cwd or ROOT), *args]).stdout
    return output.strip() if strip else output


def read_lock() -> dict[str, Any]:
    return json.loads(LOCK_PATH.read_text(encoding="utf-8"))


def read_manifest() -> dict[str, Any]:
    return tomllib.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def git_bytes(repo: Path, spec: str) -> bytes:
    """Raw blob bytes (`git show <spec>`), independent of core.autocrlf and the working tree."""
    raw = subprocess.run(["git", "-C", str(repo), "show", spec], capture_output=True, check=False)
    if raw.returncode != 0:
        fail(f"Could not read git object {spec!r} in {repo}: {raw.stderr.decode('utf-8', 'replace').strip()}")
    return raw.stdout


def tracked_paths(repo: Path, *patterns: str) -> list[str]:
    raw = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-z", "--", *patterns],
        capture_output=True, check=False,
    )
    if raw.returncode != 0:
        fail(f"Could not read the git-tracked file set of {repo}.")
    return sorted(part.decode("utf-8") for part in raw.stdout.split(b"\0") if part)


# ---- staging hook ---------------------------------------------------------
def load_transform() -> Callable[[str, bytes], bytes] | None:
    if not HOOK_PATH.is_file():
        return None
    spec = importlib.util.spec_from_file_location("stage_skills", HOOK_PATH)
    if spec is None or spec.loader is None:
        fail("Cannot load scripts/stage_skills.py.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, "transform", None)
    if not callable(fn):
        fail("scripts/stage_skills.py must define transform(rel_path, data) -> bytes.")
    return fn


def apply_transform(rel: str, data: bytes, transform: Callable[[str, bytes], bytes] | None) -> bytes:
    """rel is the archive path, e.g. skills/<name>/SKILL.md. Only markdown is transformed."""
    if transform is None or not rel.casefold().endswith((".md", ".markdown")):
        return data
    out = transform(rel, data)
    if not isinstance(out, bytes):
        fail(f"transform() must return bytes: {rel}")
    return out


# ---- skill collection -----------------------------------------------------
def source_files(source: dict[str, Any]) -> list[str]:
    """Tracked files (repo-relative) under canonical_tree, minus excluded globs."""
    repo = ROOT / source["path"]
    tree = source["canonical_tree"]
    paths = tracked_paths(repo, tree)
    if not paths:
        fail(f"No tracked files under {tree} in {source['path']}.")
    globs = CFG["skill_exclude_globs"]
    kept = [p for p in paths if not any(fnmatch.fnmatchcase(p, g) for g in globs)]
    if "excluded_files" in source and len(paths) - len(kept) != int(source["excluded_files"]):
        fail(f"{source['path']}: expected {source['excluded_files']} excluded files, found {len(paths) - len(kept)}.")
    return kept


def _skill_dir_names(paths: list[str]) -> set[str]:
    return {PurePosixPath(p).parts[1] for p in paths if PurePosixPath(p).name == "SKILL.md" and len(PurePosixPath(p).parts) == 3}


def overlay_files() -> list[str]:
    odir = overlay_dir()
    if not odir.is_dir():
        return []
    rel_root = PurePosixPath(CFG["overlay_dir"].strip("/"))
    paths = tracked_paths(ROOT, str(rel_root))
    return [p for p in paths if p.startswith(rel_root.as_posix() + "/")]


def check_overlay_clean(*, development: bool = False) -> None:
    """Release mode refuses untracked or modified-but-unstaged overlay files; development warns."""
    odir = overlay_dir()
    if not odir.is_dir():
        return
    rel = CFG["overlay_dir"].strip("/")
    out = git("status", "--porcelain", "--untracked-files=all", "--", rel, strip=False)
    dirty = [line for line in out.splitlines() if len(line) > 3 and line[1] != " "]
    if not dirty:
        return
    msg = f"overlay has untracked or unstaged changes that would be ignored: {[l[3:] for l in dirty][:8]}"
    if development:
        print("WARNING: " + msg, file=sys.stderr)
    else:
        fail(msg + " (git add them or remove them; release packaging reads the index)")


def collect_skills(development: bool = False) -> dict[str, bytes]:
    """Return archive-relative (skills/<name>/...) -> staged (transformed) bytes.

    Source bytes come from git blobs at the locked commit and overlay bytes from the
    parent index, so results do not depend on core.autocrlf or working-tree state.
    """
    check_overlay_clean(development=development)
    transform = load_transform()
    staged: dict[str, bytes] = {}
    owner: dict[str, str] = {}
    lock = read_lock()
    for source in lock["sources"]:
        repo = ROOT / source["path"]
        files = source_files(source)
        if len(_skill_dir_names(files)) != int(source["expected_skill_directories"]):
            fail(f"{source['path']}: expected {source['expected_skill_directories']} skill directories, found {len(_skill_dir_names(files))}.")
        if len(files) != int(source["expected_skill_files"]):
            fail(f"{source['path']}: expected {source['expected_skill_files']} skill files, found {len(files)}.")
        for rel in files:
            path = repo.joinpath(*PurePosixPath(rel).parts)
            if path.is_symlink() or not path.is_file():
                fail(f"Skill source is not a regular file: {source['path']}/{rel}")
            if path.suffix.lower() not in ALLOWED_SOURCE_SUFFIXES:
                fail(f"Unsupported skill file type: {source['path']}/{rel}")
            if not rel.startswith("skills/"):
                fail(f"Skill path outside skills/: {rel}")
            staged[rel] = apply_transform(rel, git_bytes(repo, f"{source['commit']}:{rel}"), transform)
            owner[rel] = source["path"]
    replaces = set(CFG.get("overlay_replaces", []))
    source_names = {PurePosixPath(p).parts[1] for p in staged}
    overlay = overlay_files()
    overlay_names: set[str] = set()
    base = PurePosixPath(CFG["overlay_dir"].strip("/"))
    for rel in overlay:
        sub = PurePosixPath(rel).relative_to(base)
        name = sub.parts[0]
        if len(sub.parts) < 2:
            fail(f"Overlay file outside a skill directory: {rel}")
        overlay_names.add(name)
    collisions = (overlay_names & source_names) - replaces
    if collisions:
        fail(f"Overlay skills collide with source skills without overlay_replaces: {sorted(collisions)}")
    unused = replaces - overlay_names
    if unused and overlay:
        fail(f"overlay_replaces lists skills absent from the overlay: {sorted(unused)}")
    for name in sorted(overlay_names & replaces):
        if name not in source_names:
            fail(f"overlay_replaces names a skill not present in any source: {name}")
        for key in [k for k in staged if k.startswith(f"skills/{name}/")]:
            del staged[key]
    for rel in overlay:
        sub = PurePosixPath(rel).relative_to(base)
        path = ROOT.joinpath(*PurePosixPath(rel).parts)
        if path.is_symlink() or not path.is_file():
            fail(f"Overlay source is not a regular file: {rel}")
        if path.suffix.lower() not in ALLOWED_SOURCE_SUFFIXES:
            fail(f"Unsupported overlay file type: {rel}")
        arc = "skills/" + sub.as_posix()
        staged[arc] = apply_transform(arc, git_bytes(ROOT, f":{rel}"), transform)
    for name, path in integration_files().items():
        if name.startswith("skills/"):
            if name in staged:
                fail(f"Official skill collision: {name}")
            staged[name] = harden_skill(name, path.read_bytes())
    return dict(sorted(staged.items()))


def skill_names(staged: dict[str, bytes]) -> list[str]:
    return sorted({PurePosixPath(k).parts[1] for k in staged if PurePosixPath(k).name == "SKILL.md" and len(PurePosixPath(k).parts) == 3})


def validate_staged_skills(staged: dict[str, bytes]) -> None:
    """Validate frontmatter and relative links on the staged (transformed) markdown."""
    for rel, data in staged.items():
        if not rel.casefold().endswith((".md", ".markdown")):
            continue
        path = PurePosixPath(rel)
        if data.startswith(b"\xef\xbb\xbf"):
            fail(f"Markdown file starts with a UTF-8 BOM (remove it): {rel}")
        text = data.decode("utf-8").replace("\r\n", "\n")
        if path.name == "SKILL.md":
            if not text.startswith("---\n"):
                fail(f"Skill lacks YAML frontmatter: {rel}")
            end = text.find("\n---", 4)
            if end < 0:
                fail(f"Skill frontmatter is not closed: {rel}")
            header = text[4:end]
            name_match = re.search(r"(?m)^name:\s*(\S.*?)\s*$", header)
            description_match = re.search(r"(?m)^description:\s*(.*?)\s*$", header)
            if not name_match or name_match.group(1).strip() != path.parent.name:
                fail(f"Skill frontmatter name must equal directory name: {rel}")
            if not description_match or not 1 <= len(description_match.group(1).strip()) <= 1024:
                fail(f"Skill frontmatter description must be 1..1024 characters: {rel}")
            text = text[end + 4:]
        text = re.sub(r"(?ms)^```.*?^```\s*", "", text)
        for target in re.findall(r"!?(?:\[[^]]*\])\(((?:\\.|[^)])+)\)", text):
            target = target.strip().split(r' "', 1)[0].split(" '", 1)[0]
            target = re.sub(r"\\([\\()<>#])", r"\1", target)
            target = target.split("#", 1)[0].strip().strip("<>")
            if not target or re.match(r"(?i)(?:https?:|mailto:|data:)", target):
                continue
            if target.startswith("/"):
                fail(f"Markdown contains an absolute link: {rel}: {target}")
            parts: list[str] = list(path.parent.parts)
            for seg in target.split("/"):
                if seg == "..":
                    if not parts:
                        break
                    parts.pop()
                elif seg not in ("", "."):
                    parts.append(seg)
            if "/".join(parts) not in staged:
                fail(f"Markdown link target does not exist in the staged bundle: {rel}: {target}")


def staged_hashes(staged: dict[str, bytes]) -> dict[str, str]:
    return {k: hashlib.sha256(v).hexdigest() for k, v in staged.items()}


# ---- validation -----------------------------------------------------------
def validate_source_lock(*, development: bool = False) -> dict[str, Any]:
    lock = read_lock()
    sources = lock.get("sources")
    if not sources:
        fail("source.lock.json has no sources[].")
    for source in sources:
        repo = ROOT / source["path"]
        expected = str(source["commit"])
        actual = git("rev-parse", "HEAD", cwd=repo)
        if actual != expected:
            fail(f"{source['path']}: submodule revision mismatch: expected {expected}, got {actual}.")
        status = git("status", "--porcelain", "--untracked-files=all", cwd=repo, strip=False).strip("\n\r")
        if status and not development:
            fail(f"{source['path']}: submodule worktree is dirty; packaging refuses modified or untracked files.")
        if status and development:
            tree = source["canonical_tree"]
            for line in status.splitlines():
                p = line[3:].strip().split(" -> ")[-1]
                if not p.startswith(tree):
                    fail(f"{source['path']}: development packaging permits changes only beneath {tree}.")
        index_line = git("ls-files", "--stage", "--", source["path"])
        fields = index_line.split()
        if len(fields) < 3 or fields[0] != "160000" or fields[1] != expected:
            fail(f"The parent index does not pin {source['path']} at the locked commit.")
    staged = collect_skills(development=development)
    validate_staged_skills(staged)
    names = skill_names(staged)
    total = int(CFG["expected_total_skills"])
    computed = sum(int(s["expected_skill_directories"]) for s in sources)
    overlay_new = len(set(PurePosixPath(p).relative_to(PurePosixPath(CFG["overlay_dir"].strip("/"))).parts[0] for p in overlay_files())) if overlay_dir().is_dir() else 0
    if len(names) != total:
        fail(f"Expected {total} total skills, found {len(names)} (sources {computed}, overlay {overlay_new}, replaces {CFG.get('overlay_replaces', [])}).")
    return {"commits": {s["path"]: s["commit"] for s in sources}, "skill_names": names, "skill_hashes": staged_hashes(staged), "staged": staged}


def validate_manifest() -> dict[str, Any]:
    manifest = read_manifest()
    if manifest.get("schema_version") != "1":
        fail("Bundle manifest schema_version must be 1.")
    bundle = manifest.get("bundle", {})
    expected = {"id": BUNDLE_ID, "name": BUNDLE_NAME, "version": BUNDLE_VERSION, "os": CFG["bundle"]["os"]}
    for key, value in expected.items():
        if bundle.get(key) != value:
            fail(f"Unexpected bundle.{key}: expected {value!r}.")
    dependencies = manifest.get("dependencies")
    products = ["Simcenter 3D 2612"] if CFG.get("integration_root") else []
    if not isinstance(dependencies, dict) or dependencies.get("products") != products:
        fail("dependencies.products differs from the verified integration requirement.")
    mcps = manifest.get("mcps", [])
    if [m.get("name") for m in mcps] != CFG.get("manifest_mcp_names", []):
        fail("mcps names differ from the official integration contract")
    for m in mcps:
        if m.get("script_windows") not in CFG.get("integration_mcp_map", {}).values() or m.get("type") != "stdio" or m.get("timeout") != 180:
            fail("Invalid official mcps launcher/transport/timeout")
    if CFG.get("integration_root"):
        if manifest.get("compat") != {"product": "Simcenter 3D 2612", "shell": "*"}:
            fail("Official product compatibility missing")
    elif "compat" in manifest:
        fail("Do not declare unverified compat")
    if len(manifest.get("contacts", [])) < 1:
        fail("The bundle manifest requires a maintainer contact.")
    if manifest.get("contributions", []) != CFG["manifest_contributions"]:
        fail("Bundle contributions must be exactly the recipes, skills and readme entries from bundle.config.json.")
    return manifest


def _extension_blocks(text: str) -> list[dict[str, str]]:
    """Read the small, deliberately structural extension subset without a YAML dependency."""
    blocks: list[dict[str, str]] = []
    in_extensions = False
    current: dict[str, str] | None = None
    for line in text.splitlines():
        if re.match(r"^extensions:\s*$", line):
            in_extensions = True
            continue
        if in_extensions and line and not line.startswith(" ") and not line.startswith("-"):
            break
        if not in_extensions:
            continue
        match = re.match(r"^\s*-\s*type:\s*([^#]+?)\s*$", line)
        if match:
            if current:
                blocks.append(current)
            current = {"type": match.group(1).strip().strip("'\"")}
            continue
        match = re.match(r"^\s+([A-Za-z_][A-Za-z0-9_-]*):\s*([^#]*)$", line)
        if match and current is not None:
            current[match.group(1)] = match.group(2).strip().strip("'\"")
    if current:
        blocks.append(current)
    return blocks


def _sub_recipe_entries(text: str) -> list[tuple[str, str]]:
    """Sorted (name, normalized path) pairs of the top-level sub_recipes block."""
    entries: list[tuple[str, str]] = []
    in_block = False
    cur: dict[str, str] = {}

    def flush() -> None:
        if cur:
            entries.append((cur.get("name", ""), posixpath.normpath(cur.get("path", ""))))
        cur.clear()

    for line in text.splitlines():
        if re.match(r"^sub_recipes:\s*$", line):
            in_block = True
            continue
        if not in_block:
            continue
        if line and not line[0].isspace() and not line.startswith("-"):
            break
        m = re.match(r"^\s*-\s*([A-Za-z_]+):\s*([^#]*?)\s*$", line)
        if m and m.group(1) == "name":
            flush()
        m = m or re.match(r"^\s+([A-Za-z_]+):\s*([^#]*?)\s*$", line)
        if m:
            cur[m.group(1)] = m.group(2).strip().strip("'\"")
    flush()
    return sorted(entries)


def validate_recipe_source() -> None:
    rp = recipe_path()
    if not rp.is_file():
        fail(f"Main recipe is missing: {rp}")
    text = rp.read_text(encoding="utf-8")
    extensions = _extension_blocks(text)
    refs = {item.get("name") for item in extensions if item.get("type") == "ref"}
    for name in CFG["required_refs"]:
        if name not in refs:
            fail(f"Recipe must retain the explicit ref extension {name!r}.")
    platforms = {item.get("name", "").casefold() for item in extensions if item.get("type", "").casefold() == "platform"}
    if not {n.casefold() for n in CFG["required_platform_extensions"]}.issubset(platforms):
        fail(f"Recipe must include platform extensions {CFG['required_platform_extensions']}.")
    if re.search(r"(?m)^\s*available_tools\s*:", text):
        fail("Do not add available_tools before capturing the target AgentAI tools/list.")
    if recipe_path().stem != CFG["main_agent_name"]:
        fail(f"Main recipe file name must be {CFG['main_agent_name']}.yaml.")
    forbidden_builtin = {n.casefold() for n in CFG.get("forbidden_builtin_extensions", [])}
    for item in extensions:
        if item.get("type", "").casefold() == "builtin" and item.get("name", "").casefold() in forbidden_builtin:
            fail(f"Main recipe must not declare builtin extension {item.get('name')!r}.")
    allowed_refs = set(CFG["required_refs"]) | set(CFG.get("optional_refs", []))
    unknown_refs = sorted(n for n in refs if n not in allowed_refs)
    if unknown_refs:
        fail(f"Recipe declares ref extensions outside required+optional refs: {unknown_refs}")
    declared = _sub_recipe_entries(text)
    rec_dir = recipe_path().parent
    expected_subs = sorted(
        (Path(n).stem, os.path.relpath(subrecipes_dir() / n, rec_dir).replace("\\", "/"))
        for n in CFG["subrecipes"]
    )
    if declared != expected_subs:
        fail(f"Main recipe sub_recipes {declared} do not equal bundle.config.json subrecipes {expected_subs}.")
    tokens = CFG.get("forbidden_evidence_tokens", [])
    for rpath in [rp, *subrecipe_paths()]:
        if not rpath.is_file():
            continue
        body = rpath.read_text(encoding="utf-8")
        for tok in tokens:
            if re.search(rf"(?<![A-Za-z0-9_]){re.escape(tok)}(?![A-Za-z0-9_])", body):
                fail(f"{rpath.name} uses evidence token {tok!r} outside the configured evidence classes {CFG.get('evidence_classes', [])}.")
    if not readme_path().is_file():
        fail("The packaged product README is missing.")
    for sub in subrecipe_paths():
        if not sub.is_file():
            fail(f"Expected subrecipe does not exist: {sub}")
        if re.search(r"(?m)^\s*sub_recipes\s*:", sub.read_text(encoding="utf-8")):
            fail(f"Subrecipes must not declare sub_recipes: {sub.name}")
    sub_dir = subrecipes_dir()
    extra = sorted(p.name for p in sub_dir.glob("*.y*ml") if p.name not in CFG["subrecipes"])
    if extra:
        fail(f"Unexpected subrecipe files not in bundle.config.json: {extra}")


def cli_path(value: str | None) -> Path | None:
    candidate = value or os.environ.get("SC_AGENTS_CLI")
    if not candidate:
        return None
    path = Path(candidate).expanduser().resolve()
    if not path.is_file():
        fail(f"AgentAI CLI does not exist at the requested path: {path}")
    return path


def cli_call(cli: Path, *args: str, productdata: Path | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if productdata is not None:
        env["SC_AGENTS_PRODUCT_DATA"] = str(productdata.resolve())
    return run([str(cli), *args], env=env, cwd=cwd or ROOT)


def cli_version(cli: Path) -> str:
    result = cli_call(cli, "--version")
    return result.stdout.strip().splitlines()[0] if result.stdout.strip() else "UNKNOWN"


def _validate_cli_recipes(cli: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="fea-recipes-") as td:
        root = Path(td)
        recipes = []
        for arc, source in archive_payload_map().items():
            if arc.startswith("recipes/"):
                recipe = root / arc
                recipe.parent.mkdir(parents=True, exist_ok=True)
                recipe.write_bytes(payload_bytes(arc, source))
                recipes.append(recipe)
        for recipe in recipes:
            cli_call(cli, "recipe", "validate", str(recipe))


def precheck(cli: Path | None, *, development: bool = False) -> dict[str, Any]:
    source = validate_source_lock(development=development)
    manifest = validate_manifest()
    validate_recipe_source()
    recipe_validation = "NOT_RUN"
    target_version = "NOT_RUN"
    if cli is not None:
        _validate_cli_recipes(cli)
        recipe_validation = "PASS"
        target_version = cli_version(cli)
    return {
        "source_commits": source["commits"],
        "skill_directories": len(source["skill_names"]),
        "skill_files": len(source["skill_hashes"]),
        "bundle_id": manifest["bundle"]["id"],
        "bundle_version": manifest["bundle"]["version"],
        "target_cli_version": target_version,
        "recipe_validation": recipe_validation,
        "host_mcp_tools_list": "NOT_RUN",
        "integration_provenance": integration_evidence(),
    }


def scan_content(name: str, text: str) -> dict[str, Any]:
    def hit(rx: re.Pattern[str]) -> bool:
        for m in rx.finditer(text):
            # an allowlist entry exempts only if one of its matches covers the offending substring
            covered = any(
                am.start() <= m.start() and am.end() >= m.end()
                for a in ALLOWLIST_RES for am in a.finditer(text)
            )
            if not covered:
                return True
        return False

    issues: list[str] = []
    if hit(CREDENTIAL_RE):
        issues.append("credential_literal")
    if hit(LOCAL_PATH_RE):
        issues.append("local_absolute_path")
    if hit(TRAINING_ID_RE):
        issues.append("training_identity")
    return {"issues": issues, "copyright_marker": bool(COPYRIGHT_RE.search(text))}


def archive_expected_paths(skill_files: list[str]) -> set[str]:
    return {*archive_payload_map(), *skill_files}


def audit_archive(archive_path: Path, staged: dict[str, bytes] | None = None, development: bool = False) -> dict[str, Any]:
    if staged is None:
        staged = collect_skills(development=development)
    expected_hashes = staged_hashes(staged)
    expected = archive_expected_paths(list(staged))
    issues: list[str] = []
    copyright_files: list[str] = []
    if not archive_path.is_file():
        fail(f"Windows bundle artifact is missing: {archive_path}")
    with zipfile.ZipFile(archive_path, "r") as archive:
        names = [info.filename for info in archive.infolist()]
        if len(names) != len(set(names)):
            fail("Bundle archive contains duplicate entries.")
        if set(names) != expected:
            missing = sorted(expected - set(names))
            extra = sorted(set(names) - expected)
            fail(f"Bundle archive file set mismatch. missing={missing[:8]} extra={extra[:8]}")
        if archive.testzip() is not None:
            fail("Bundle archive CRC validation failed.")
        if any("\\" in n or n.startswith("/") or ".." in PurePosixPath(n).parts for n in names):
            fail("Bundle archive contains an unsafe or non-portable entry path.")
        if any(PurePosixPath(n).suffix.lower() in FORBIDDEN_SUFFIXES for n in names):
            fail("Bundle archive contains a forbidden CAD, manual, log, credential, or binary file type.")
        archive_skills: dict[str, str] = {}
        for name in names:
            data = archive.read(name)
            if PurePosixPath(name).suffix.lower() not in ALLOWED_SOURCE_SUFFIXES:
                fail(f"Unexpected non-text bundle file: {name}")
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                fail(f"Bundle contains a non-UTF-8 text payload: {name}")
            if PurePosixPath(name).suffix.lower() == ".bat" and name not in CFG.get("integration_mcp_map", {}).values():
                fail(f"Unapproved launcher: {name}")
            scan_text = text
            # Portable install token in the hash-pinned official BatchPost skill is
            # documentation, not a private workstation location; no line-wide bypass.
            if name == "skills/batchpost-actions/SKILL.md":
                scan_text = scan_text.replace("%USERPROFILE%\\.agents\\skills\\batchpost-actions\\", "USER_SKILL_LOCATION")
            scan = scan_content(name, scan_text)
            issues.extend(f"{name}:{issue}" for issue in scan["issues"])
            if scan["copyright_marker"]:
                copyright_files.append(name)
            if name.startswith("skills/"):
                archive_skills[name] = hashlib.sha256(data).hexdigest()
        if copyright_files and CFG.get("fail_on_copyright_marker", False):
            fail("Bundle contains copyright/proprietary markers: " + ", ".join(copyright_files[:12]))
        if issues:
            fail("Bundle scan found restricted content: " + ", ".join(issues[:12]))
        if archive_skills != expected_hashes:
            fail("Packaged skill file set or SHA-256 values differ from the staged (transformed) skills.")
        for archive_name, source_path in archive_payload_map().items():
            if not source_path.is_file() or archive.read(archive_name) != payload_bytes(archive_name, source_path):
                fail(f"Packaged {archive_name} differs from its source file.")
    return {
        "archive_entries": len(names),
        "skill_directories": len(skill_names(staged)),
        "skill_files": len(staged),
        "duplicate_entries": 0,
        "zip_crc": "PASS",
        "skill_sha256_parity": "PASS",
        "credential_hits": 0,
        "local_absolute_path_hits": 0,
        "training_identity_hits": 0,
        "copyright_marker_files": copyright_files,
        "copyright_marker_file_count": len(copyright_files),
        "forbidden_payloads": "PASS",
        "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "integration_provenance": integration_evidence(),
    }


def package_sources(stage: Path, source: dict[str, Any]) -> None:
    generated = stage / ".agents" / "skills"
    staged: dict[str, bytes] = source["staged"]
    for rel, data in staged.items():
        dst = generated.joinpath(*PurePosixPath(rel.removeprefix("skills/")).parts)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
    on_disk = {p.relative_to(generated).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in generated.rglob("*") if p.is_file()}
    expected = {k.removeprefix("skills/"): v for k, v in source["skill_hashes"].items()}
    if on_disk != expected:
        fail("Generated .agents/skills stage does not match the staged skill set byte-for-byte.")
    for arc, src in archive_payload_map().items():
        dst = stage / "payload" / arc
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(payload_bytes(arc, src))


def write_deterministic_zip(stage: Path, output: Path, skill_files: list[str]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    files: list[tuple[str, Path]] = [(arc, stage / "payload" / arc) for arc in archive_payload_map()]
    skills_root = stage / ".agents" / "skills"
    files.extend((rel, skills_root.joinpath(*PurePosixPath(rel.removeprefix("skills/")).parts)) for rel in skill_files)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for archive_name, path in sorted(files):
            info = zipfile.ZipInfo(archive_name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def build(replace_existing: bool = False) -> dict[str, Any]:
    source = validate_source_lock()
    validate_manifest()
    validate_recipe_source()
    output = ROOT / ARTIFACT_REL
    release_dir = output.parent
    sidecar = release_dir / SIDECAR_NAME
    release_exists = release_dir.exists()
    if release_exists:
        names = {path.name for path in release_dir.iterdir()}
        if names != {output.name, SIDECAR_NAME}:
            fail("Release directory already exists with unexpected contents; refusing to overwrite it.")
        if sidecar.read_bytes() != MANIFEST_PATH.read_bytes():
            fail("Existing release sidecar differs from the canonical manifest; refusing to overwrite it.")
        if not replace_existing:
            report = audit_archive(output, source["staged"])
            return {"artifact": str(output), "sidecar": str(sidecar), "existing_artifact_reused": True, **report}
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bundle-stage-", dir=WORK_DIR) as tmp:
        stage = Path(tmp)
        package_sources(stage, source)
        staged_archive = stage / ARTIFACT_NAME
        write_deterministic_zip(stage, staged_archive, list(source["skill_hashes"]))
        audit_archive(staged_archive, source["staged"])
        if release_exists:
            os.replace(staged_archive, output)
        else:
            release_dir.mkdir(parents=True)
            shutil.copyfile(staged_archive, output)
            shutil.copyfile(MANIFEST_PATH, sidecar)
    report = audit_archive(output, source["staged"])
    return {"artifact": str(output), "sidecar": str(sidecar), "existing_artifact_reused": False, **report}


def build_development() -> dict[str, Any]:
    source = validate_source_lock(development=True)
    validate_manifest()
    validate_recipe_source()
    output_dir = WORK_DIR / "development-bundle"
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bundle-dev-stage-", dir=WORK_DIR) as tmp:
        stage = Path(tmp)
        package_sources(stage, source)
        archive = output_dir / ARTIFACT_NAME
        write_deterministic_zip(stage, archive, list(source["skill_hashes"]))
    shutil.copyfile(MANIFEST_PATH, output_dir / SIDECAR_NAME)
    receipt = {
        "result": "DEVELOPMENT_NOT_RELEASE",
        "artifact_kind": "DEVELOPMENT_NOT_RELEASE",
        "base_commits": source["commits"],
        "skill_hashes": source["skill_hashes"],
        "source_hashes": {arc: hashlib.sha256(p.read_bytes()).hexdigest() for arc, p in archive_payload_map().items()},
        "artifact": str(archive),
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "runtime_qualification": "NOT_CLAIMED",
    }
    (output_dir / "development-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return {**receipt, **audit_archive(archive, source["staged"])}


def postcheck(cli: Path | None, *, development: bool = False) -> dict[str, Any]:
    output = ROOT / ARTIFACT_REL
    report = audit_archive(output, development=development)
    sidecar = output.parent / SIDECAR_NAME
    if sidecar.read_bytes() != MANIFEST_PATH.read_bytes():
        fail("Release manifest sidecar differs from the canonical bundle manifest.")
    cli_validation = "NOT_RUN"
    target_version = "NOT_RUN"
    if cli is not None:
        _validate_cli_recipes(cli)
        cli_validation = "PASS"
        target_version = cli_version(cli)
    return {"recipe_validation": cli_validation, "target_cli_version": target_version, **report}


def parse_json_result(result: subprocess.CompletedProcess[str], label: str) -> Any:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        fail(f"{label} did not return JSON: {exc}")


def local_test(cli: Path, development: bool = False) -> dict[str, Any]:
    precheck(cli, development=development)
    output = (WORK_DIR / "development-bundle" / ARTIFACT_NAME) if development else ROOT / ARTIFACT_REL
    audit_archive(output, development=development)
    sidecar = output.parent / SIDECAR_NAME
    if not sidecar.is_file():
        fail(f"Bundle sidecar is missing: {sidecar}")
    root = WORK_DIR / "agentai-local-test"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_root = root / stamp
    suffix = 1
    while run_root.exists():
        run_root = root / f"{stamp}-{suffix}"
        suffix += 1
    productdata = run_root / "productdata"
    productdata.mkdir(parents=True)
    name_version = f"{BUNDLE_ID}-{BUNDLE_VERSION}"
    shutil.copyfile(output, productdata / f"{name_version}.bundle")
    shutil.copyfile(sidecar, productdata / f"{name_version}.toml")

    before = parse_json_result(cli_call(cli, "bundle", "list", "--json", productdata=productdata, cwd=productdata), "bundle list before enable")
    if BUNDLE_ID not in json.dumps(before).casefold():
        fail("Target CLI did not list the staged local bundle.")
    cli_call(cli, "bundle", "enable", BUNDLE_ID, "--version", BUNDLE_VERSION, productdata=productdata, cwd=productdata)
    enabled_path = productdata / "enabled-bundles.json"
    if not enabled_path.is_file():
        fail("Target CLI did not create the isolated enabled-bundles record.")
    enabled = json.loads(enabled_path.read_text(encoding="utf-8"))
    if not any(item.get("id") == BUNDLE_ID and item.get("version") == BUNDLE_VERSION for item in enabled):
        fail("Target CLI enabled-bundles readback did not contain the expected bundle/version.")
    after = parse_json_result(cli_call(cli, "bundle", "list", "--json", productdata=productdata, cwd=productdata), "bundle list after enable")
    if BUNDLE_ID not in json.dumps(after).casefold():
        fail("Target CLI bundle listing after enable omitted the expected bundle.")

    expected_names = set(skill_names(collect_skills(development=development)))
    skills_output = cli_call(cli, "skills", "list", productdata=productdata, cwd=productdata).stdout
    visible_names = {
        line.split("|", 1)[0].strip()
        for line in skills_output.splitlines()
        if "|" in line and line.split("|", 1)[0].strip() in expected_names
    }
    if visible_names != expected_names:
        fail(f"AgentAI CLI skill discovery mismatch; missing {sorted(expected_names - visible_names)[:10]}.")

    agents = parse_json_result(cli_call(cli, "recipe", "list", "--format", "json", productdata=productdata, cwd=productdata), "recipe list")
    agent_name = CFG["main_agent_name"]
    matching = [a for a in agents if a.get("name") == agent_name or Path(a.get("path", "")).name == recipe_path().name]
    if len(matching) != 1:
        fail(f"Isolated productdata should expose exactly one agent named {agent_name}; CLI returned {len(agents)} recipes and {len(matching)} matching.")
    if matching[0].get("name") not in (None, agent_name):
        fail(f"Agent name mismatch: expected {agent_name}, got {matching[0].get('name')}.")

    expected_agents = {recipe_path().stem} | {PurePosixPath(n).stem for n in integration_files() if n.startswith("recipes/")}
    actual_agents = {a.get("name") for a in agents}
    if actual_agents != expected_agents:
        fail(f"Agent set mismatch: expected {expected_agents}, actual {actual_agents}")
    expanded = productdata / name_version
    mcp_config = json.loads((expanded / "mcps.json").read_text(encoding="utf-8"))
    configs = mcp_config.get("configs", [])
    if {m.get("name") for m in configs} != set(CFG.get("manifest_mcp_names", [])):
        fail("Materialized MCP names mismatch")
    for m in configs:
        launch = productdata / m["cmd"]
        if not launch.is_file():
            fail(f"Materialized launcher missing: {launch}")
        arc = m["cmd"].replace("\\", "/")
        if launch.read_bytes() != archive_payload_map()[arc].read_bytes():
            fail("Materialized launcher byte mismatch")
    if not (expanded / "recipes" / recipe_path().name).is_file():
        fail("Enabled bundle did not materialize the Agent recipe into productdata.")
    for sub in CFG["subrecipes"]:
        if not (expanded / "recipes" / "subrecipes" / sub).is_file():
            fail(f"Enabled bundle did not materialize subrecipe {sub}.")
    discovered = {p.parent.name for p in (expanded / "skills").glob("*/SKILL.md")}
    total = int(CFG["expected_total_skills"])
    if discovered != expected_names or len(discovered) != total:
        fail(f"Enabled bundle productdata must contain all {total} skills; missing {sorted(expected_names - discovered)[:10]}, found {len(discovered)}.")
    receipt = {
        "result": "DEVELOPMENT_NOT_RELEASE" if development else "PASS",
        "artifact_kind": "DEVELOPMENT_NOT_RELEASE" if development else "RELEASE",
        "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "target_cli_version": cli_version(cli),
        "bundle_list_before_enable": "PASS",
        "bundle_enable": "PASS",
        "bundle_list_after_enable": "PASS",
        "agent_name": agent_name,
        "subrecipes_materialised": len(CFG["subrecipes"]),
        "visible_agents": len(agents),
        "visible_skills": len(visible_names),
        "skills_discovered_in_productdata": len(discovered),
        "skill_names_match_expected": True,
        "productdata_isolated": True,
        "host_mcp_registration": "CONFIG_AND_LAUNCHERS_VERIFIED_HANDSHAKE_NOT_RUN",
        "mcp_names": [m["name"] for m in configs],
        "agentai_new_session_ui": "NOT_RUN",
        "host_settings_modified": False,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt_path = run_root / "acceptance.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return {**receipt, "receipt": str(receipt_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=f"Build and locally validate the {BUNDLE_NAME} bundle.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    pre = subparsers.add_parser("precheck")
    pre.add_argument("--cli")
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--replace-existing", action="store_true")
    post = subparsers.add_parser("postcheck")
    post.add_argument("--cli")
    local = subparsers.add_parser("local-test")
    local.add_argument("--cli", required=True)
    local.add_argument("--development", action="store_true")
    subparsers.add_parser("build-development")
    args = parser.parse_args()
    try:
        cli = cli_path(getattr(args, "cli", None))
        if args.command == "precheck":
            result = precheck(cli)
        elif args.command == "build":
            result = build(args.replace_existing)
        elif args.command == "postcheck":
            result = postcheck(cli)
        elif args.command == "build-development":
            result = build_development()
        else:
            if cli is None:
                fail("local-test requires the target AgentAI CLI path.")
            result = local_test(cli, development=args.development)
    except (OSError, KeyError, ValueError, zipfile.BadZipFile, tomllib.TOMLDecodeError, RuntimeError) as exc:
        print(json.dumps({"result": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps({k: v for k, v in result.items() if k not in ("skill_hashes",)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
