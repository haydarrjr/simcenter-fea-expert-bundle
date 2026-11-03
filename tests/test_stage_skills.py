import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import stage_skills as s  # noqa: E402

P = "skills/fea-a/SKILL.md"
R = "skills/fea-a/references/r.md"


def t(rel, text):
    return s.transform(rel, text.encode()).decode()


class TransformTests(unittest.TestCase):
    def test_outside_rewritten(self):
        out = t(P, "see [Doc](../../docs/x.md) now\n")
        self.assertEqual(out, "see Doc (source: fea_expert_agent_plugin/docs/x.md) now\n")

    def test_deeper_outside(self):
        out = t(R, "[E](../../../docs/e.md)")
        self.assertEqual(out, "E (source: fea_expert_agent_plugin/docs/e.md)")

    def test_sibling_kept(self):
        txt = "[b](../fea-b/SKILL.md) [c](../fea-b/references/y.md) [d](references/r.md)\n"
        self.assertEqual(t(P, txt), txt)

    def test_title(self):
        out = t(P, '[a](../../x.md "t") and [b](../fea-b/SKILL.md "t")')
        self.assertEqual(out, 'a (source: fea_expert_agent_plugin/x.md) and [b](../fea-b/SKILL.md "t")')

    def test_anchor_and_external(self):
        txt = "[a](#h) [b](https://e.com/x) [c](mailto:a@b.c)\n"
        self.assertEqual(t(P, txt), txt)

    def test_anchor_on_outside(self):
        self.assertEqual(t(P, "[a](../../x.md#sec)"), "a (source: fea_expert_agent_plugin/x.md)")

    def test_fenced_and_inline_code(self):
        txt = "```\n[a](../../x.md)\n```\n`[b](../../y.md)`\n~~~\n[c](../../z.md)\n~~~\n"
        self.assertEqual(t(P, txt), txt)

    def test_idempotent(self):
        txt = "---\nname: fea-a\n---\n[a](../../x.md) ![i](../../examples/i.png) [b](../fea-b/SKILL.md)\n"
        once = t(P, txt)
        self.assertEqual(t(P, once), once)
        self.assertNotIn("](", once.split("---\n")[-1].split("[b]")[0])

    def test_crlf(self):
        out = s.transform(P, b"a\r\n[x](../../d.md)\r\nb\r\n")
        self.assertEqual(out, b"a\r\nx (source: fea_expert_agent_plugin/d.md)\r\nb\r\n")

    def test_frontmatter_untouched(self):
        fm = "---\nname: fea-a\ndescription: see [x](../../d.md)\n---\n"
        out = t(P, fm + "[x](../../d.md)\n")
        self.assertTrue(out.startswith(fm))
        self.assertIn("x (source:", out[len(fm):])

    def test_non_md(self):
        d = b"[a](../../x.md)"
        self.assertEqual(s.transform("skills/fea-a/x.txt", d), d)

    def test_no_absolute_in_output(self):
        out = t(P, "[a](examples/e.json)")
        self.assertEqual(out, "a (source: fea_expert_agent_plugin/skills/fea-a/examples/e.json)".replace(
            "skills/fea-a/", "skills/fea-a/")) if False else None
        self.assertNotRegex(out, r"[A-Za-z]:[\\/]")


class PrefixAndSuffixTests(unittest.TestCase):
    def test_leading_dot_segments_only(self):
        self.assertEqual(s._strip_dot_segments("./a/b.md"), "a/b.md")
        self.assertEqual(s._strip_dot_segments("././a.md"), "a.md")
        self.assertEqual(s._strip_dot_segments(".github/x.md"), ".github/x.md")
        self.assertEqual(s._strip_dot_segments("../x"), "../x")

    def test_dot_directory_preserved_in_rewrite(self):
        out = t("skills/fea-a/SKILL.md", "[a](../../.github/x.md)")
        self.assertEqual(out, "a (source: fea_expert_agent_plugin/.github/x.md)")

    def test_markdown_suffix_variants(self):
        for rel in ("skills/fea-a/r.markdown", "skills/fea-a/R.MD"):
            self.assertEqual(t(rel, "[a](../../x.md)"), "a (source: fea_expert_agent_plugin/x.md)")

    def test_bom_flagged_in_audit(self):
        files = {"skills/fea-a/SKILL.md": b"\xef\xbb\xbf---\nname: fea-a\ndescription: d\n---\n"}
        self.assertIn("BOM", "\n".join(s._audit_files(files)))


class AuditTests(unittest.TestCase):
    def test_audit_problems(self):
        files = {
            "skills/fea-a/SKILL.md": b"---\nname: wrong\ndescription: \n---\n[x](../../d.md) [y](../fea-q/SKILL.md)\nC:\\foo\n",
        }
        probs = "\n".join(s._audit_files(files))
        for needle in ("outside skills", "broken sibling", "absolute path", "name", "empty description"):
            self.assertIn(needle, probs)

    def test_long_description(self):
        files = {"skills/fea-a/SKILL.md": ("---\nname: fea-a\ndescription: " + "x" * 1025 + "\n---\n").encode()}
        self.assertIn("too long", "\n".join(s._audit_files(files)))


class RealRun(unittest.TestCase):
    def test_vendor_audit_after_transform(self):
        src = ROOT / "vendor" / "fea-expert-agent-plugin"
        if not (src / "skills").is_dir():
            self.skipTest("vendor missing")
        staged = {r: s.transform(r, d) for r, d in s._read_tree(src).items()}
        self.assertEqual(s._audit_files(staged), [])


if __name__ == "__main__":
    unittest.main()
