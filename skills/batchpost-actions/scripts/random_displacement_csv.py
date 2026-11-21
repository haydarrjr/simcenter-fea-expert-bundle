"""Plan a scoped BatchPost random-displacement export from its observed catalog."""

import argparse
import csv
import json
import math
from pathlib import Path
import re
from xml.etree import ElementTree as ET


def selected(value):
    return {"type": "single", "value": value}


def select_states(catalog, loadcase, unique_name, component):
    cases = [case for case in catalog["loadcases"] if case["index"] == loadcase]
    if len(cases) != 1:
        raise ValueError("expected exactly one matching loadcase")
    states = []
    for item in cases[0]["iterations"]:
        matches = [r for r in item["result_types"] if r["unique_name"] == unique_name]
        if len(matches) > 1:
            raise ValueError("duplicate result type in one iteration")
        if matches:
            if component not in matches[0]["components"]:
                raise ValueError(f"component unavailable at iteration {item['index']}")
            frequencies = [v for v in item["value_types"] if v["type"] == "frequency"]
            states.append({"iteration": item["index"], "result_name": matches[0]["name"],
                           "frequency_hz": _frequency(frequencies)})
    if not states or len({s["iteration"] for s in states}) != len(states):
        raise ValueError("no matching iterations or duplicated iteration identity")
    frequencies = [s["frequency_hz"] for s in states]
    if unique_name == "[PSD Displacement][Nodal]":
        if None in frequencies or len(set(frequencies)) != len(frequencies):
            raise ValueError("PSD requires distinct frequency states in Hz")
    elif unique_name == "[Root Mean Square Displacement][Nodal]":
        if frequencies != [None]:
            raise ValueError("RMS requires one aggregate state without a frequency")
    else:
        raise ValueError("the qualified CSV layout covers nodal displacement RMS and PSD")
    if len({s["result_name"] for s in states}) != 1:
        raise ValueError("result display name differs across selected states")
    return states


def _frequency(values):
    if not values:
        return None
    if (len(values) != 1 or values[0]["unit"] != "Hz"
            or not math.isfinite(values[0]["value"]) or values[0]["value"] < 0):
        raise ValueError("ambiguous or invalid frequency units or value")
    return values[0]["value"]


def prepare(catalog, loadcase, unique_name, component, node, output, *, input_units=None):
    if loadcase < 1 or node < 1 or component not in ("X", "Y", "Z"):
        raise ValueError("use one positive loadcase and node and a Cartesian component")
    states = select_states(catalog, loadcase, unique_name, component)
    output = Path(output)
    if not output.is_dir():
        raise ValueError("output directory must already exist")
    path = output.resolve() / "result-options.xml"
    preferences = {"contour_csv_write_column_header": True,
                   "contour_csv_export_undeformed_coordinates": True,
                   "contour_csv_component_option": "Specified",
                   "contour_csv_iteration_file_option": "Single file",
                   "iteration_precision": 9}
    if input_units is not None:
        if set(input_units) != {"length_unit", "mass_unit", "time_unit"} or any(
                not isinstance(value, str) or not value.strip() for value in input_units.values()):
            raise ValueError("supply verified input length, mass and time units together")
        preferences.update(read_units=False, **input_units)
    if any(output.glob("random-displacement*.csv")):
        raise FileExistsError("use a fresh CSV output prefix")
    root = ET.Element("NXPostProcessingTemplate", TemplateType="User", Version="NX2612")
    result = ET.SubElement(ET.SubElement(root, "PostView"), "ResultOptions")
    ET.SubElement(result, "Result").text = unique_name
    ET.SubElement(result, "Component").text = component
    with path.open("xb") as stream:
        ET.ElementTree(root).write(stream, encoding="utf-8", xml_declaration=True)
    return {
        "preferences_before_open": preferences,
        "contour": {"to": selected(str(output.resolve() / "random-displacement.csv")),
                    "loadcase_index": selected(loadcase),
                    "iteration_index": {"type": "list", "values": [s["iteration"] for s in states]},
                    "result": selected(str(path)), "node_ids": str(node)},
        "states": states, "node": node, "component": component,
        "loadcase_name": next(case["name"] for case in catalog["loadcases"] if case["index"] == loadcase),
    }


def verify_csv(path, plan, unit):
    """Read back one English 2612 displacement table and bind every value to its state."""
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        rows = [[cell.strip() for cell in row] for row in csv.reader(stream) if any(cell.strip() for cell in row)]
    if len(rows) != 8 or len(rows[7]) < 5 or len(rows[6]) < 5:
        raise ValueError("expected metadata, one column header and one requested node")
    states = plan["states"]
    if (rows[1] != [f"Result : {states[0]['result_name']}"] or rows[2] != [f"Result Units : {unit}"]
            or rows[6][:4] != ["Node ID", "X Coord", "Y Coord", "Z Coord"]
            or rows[7][0] != str(plan["node"])):
        raise ValueError("unexpected result, unit, layout or node")
    labels, headers, values = rows[5][4:], rows[6][4:], rows[7][4:]
    if len({len(labels), len(headers), len(values), len(states)}) != 1 or len(set(labels)) != len(labels):
        raise ValueError("missing, extra or ambiguous result columns")
    expected_rms_header = {"X": "1", "Y": "2", "Z": "3"}[plan["component"]]
    by_frequency = {s["frequency_hz"]: s for s in states}
    result = []
    prefix = plan["loadcase_name"] + " - "
    for label, header, value in zip(labels, headers, values):
        if not label.startswith(prefix):
            raise ValueError("unexpected loadcase label")
        if None in by_frequency:
            if not label.endswith(" - Root Mean Square Results") or header != expected_rms_header:
                raise ValueError("unexpected RMS state or component")
            frequency = None
        else:
            if not Path(path).stem.endswith(f"-{plan['component']}"):
                raise ValueError("PSD export filename does not identify the selected component")
            match = re.fullmatch(r"Frequency \d+, (\d+(?:\.\d+)?)\s*Hz", label.removeprefix(prefix))
            if not match:
                raise ValueError("missing PSD frequency label")
            frequency = float(match[1])
        if frequency not in by_frequency:
            raise ValueError("unexpected or ambiguously rounded frequency label")
        iteration = by_frequency.pop(frequency)["iteration"]
        number = float(value)
        if not math.isfinite(number) or number < 0:
            raise ValueError("invalid random displacement value")
        result.append({"iteration": iteration, "frequency_hz": frequency, "value": number})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--loadcase", type=int, required=True)
    parser.add_argument("--node", type=int, required=True)
    parser.add_argument("--component", choices=("X", "Y", "Z"), required=True)
    parser.add_argument("--result", required=True, help="exact discovered XML unique_name")
    parser.add_argument("--input-units", nargs=3, metavar=("LENGTH", "MASS", "TIME"))
    args = parser.parse_args()
    units = dict(zip(("length_unit", "mass_unit", "time_unit"), args.input_units)) if args.input_units else None
    catalog = json.loads(args.catalog.read_text(encoding="utf-8-sig"))
    print(json.dumps(prepare(catalog, args.loadcase, args.result, args.component, args.node,
                             args.output, input_units=units), indent=2))
