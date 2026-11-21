"""Synthetic, text-only regressions for the scoped Nastran deck helper."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/simcenter-nastran/scripts/deck.py"
SPEC = importlib.util.spec_from_file_location("nastran_deck", SCRIPT)
deck = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deck)

GEOMETRY = [
    "GRID,1,,0.,0.,0.",
    "GRID,2,,1.,0.,0.",
    "GRID,3,,0.,1.,0.",
    "GRID,4,,0.,0.,1.",
    "CTETRA,10,20,1,2,3,4",
    "PSOLID,20,30",
    "MAT1,30,1.+5,,0.3,1.-6",
]
CONTROL = ["METHOD = 100", "DISPLACEMENT(PLOT,REAL) = ALL"]
METHOD = "EIGRL,100,,,26,,,,MASS"


def fixed(head, values, width=8, marker=""):
    slots = 64 // width
    fields = "".join(f"{value:<{width}}" for value in [*values, *[""] * (slots - len(values))])
    return f"{head:<8}{fields}{marker}".rstrip()


class DeckTests(unittest.TestCase):
    def setUp(self):
        work = Path.cwd() if Path.cwd().name == ".work" else SCRIPT.parents[3] / ".work"
        work.mkdir(exist_ok=True)
        tmp = tempfile.TemporaryDirectory(prefix="nastran-text-test-", dir=work)
        self.addCleanup(tmp.cleanup)
        self.work = Path(tmp.name)
        self.root = self.work / "authorized"
        self.root.mkdir()

    def write(self, name, *lines, base=None):
        path = (base or self.root) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(("\n".join(lines) + "\n").encode())
        return path

    def entry(self, *, sol=103, control=CONTROL, bulk=None, end="ENDDATA"):
        return self.write("main.dat", "$ Fixture", "ID,NASTRAN,DEMO", f"SOL {sol}", "CEND",
                          *control, "BEGIN BULK", *(bulk if bulk is not None else [METHOD, *GEOMETRY]), end)

    def cli(self, entry, *args):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(entry), *args],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def test_inheritance_is_global_then_local_and_does_not_leak_between_subcases(self):
        entry = self.entry(sol=101, control=[
            "SPC = 1", "LOAD = 3", "DISPLACEMENT = ALL",
            "SUBCASE 10", "SPC = 2", "LOAD = 4",
            "SUBCASE 20", "MPC = 5",
        ], bulk=["SPCADD,1,2", "SPC1,2,123,1", "LOAD,3,2.,1.,4", "FORCE,4,1,,50.,1.,0.,0."])
        result = deck.read_deck(entry).summary(show_cards=True)
        a, b = [item["effective"] for item in result["subcases"]]
        self.assertEqual(result["sol"], 101)
        self.assertEqual((a["SPC"]["value"], a["LOAD"]["value"]), ("2", "4"))
        self.assertEqual((b["SPC"]["value"], b["LOAD"]["value"]), ("1", "3"))
        self.assertNotIn("MPC", a)
        self.assertEqual((a["DISPLACEMENT"]["line"], b["DISPLACEMENT"]["line"]), (7, 7))
        self.assertEqual(result["cards"][2]["fields"], ("3", "2.", "1.", "4"))

    def test_advanced_observation_reports_locations_without_effective_claims(self):
        entry = self.write(
            "advanced.dat", "ASSIGN INPUTT2='unavailable.op2' UNIT=20", "SOL 111", "CEND",
            "METHOD(STRUCTURE) = 40", "SET 13 = 1 THRU 10,", "  15 THRU 20",
            "SUBCASE 2", "SDAMPING = 42", "RANDOM(RPOSTS1=1) = 50", "BEGIN BULK",
            "INCLUDE 'random.inc'", "BEGIN SUPER=1", "SECONCT,1,0", "ENDDATA",
        )
        dependency = self.write("random.inc", "RANDPS,50,1,1,1.,0.,51", "TABRND1,51")
        expected_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in (entry, dependency)}
        with self.assertRaises(deck.DeckError):
            deck.read_deck(entry, root=self.root)
        observed = deck.observe_deck(entry, root=self.root, expected_hashes=expected_hashes)
        self.assertEqual(observed["status"], "RECORDS_OBSERVED")
        self.assertEqual(observed["effective_sets"], "UNVERIFIED")
        self.assertTrue(observed["boundary_markers_seen"])
        self.assertEqual(observed["records"][0]["resolution"], "NOT_RESOLVED")
        self.assertEqual(observed["records"][5]["possible_continuation_of"],
                         {"file": entry.name, "line": 5})
        self.assertEqual(observed["records"][8]["subcase"], 2)
        self.assertEqual(observed["bulk_head_counts"], {"RANDPS": 1, "SECONCT": 1, "TABRND1": 1})
        self.assertEqual(observed["includes"], [{"file": entry.name, "line": 11, "target": dependency.name}])
        self.assertEqual(self.cli(entry, "--observe", "--root", str(self.root)), (0, observed))
        self.assertEqual(self.cli(entry, "--observe")[0], 2)
        with self.assertRaisesRegex(deck.DeckError, "outside the effective"):
            deck.observe_deck(entry, root=self.root, expected_hashes={**expected_hashes, "unused": "a" * 64})

    def test_advanced_observation_keeps_incomplete_input_unverified(self):
        entry = self.write("fragment.dat", "SOL 111", "CEND", "SUBCASE 1")
        observed = deck.observe_deck(entry)
        self.assertFalse(observed["boundary_markers_seen"])
        self.assertEqual(observed["effective_sets"], "UNVERIFIED")

    def test_fixed_small_large_and_free_continuations_preserve_key_blanks(self):
        entry = self.entry(bulk=[
            fixed("CTETRA", ["8", "20", "1", "2", "3", "4", "5", "6"], marker="+S"),
            "$ A comment is not a continuation break.",
            fixed("+S", ["7", "8", "9", "10"]),
            fixed("GRID*", ["5", "", "1.25", "2.5"], width=16, marker="+"),
            fixed("*", ["3.75", "", "123"], width=16),
            "TABLEM1,10,,,,,,,,+TAB",
            "+TAB,1.0,2.4+5,ENDT",
            "EIGRL*,100,,,26,*E",
            "*E,0,7,,MASS",
            "TABLEM1,11",
            ",1.0,2.5+5,ENDT",
        ], end="ENDDATA a1b2c3d4 $ translator checksum")
        parsed = deck.read_deck(entry)
        self.assertEqual(parsed.enddata_suffix, "a1b2c3d4")
        self.assertEqual([card.name for card in parsed.cards], ["CTETRA", "GRID", "TABLEM1", "EIGRL", "TABLEM1"])
        self.assertEqual(parsed.cards[0].fields[-6:], ("5", "6", "7", "8", "9", "10"))
        self.assertEqual(parsed.cards[1].fields, ("5", "", "1.25", "2.5", "3.75", "", "123"))
        self.assertEqual(parsed.cards[2].fields, ("10", "", "", "", "", "", "", "", "1.0", "2.4+5", "ENDT"))
        self.assertEqual(parsed.cards[3].fields, ("100", "", "", "26", "0", "7", "", "MASS"))
        self.assertEqual(parsed.cards[4].fields, ("11", "", "", "", "", "", "", "", "1.0", "2.5+5", "ENDT"))

    def test_nested_include_has_relative_source_and_exact_byte_hashes(self):
        entry = self.entry(control=["INCLUDE 'case.inc'"], bulk=["INCLUDE 'mesh\\solid.inc'"])
        case = self.write("case.inc", *CONTROL)
        solid = self.write("mesh/solid.inc", 'INCLUDE "../method.inc" $ relative to solid.inc', *GEOMETRY)
        method = self.write("method.inc", METHOD)
        hashes = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (entry, case, solid, method)}
        parsed = deck.read_deck(entry, root=self.root, expected_hashes=hashes)
        self.assertEqual({name: file["sha256"] for name, file in parsed.files.items()}, hashes)
        self.assertEqual(parsed.files["mesh/solid.inc"]["bytes"], solid.stat().st_size)
        self.assertEqual(parsed.includes[2], {"file": "mesh/solid.inc", "line": 1, "target": "method.inc"})
        self.assertEqual(parsed.effective()[None]["METHOD"].source.file, "case.inc")
        self.assertEqual(deck.free_free_profile(parsed)["methods"][0]["file"], "method.inc")
        with self.assertRaisesRegex(deck.DeckError, "files outside the effective"):
            deck.read_deck(entry, root=self.root, expected_hashes={**hashes, "unexpected.dat": "a" * 64})
        with self.assertRaisesRegex(deck.DeckError, "absent from the expected"):
            deck.read_deck(entry, root=self.root, expected_hashes={"main.dat": hashes["main.dat"]})
        method.write_bytes(method.read_bytes() + b"$ byte-level change\n")
        with self.assertRaisesRegex(deck.DeckError, "SHA-256 mismatch for method.inc"):
            deck.read_deck(entry, root=self.root, expected_hashes=hashes)

    def test_unauthorized_unresolved_and_unsupported_includes_fail_closed(self):
        outside = self.write("outside.inc", METHOD, base=self.work)
        with self.assertRaisesRegex(deck.DeckError, "entry deck is outside"):
            deck.read_deck(outside, root=self.root)
        entry = self.entry(bulk=["INCLUDE 'missing.inc'"])
        with self.assertRaisesRegex(deck.DeckError, "requires an explicit authorized root"):
            deck.read_deck(entry)
        for use, reason in [
            ("INCLUDE 'missing.inc'", "cannot read missing.inc"),
            ("INCLUDE '../outside.inc'", "escapes the authorized root"),
            (f"INCLUDE '{outside}'", "literal relative filename"),
            ("INCLUDE 'C:outside.inc'", "literal relative filename"),
            ("INCLUDE '%VAR%\\outside.inc'", "literal relative filename"),
            ("INCLUDE 'main.dat'", "cyclic INCLUDE"),
            ("INCLUDE 'folder.inc", "unsupported INCLUDE syntax"),
            ("INCLUDE 'mesh.inc' extra", "unsupported INCLUDE syntax"),
        ]:
            with self.subTest(use=use):
                entry = self.entry(bulk=[use])
                with self.assertRaisesRegex(deck.DeckError, reason):
                    deck.read_deck(entry, root=self.root)

    def test_link_outside_root_is_not_read(self):
        outside = self.write("outside.inc", METHOD, base=self.work)
        try:
            (self.root / "alias.inc").symlink_to(outside)
        except (NotImplementedError, OSError) as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        entry = self.entry(bulk=["INCLUDE 'alias.inc'"])
        with self.assertRaisesRegex(deck.DeckError, "aliases or escapes"):
            deck.read_deck(entry, root=self.root)

    def test_unknown_control_and_missing_sections_fail_closed(self):
        prefix = ["SOL 103", "CEND", *CONTROL, "BEGIN BULK", METHOD, *GEOMETRY]
        for lines, reason in [
            (["SOL 103,ALT", *prefix[1:], "ENDDATA"], "unsupported Executive"),
            (["SOL 103", *prefix, "ENDDATA"], "duplicate Executive SOL"),
            (["SOL 103", "ALTER 1", *prefix[1:], "ENDDATA"], "unsupported Executive"),
            ([*prefix[:4], "IF (1) THEN", *prefix[4:], "ENDDATA"], "unsupported Case Control"),
            ([*prefix, "IF,1", "ENDDATA"], "unsupported bulk record or directive"),
            ([*prefix, "ENDDATA rubbish"], "unsupported bulk record"),
            ([*prefix, "ENDDATA", "GRID,6"], "active text after ENDDATA"),
            (prefix, "incomplete text deck"),
        ]:
            with self.subTest(reason=reason, inserted=lines[-1]):
                with self.assertRaisesRegex(deck.DeckError, reason):
                    deck.read_deck(self.write("broken.dat", *lines))

    def test_malformed_continuations_do_not_disappear(self):
        small = fixed("CTETRA", ["8", "20", "1", "2", "3", "4", "5", "6"], marker="+S")
        for bulk, reason in [
            (["+X,123"], "orphaned"),
            ([small, fixed("+X", ["7", "8"])], "ID does not match"),
            ([small, "+S,7,8"], "mixed-format"),
            ([small, "INCLUDE 'continuation.inc'"], "missing continuation"),
            ([small], "missing continuation"),
            (["GRID,1,,0.,0.,0.,,,,X"], "continuation marker or excess free fields"),
        ]:
            with self.subTest(bulk=bulk):
                with self.assertRaisesRegex(deck.DeckError, reason):
                    deck.read_deck(self.entry(bulk=bulk), root=self.root)

    def test_free_free_profile_checks_each_subcase_and_leaves_physics_manual(self):
        entry = self.entry(
            control=[*CONTROL, "SUBCASE 4", "METHOD = 101", "SUBCASE 5", "LABEL = inherited method"],
            bulk=[METHOD, "EIGRL,101,,,26", *GEOMETRY, "SPC1,90,123,1", "FORCE,2,1,,5.,1.,0.,0."],
        )
        report = deck.free_free_profile(deck.read_deck(entry), expected_nd=26)
        self.assertEqual(report["status"], "PROFILE_MATCH")
        self.assertEqual([(item["subcase"], item["method"]) for item in report["methods"]], [(4, 101), (5, 100)])
        self.assertTrue(any("connectivity" in item for item in report["manual_review"]))
        self.assertTrue(any("material" in item for item in report["manual_review"]))

    def test_method_and_displacement_rejections(self):
        for control, bulk, reason in [
            ([CONTROL[1]], [METHOD], "missing METHOD"),
            (CONTROL, ["EIGRL,101,,,26"], "does not resolve"),
            (CONTROL, [METHOD, METHOD], "duplicate EIGRL ID"),
            (CONTROL, ["EIGRL,100,0.0,,26"], "blank EIGRL"),
            (CONTROL, ["EIGRL,100,,500.,26"], "blank EIGRL"),
            (CONTROL, ["EIGRL,100,,,0"], "positive integer ND"),
            (CONTROL, ["EIGRL,100,,,16"], "expected EIGRL ND=26"),
            ([CONTROL[0]], [METHOD], "missing DISPLACEMENT"),
            ([*CONTROL, "SUBCASE 1", "DISPLACEMENT = NONE"], [METHOD], "real nodal DISPLACEMENT"),
            ([CONTROL[0], "DISPLACEMENT(PHASE) = ALL"], [METHOD], "real nodal DISPLACEMENT"),
        ]:
            with self.subTest(reason=reason, control=control, bulk=bulk):
                entry = self.entry(control=control, bulk=[*bulk, *GEOMETRY])
                report = deck.free_free_profile(deck.read_deck(entry), expected_nd=26)
                self.assertEqual(report["status"], "REJECTED")
                self.assertIn(reason, "\n".join(report["issues"]))

    def test_grounding_preload_and_non_solid_paths_are_rejected(self):
        for control in ["SPC = 9", "MPC = 9", "STATSUB(PRELOAD) = 2", "LOAD = 1",
                        "DLOAD = 3", "TEMPERATURE(LOAD) = 4", "SUPORT1 = 1"]:
            with self.subTest(control=control):
                entry = self.entry(control=[*CONTROL, control, "SUBCASE 1"])
                report = deck.free_free_profile(deck.read_deck(entry))
                self.assertEqual(report["status"], "REJECTED")
                self.assertIn(f"SUBCASE 1: {control.split(' = ')[0]}", report["issues"][0])
        for card, reason in [
            ("GRID,5,,0.,0.,0.,,123", "GRID PS"),
            ("GRID,5,,0.,0.,0.,-1", "GRID CP/CD"),
            ("GRDSET,,,,,,,1", "GRDSET is outside"),
            ("RBE2,9,1,123,2", "RBE2 is outside"),
            ("CELAS2,9,100.,1,1", "CELAS2 is outside"),
            ("SUPORT,1,123", "SUPORT is outside"),
            ("PARAM,AUTOSPC,YES", "unsupported PARAM AUTOSPC"),
            ("PSOLID,21,30,,,,,PFLUID", "PSOLID must use structural mechanics"),
        ]:
            with self.subTest(card=card):
                entry = self.entry(bulk=[METHOD, *GEOMETRY, card])
                report = deck.free_free_profile(deck.read_deck(entry))
                self.assertEqual(report["status"], "REJECTED")
                self.assertIn(reason, report["issues"][0])

    def test_cli_distinguishes_profile_rejection_from_unresolved_text(self):
        entry = self.entry()
        code, result = self.cli(entry, "--free-free", "--nd", "26")
        self.assertEqual((code, result["free_free"]["status"]), (0, "PROFILE_MATCH"))
        code, result = self.cli(entry, "--free-free", "--nd", "24")
        self.assertEqual((code, result["free_free"]["status"]), (1, "REJECTED"))
        invalid = self.write("invalid.json", "{")
        code, result = self.cli(entry, "--expect-closure", str(invalid))
        self.assertEqual((code, result["status"]), (2, "UNRESOLVED"))
        entry = self.entry(bulk=["INCLUDE 'absent.inc'"])
        code, result = self.cli(entry, "--root", str(self.root), "--free-free")
        self.assertEqual((code, result["status"]), (2, "UNRESOLVED"))
        self.assertNotIn("free_free", result)


if __name__ == "__main__":
    unittest.main()
