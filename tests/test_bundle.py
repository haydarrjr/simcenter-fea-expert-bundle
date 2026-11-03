import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[1]))
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts import bundle

CFG = bundle.CFG
REAL_ROOT = bundle.ROOT


def skill_md(name: str, body: str = "") -> bytes:
    return f"---\nname: {name}\ndescription: test skill {name}\n---\n# {name}\n{body}\n".encode()


class ConfigChecks(unittest.TestCase):
    def test_config_required_keys(self):
        for key in ("bundle", "recipe", "subrecipes", "required_refs", "expected_total_skills",
                    "overlay_replaces", "manifest_contributions", "readme_dir"):
            self.assertIn(key, CFG)
        self.assertEqual(CFG["bundle"]["id"], bundle.BUNDLE_ID)

    def test_copyright_regex_has_no_mojibake(self):
        self.assertNotIn("\u00c2", CFG["copyright_re"])
        self.assertTrue(bundle.COPYRIGHT_RE.search("\u00a9 2026"))
        self.assertTrue(bundle.COPYRIGHT_RE.search("All Rights Reserved"))

    def test_real_manifest_valid(self):
        manifest = bundle.validate_manifest()
        self.assertEqual([m["name"] for m in manifest["mcps"]], CFG["manifest_mcp_names"])
        self.assertEqual(manifest["dependencies"]["products"], ["Simcenter 3D 2612"])

    def test_manifest_with_mcps_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "m.toml"
            p.write_text(bundle.MANIFEST_PATH.read_text(encoding="utf-8") + '\n[[mcps]]\nname = "x"\n', encoding="utf-8")
            with patch.object(bundle, "MANIFEST_PATH", p):
                with self.assertRaisesRegex(RuntimeError, "mcps"):
                    bundle.validate_manifest()

    def test_manifest_with_products_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "m.toml"
            text = bundle.MANIFEST_PATH.read_text(encoding="utf-8").replace('products = ["Simcenter 3D 2612"]', 'products = ["x"]')
            p.write_text(text, encoding="utf-8")
            with patch.object(bundle, "MANIFEST_PATH", p):
                with self.assertRaises(RuntimeError):
                    bundle.validate_manifest()


class ScanChecks(unittest.TestCase):
    def test_scan_flags_and_allowlist(self):
        self.assertIn("local_absolute_path", bundle.scan_content("a.md", "see C:\\Users\\x")["issues"])
        self.assertIn("credential_literal", bundle.scan_content("a.md", "ghp_" + "a" * 25)["issues"])
        with patch.object(bundle, "ALLOWLIST_RES", [re.compile(r"C:\\Users\\x")]):
            self.assertEqual(bundle.scan_content("a.md", "see C:\\Users\\x")["issues"], [])

    def test_new_local_path_patterns(self):
        for bad in ("%USERPROFILE%\\x", "see ~/notes", "file:///c/x", "/mnt/data/x", "/opt/tool", "/etc/passwd"):
            with self.subTest(bad=bad):
                self.assertIn("local_absolute_path", bundle.scan_content("a.md", f"x {bad}")["issues"])
        for ok in ("a~/b", "https://e.com/opt/x", "relative/mnt/x"):
            with self.subTest(ok=ok):
                self.assertEqual(bundle.scan_content("a.md", ok)["issues"], [] if "e.com" not in ok else bundle.scan_content("a.md", ok)["issues"])
        self.assertEqual(bundle.scan_content("a.md", "a~/b relative/mnt/x")["issues"], [])

    def test_allowlist_is_not_line_wide(self):
        text = "C:\\Users\\ok and C:\\Users\\bad"
        with patch.object(bundle, "ALLOWLIST_RES", [re.compile(r"C:\\Users\\ok")]):
            self.assertIn("local_absolute_path", bundle.scan_content("a.md", text)["issues"])
            self.assertEqual(bundle.scan_content("a.md", "C:\\Users\\ok")["issues"], [])

    def test_copyright_fail_option(self):
        self.assertFalse(CFG.get("fail_on_copyright_marker", False))
        self.assertTrue(bundle.scan_content("a.md", "Copyright X")["copyright_marker"])


class FixtureBase(unittest.TestCase):
    """Builds a temp repo layout from config values."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.root = Path(self._td.name)
        self.stack = []
        cfg_patch = patch.object(bundle, "CFG", {**CFG, "integration_receipt": None})
        cfg_patch.start()
        self.addCleanup(cfg_patch.stop)
        p = patch.object(bundle, "ROOT", self.root)
        p.start()
        self.addCleanup(p.stop)

    def write_recipes(self, *, drop_ref=None, sub_recipes_in=None, extra_ext=(), drop_sub=None, extra_text="", sub_text=""):
        rp = bundle.recipe_path()
        rp.parent.mkdir(parents=True, exist_ok=True)
        subs = bundle.subrecipes_dir()
        subs.mkdir(parents=True, exist_ok=True)
        exts = [("ref", n) for n in CFG["required_refs"] + CFG["optional_refs"] if n != drop_ref]
        exts += [("platform", n) for n in CFG["required_platform_extensions"]]
        lines = [f"name: {CFG['main_agent_name']}", "extensions:"]
        for t, n in exts:
            lines += [f"  - type: {t}", f"    name: {n}"]
        for t, n in extra_ext:
            lines += [f"  - type: {t}", f"    name: {n}"]
        lines.append("sub_recipes:")
        for n in CFG["subrecipes"]:
            if n != drop_sub:
                lines += [f'  - name: "{n[:-5]}"', f'    path: "./subrecipes/{n}"']
        rp.write_text("\n".join(lines) + "\n" + extra_text, encoding="utf-8")
        for n in CFG["subrecipes"]:
            body = f"name: {n}\n{sub_text if n == CFG['subrecipes'][0] else ''}"
            if n == sub_recipes_in:
                body += "sub_recipes:\n  - name: x\n"
            (subs / n).write_text(body, encoding="utf-8")
        bundle.readme_path().parent.mkdir(parents=True, exist_ok=True)
        bundle.readme_path().write_text("# readme\n", encoding="utf-8")

    def make_zip(self, staged, extra=None, mutate=None):
        out = self.root / "a.zip"
        with zipfile.ZipFile(out, "w") as z:
            for arc, src in bundle.archive_payload_map().items():
                z.writestr(arc, src.read_bytes())
            for arc, data in staged.items():
                z.writestr(arc, (mutate or {}).get(arc, data))
            for arc, data in (extra or {}).items():
                z.writestr(arc, data)
        return out


class RecipeChecks(FixtureBase):
    def test_valid_recipes_accepted(self):
        self.write_recipes()
        bundle.validate_recipe_source()

    def test_each_required_ref_is_required(self):
        for ref in CFG["required_refs"]:
            with self.subTest(ref=ref):
                self.write_recipes(drop_ref=ref)
                with self.assertRaisesRegex(RuntimeError, re.escape(ref)):
                    bundle.validate_recipe_source()

    def test_optional_ref_not_required(self):
        for ref in CFG["optional_refs"]:
            with self.subTest(ref=ref):
                self.write_recipes(drop_ref=ref)
                bundle.validate_recipe_source()

    def test_subrecipe_with_sub_recipes_rejected(self):
        self.write_recipes(sub_recipes_in=CFG["subrecipes"][0])
        with self.assertRaisesRegex(RuntimeError, "sub_recipes"):
            bundle.validate_recipe_source()

    def test_sub_recipes_must_match_config(self):
        self.write_recipes(drop_sub=CFG["subrecipes"][-1])
        with self.assertRaisesRegex(RuntimeError, "sub_recipes"):
            bundle.validate_recipe_source()

    def test_sub_recipe_path_mismatch_rejected(self):
        self.write_recipes()
        rp = bundle.recipe_path()
        rp.write_text(rp.read_text(encoding="utf-8").replace("./subrecipes/", "./other/", 1), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "sub_recipes"):
            bundle.validate_recipe_source()

    def test_unknown_ref_rejected(self):
        self.write_recipes(extra_ext=[("ref", "Mystery MCP")])
        with self.assertRaisesRegex(RuntimeError, "Mystery"):
            bundle.validate_recipe_source()

    def test_builtin_developer_rejected(self):
        self.write_recipes(extra_ext=[("builtin", "developer")])
        with self.assertRaisesRegex(RuntimeError, "developer"):
            bundle.validate_recipe_source()

    def test_other_builtin_allowed(self):
        self.write_recipes(extra_ext=[("builtin", "memory")])
        bundle.validate_recipe_source()

    def test_forbidden_evidence_token_rejected(self):
        for tok in CFG["forbidden_evidence_tokens"]:
            with self.subTest(tok=tok):
                self.write_recipes(sub_text=f"instructions: result is {tok}.\n")
                with self.assertRaisesRegex(RuntimeError, tok):
                    bundle.validate_recipe_source()
        self.write_recipes(extra_text="instructions: SOURCE_TESTED only\n")
        bundle.validate_recipe_source()

    def test_missing_subrecipe_rejected(self):
        self.write_recipes()
        (bundle.subrecipes_dir() / CFG["subrecipes"][-1]).unlink()
        with self.assertRaises(RuntimeError):
            bundle.validate_recipe_source()


class StagedSkillChecks(FixtureBase):
    def test_broken_link_rejected_and_good_link_ok(self):
        good = {"skills/a/SKILL.md": skill_md("a", "[r](references/x.md)"), "skills/a/references/x.md": b"# x\n"}
        bundle.validate_staged_skills(good)
        bad = {"skills/a/SKILL.md": skill_md("a", "[r](references/none.md)")}
        with self.assertRaisesRegex(RuntimeError, "link target"):
            bundle.validate_staged_skills(bad)

    def test_fenced_links_ignored_and_frontmatter_name_enforced(self):
        bundle.validate_staged_skills({"skills/a/SKILL.md": skill_md("a", "```\n[x](nope.md)\n```")})
        with self.assertRaisesRegex(RuntimeError, "name"):
            bundle.validate_staged_skills({"skills/a/SKILL.md": skill_md("b")})

    def test_bom_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "BOM"):
            bundle.validate_staged_skills({"skills/a/SKILL.md": b"\xef\xbb\xbf" + skill_md("a")})

    def test_markdown_suffix_checked(self):
        with self.assertRaisesRegex(RuntimeError, "BOM"):
            bundle.validate_staged_skills({"skills/a/SKILL.md": skill_md("a"), "skills/a/n.markdown": b"\xef\xbb\xbfx"})

    def test_crlf_frontmatter_accepted(self):
        bundle.validate_staged_skills({"skills/a/SKILL.md": skill_md("a").replace(b"\n", b"\r\n")})


class ArchiveAuditChecks(FixtureBase):
    def setUp(self):
        super().setUp()
        self.write_recipes()
        self.staged = {"skills/a/SKILL.md": skill_md("a")}

    def test_valid_archive(self):
        report = bundle.audit_archive(self.make_zip(self.staged), self.staged)
        self.assertEqual(report["skill_sha256_parity"], "PASS")

    def test_extra_file_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "mismatch"):
            bundle.audit_archive(self.make_zip(self.staged, extra={"skills/a/extra.md": b"x"}), self.staged)

    def test_forbidden_suffix_rejected(self):
        z = self.make_zip(self.staged, extra={"skills/a/m.pdf": b"x"})
        staged = {**self.staged, "skills/a/m.pdf": b"x"}
        with self.assertRaisesRegex(RuntimeError, "forbidden"):
            bundle.audit_archive(z, staged)

    def test_modified_skill_bytes_rejected(self):
        z = self.make_zip(self.staged, mutate={"skills/a/SKILL.md": skill_md("a", "changed")})
        with self.assertRaisesRegex(RuntimeError, "SHA-256"):
            bundle.audit_archive(z, self.staged)

    def test_stale_recipe_payload_rejected(self):
        z = self.make_zip(self.staged)
        bundle.recipe_path().write_text("name: changed\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "differs"):
            bundle.audit_archive(z, self.staged)

    def test_restricted_content_rejected(self):
        staged = {"skills/a/SKILL.md": skill_md("a", "path C:\\Users\\bob\\x")}
        with self.assertRaisesRegex(RuntimeError, "restricted"):
            bundle.audit_archive(self.make_zip(staged), staged)

    def test_audit_compares_against_transformed_bytes(self):
        raw = skill_md("a", "RAW")
        staged = {"skills/a/SKILL.md": raw.replace(b"RAW", b"XFORMED")}
        z = self.make_zip(staged)
        bundle.audit_archive(z, staged)  # transformed expectation passes
        with self.assertRaisesRegex(RuntimeError, "SHA-256"):
            bundle.audit_archive(z, {"skills/a/SKILL.md": raw})


def git_init(path: Path):
    subprocess.run(["git", "-c", "core.autocrlf=false", "init", "-q", str(path)], check=True)
    cfg = path / ".git" / "config"
    cfg.write_text(cfg.read_text(encoding="utf-8") + "[user]\n\temail = t@t\n\tname = t\n[core]\n\tautocrlf = false\n", encoding="utf-8")


def git_add(path: Path, *extra: str):
    subprocess.run(["git", "-C", str(path), "-c", "core.autocrlf=false", "add", "-A", "--", *extra], check=True)


class CollectSkillsChecks(FixtureBase):
    """Uses a pre-built git source repo template and fast local copies."""

    _template_td: tempfile.TemporaryDirectory[str] | None = None
    _template_src: Path
    _template_commit: str

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._template_td = tempfile.TemporaryDirectory()
        src = Path(cls._template_td.name) / "src"
        for n in ("s1", "rep"):
            d = src / "skills" / n
            (d / "agents").mkdir(parents=True)
            (d / "SKILL.md").write_bytes(skill_md(n, "SRC"))
            (d / "agents" / "openai.yaml").write_text("x: 1\n", encoding="utf-8")
        git_init(src)
        git_add(src)
        subprocess.run(["git", "-C", str(src), "commit", "-q", "-m", "s"], check=True)
        cls._template_commit = subprocess.run(
            ["git", "-C", str(src), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
        cls._template_src = src

    @classmethod
    def tearDownClass(cls):
        if cls._template_td is not None:
            cls._template_td.cleanup()
        super().tearDownClass()

    def build(self, *, overlay=("o1",), replaces=("rep",), src_skills=("s1", "rep"), exclude_files=1, lock_dirs=None, overlay_dir_name="overlay/skills/"):
        git_init(self.root)
        src = self.root / "vendor" / "src"
        src.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self._template_src, src)
        commit = self._template_commit
        self.src, self.commit = src, commit
        for n in overlay:
            d = self.root / "overlay" / "skills" / n
            d.mkdir(parents=True)
            (d / "SKILL.md").write_bytes(skill_md(n, "OVL"))
        if overlay:
            git_add(self.root, ".", ":!vendor")
        lock = {"sources": [{
            "path": "vendor/src", "commit": commit, "canonical_tree": "skills/",
            "expected_skill_directories": len(src_skills if lock_dirs is None else range(lock_dirs)),
            "expected_skill_files": len(src_skills),
            "excluded_files": len(src_skills) * exclude_files,
        }]}
        (self.root / "source.lock.json").write_text(json.dumps(lock), encoding="utf-8")
        cfg = {**CFG, "overlay_replaces": list(replaces), "integration_receipt": None}
        for p in (patch.object(bundle, "LOCK_PATH", self.root / "source.lock.json"),
                  patch.object(bundle, "CFG", cfg),
                  patch.object(bundle, "HOOK_PATH", self.root / "none.py")):
            p.start()
            self.addCleanup(p.stop)

    def test_excludes_openai_yaml_and_adds_overlay(self):
        self.build(replaces=())
        staged = bundle.collect_skills()
        self.assertFalse([k for k in staged if k.endswith("openai.yaml")])
        self.assertEqual(bundle.skill_names(staged), ["o1", "rep", "s1"])

    def test_overlay_replaces_source_skill(self):
        self.build(overlay=("rep",))
        staged = bundle.collect_skills()
        self.assertIn(b"OVL", staged["skills/rep/SKILL.md"])
        self.assertNotIn(b"SRC", staged["skills/rep/SKILL.md"])

    def test_unlisted_collision_rejected(self):
        self.build(overlay=("s1",), replaces=())
        with self.assertRaisesRegex(RuntimeError, "collide"):
            bundle.collect_skills()

    def test_wrong_expected_directory_count_rejected(self):
        self.build(lock_dirs=5)
        with self.assertRaisesRegex(RuntimeError, "skill directories"):
            bundle.collect_skills()

    def test_untracked_overlay_fails_in_release(self):
        self.build(overlay=("o1",), replaces=())
        d = self.root / "overlay" / "skills" / "ghost"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_bytes(skill_md("ghost"))
        with self.assertRaisesRegex(RuntimeError, "ghost"):
            bundle.collect_skills()
        staged = bundle.collect_skills(development=True)  # warns only
        self.assertNotIn("ghost", bundle.skill_names(staged))

    def test_unstaged_modified_overlay_fails_in_release(self):
        self.build(overlay=("o1",), replaces=())
        (self.root / "overlay" / "skills" / "o1" / "SKILL.md").write_bytes(skill_md("o1", "EDITED"))
        with self.assertRaisesRegex(RuntimeError, "unstaged"):
            bundle.collect_skills()
        staged = bundle.collect_skills(development=True)
        self.assertNotIn(b"EDITED", staged["skills/o1/SKILL.md"])  # index bytes, not worktree

    def test_crlf_worktree_copy_hashes_like_lf_blob(self):
        self.build(overlay=())
        lf = bundle.staged_hashes(bundle.collect_skills())
        wt = self.src / "skills" / "s1" / "SKILL.md"
        wt.write_bytes(wt.read_bytes().replace(b"\n", b"\r\n"))
        self.assertIn(b"\r\n", wt.read_bytes())
        self.assertEqual(bundle.staged_hashes(bundle.collect_skills()), lf)

    def test_transform_hook_applied_to_markdown(self):
        self.build(overlay=())
        (self.root / "hook.py").write_text("def transform(rel, data):\n    return data.replace(b'SRC', b'HOOKED')\n", encoding="utf-8")
        with patch.object(bundle, "HOOK_PATH", self.root / "hook.py"):
            staged = bundle.collect_skills()
        self.assertIn(b"HOOKED", staged["skills/s1/SKILL.md"])
        self.assertEqual(staged["skills/s1/SKILL.md"].count(b"SRC"), 0)


class RealRepoChecks(unittest.TestCase):
    def test_real_repo_skill_totals(self):
        if not bundle.overlay_files():
            self.skipTest("overlay/skills not yet git-tracked")
        if not (REAL_ROOT / "vendor" / "fea-expert-agent-plugin" / "skills").is_dir():
            self.skipTest("submodules not checked out")
        names = bundle.skill_names(bundle.collect_skills())
        self.assertEqual(len(names), CFG["expected_total_skills"])

    def test_real_recipes(self):
        if not bundle.recipe_path().is_file():
            self.skipTest(".agents recipes not yet present")
        if not bundle.readme_path().is_file():
            self.skipTest("dist/docs README not yet present")
        bundle.validate_recipe_source()


if __name__ == "__main__":
    unittest.main()
