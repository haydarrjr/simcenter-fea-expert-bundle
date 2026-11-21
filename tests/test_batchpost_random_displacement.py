import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree as ET


MODULE = Path(__file__).resolve().parents[1] / "skills/batchpost-actions/scripts/random_displacement_csv.py"
spec = importlib.util.spec_from_file_location("random_displacement_csv", MODULE)
post = importlib.util.module_from_spec(spec)
spec.loader.exec_module(post)

RMS = "[Root Mean Square Displacement][Nodal]"
PSD = "[PSD Displacement][Nodal]"


def catalog():
    return {"loadcases": [{"index": 1, "name": "case", "iterations": [
        {"index": i, "value_types": [] if f is None else [{"type": "frequency", "value": f, "unit": "Hz"}],
         "result_types": [{"unique_name": kind, "name": name, "components": ["X", "Y", "Z"]}]}
        for i, f, kind, name in (
            (1, None, RMS, "Root Mean Square Displacement - Nodal"),
            (3, 5.0, PSD, "PSD Displacement - Nodal"),
            (4, 5.25, PSD, "PSD Displacement - Nodal"),
        )
    ]}]}


def table(path, result, units, labels, headings, data):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerows([
            ["Solution Name : Imported Result"],
            [f"Result : {result}"], [f"Result Units : {units}"],
            ["Coordinate Units : mm"], ["Coordinate System : Native"], [],
            ["", "", "", "", *labels],
            ["Node ID", "X Coord", "Y Coord", "Z Coord", *headings],
            [17, 0, 0, 0, *data],
        ])


class RandomDisplacementTests(unittest.TestCase):
    def test_rms_request_uses_discovered_xml_and_no_direct_override(self):
        with tempfile.TemporaryDirectory() as path:
            output = Path(path)
            plan = post.prepare(catalog(), 1, RMS, "X", 17, output)
            self.assertNotIn("resulttype", plan["contour"])
            self.assertEqual(plan["contour"]["iteration_index"]["values"], [1])
            xml = ET.parse(plan["contour"]["result"]["value"])
            self.assertEqual(xml.findtext("./PostView/ResultOptions/Result"), RMS)
            target = output / "actual.csv"
            table(target, "Root Mean Square Displacement - Nodal", "mm",
                  ["case - Root Mean Square Results"], ["1"], [3.5])
            self.assertEqual(post.verify_csv(target, plan, "mm"),
                             [{"iteration": 1, "frequency_hz": None, "value": 3.5}])
            with self.assertRaisesRegex(ValueError, "unit"):
                post.verify_csv(target, plan, "m")
            table(target, "Root Mean Square Displacement - Nodal", "mm",
                  ["another case - Root Mean Square Results"], ["1"], [3.5])
            with self.assertRaisesRegex(ValueError, "loadcase"):
                post.verify_csv(target, plan, "mm")
            with self.assertRaises(FileExistsError):
                post.prepare(catalog(), 1, RMS, "X", 17, output)

    def test_psd_binds_every_exported_frequency_and_component(self):
        with tempfile.TemporaryDirectory() as path:
            output = Path(path)
            plan = post.prepare(catalog(), 1, PSD, "X", 17, output,
                                input_units={"length_unit": "m", "mass_unit": "kg", "time_unit": "s"})
            self.assertEqual(plan["contour"]["iteration_index"]["values"], [3, 4])
            self.assertFalse(plan["preferences_before_open"]["read_units"])
            target = output / "actual-X.csv"
            table(target, "PSD Displacement - Nodal", "mm^2/Hz",
                  ["case - Frequency 2, 5.25Hz", "case - Frequency 1, 5.00Hz"],
                  ["Unknown", "Unknown"], [0.4, 0.3])
            values = post.verify_csv(target, plan, "mm^2/Hz")
            self.assertEqual([r["iteration"] for r in values], [4, 3])
            wrong_path = target.with_name("actual-Y.csv")
            target.rename(wrong_path)
            with self.assertRaisesRegex(ValueError, "component"):
                post.verify_csv(wrong_path, plan, "mm^2/Hz")
            table(target, "PSD Displacement - Nodal", "mm^2/Hz",
                  ["case - Frequency 1, 5.00Hz", "case - Frequency 2, 5.00Hz"],
                  ["Unknown", "Unknown"], [0.3, 0.4])
            with self.assertRaisesRegex(ValueError, "unexpected or ambiguously rounded"):
                post.verify_csv(target, plan, "mm^2/Hz")

    def test_rejects_empty_catalog_or_unknown_frequency_unit(self):
        with self.assertRaisesRegex(ValueError, "loadcase"):
            post.select_states({"loadcases": []}, 1, PSD, "X")
        changed = catalog()
        changed["loadcases"][0]["iterations"][1]["value_types"][0]["unit"] = "rad/s"
        with self.assertRaisesRegex(ValueError, "frequency units"):
            post.select_states(changed, 1, PSD, "X")
