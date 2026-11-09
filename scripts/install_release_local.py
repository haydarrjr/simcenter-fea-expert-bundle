"""Package (if needed), stage, and enable the local Simcenter 3D FEA Expert bundle in Simcenter Agent Workspace.

Uses the documented Workspace bundle CLI for materialization and activation,
and hydrates materialized skill/recipe files so zero-byte placeholders are replaced.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, tomllib, zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import package_bundle as pb


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hydrate(bundle_zip: Path, target_dir: Path) -> int:
    if not bundle_zip.is_file():
        return 0
    target_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(bundle_zip, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            norm = info.filename.replace("\\", "/")
            if norm.startswith(("recipes/", "skills/")):
                out = target_dir / norm
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(zf.read(info.filename))
                count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--productdata", required=True, type=Path)
    parser.add_argument("--cli", required=True, type=Path)
    args = parser.parse_args()
    target = args.productdata.resolve(strict=True)
    cli = args.cli.resolve(strict=True)
    manifest = tomllib.loads((ROOT / ".sim-ai-agents.toml").read_text(encoding="utf-8"))
    bundle_id, version = manifest["bundle"]["id"], manifest["bundle"]["version"]
    release = ROOT / "dist" / bundle_id / version
    pb.package(release, root=ROOT)
    archive, sidecar = release / "agents-artefact-windows.zip", release / ".sim-ai-agents.toml"
    stem = f"{bundle_id}-{version}"
    shutil.copy2(archive, target / f"{stem}.bundle")
    shutil.copy2(sidecar, target / f"{stem}.toml")
    env = dict(os.environ, SC_AGENTS_PRODUCT_DATA=str(target))
    subprocess.run([str(cli), "bundle", "disable", bundle_id], env=env, text=True, capture_output=True, check=False)
    res = subprocess.run([str(cli), "bundle", "enable", bundle_id, "--version", version], env=env, text=True, capture_output=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(res.stdout + "\n" + res.stderr)
    expanded = target / stem
    hydrated = hydrate(target / f"{stem}.bundle", expanded)
    print(json.dumps({
        "result": "PASS",
        "bundle_id": bundle_id,
        "version": version,
        "archive_sha256": digest(target / f"{stem}.bundle"),
        "expanded": str(expanded),
        "hydrated_files": hydrated,
        "skill_count": len(list((expanded / "skills").glob("*/SKILL.md"))),
        "subrecipe_count": len(list((expanded / "recipes" / "subrecipes").glob("*.yaml"))),
    }, indent=2))


if __name__ == "__main__":
    main()
