"""Compare the exported synthetic static fixture results with independent mechanics.

Run this script after native Save/reopen, scoped BatchPost CSV export and batch solve.
It reads only the plain-text and CSV results for the named job and the hashes of native files.
"""
import argparse
import csv
from hashlib import sha256
import json
import math
from pathlib import Path
import re


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_quantity(job, prefix, units, expected_entities, component, state_pattern):
    matches = sorted(job.glob(f"{prefix}*.csv"))
    require(len(matches) == 1, f"Expected one CSV for {prefix}: {len(matches)}")
    path = matches[0]
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    require(f"Result Units : {units}" in lines, f"Incorrect units in {path.name}")
    heading = next(i for i, line in enumerate(lines) if re.match(r"\s*(Node ID|Elem ID),", line))
    require(re.search(state_pattern, lines[heading - 1]), f"Wrong result state in {path.name}")
    fields = [value.strip() for value in next(csv.reader([lines[heading]]))]
    ids = [i for i, field in enumerate(fields) if field in ("Node ID", "Elem ID")]
    column = fields.index(component)
    rows = {}
    for row in csv.reader(lines[heading + 1:]):
        if row and row[0].strip():
            key = tuple(int(row[i]) for i in ids)
            require(key not in rows, f"Duplicate result labels in {path.name}: {key}")
            rows[key] = float(row[column])
    require(set(rows) == expected_entities, f"Different entity scope in {path.name}: {set(rows)}")
    return list(rows.values())


def compare(values, expected, label):
    require(all(math.isclose(v, expected, rel_tol=3e-7, abs_tol=1e-10) for v in values),
            f"{label}: expected {expected}, observed {values}")


def verify_402_f06(text):
    tables = {
        "u": "D I S P L A C E M E N T   V E C T O R",
        "r": "F O R C E S   O F   S I N G L E - P O I N T",
        "sx": "S T R E S S E S   I N   H E X A H E D R O N",
        "p": "P L A S T I C   S T R A I N S   I N   H E X A H E D R O N",
    }
    observed = {}
    for page in re.split(r"(?m)^1 +.*\bPAGE +\d+ *$", text):
        title = re.search(r"(?m)^0 +(?P<case>LOAD PAST YIELD|UNLOAD)\s*\n\s*TIME\s*=\s*(?P<time>\S+)", page)
        if not title:
            continue
        for quantity, heading in tables.items():
            if heading not in page:
                continue
            key = title["case"], float(title["time"]), quantity
            require(key not in observed, f"Duplicate F06 table: {key}")
            content = page.split(heading, 1)[1]
            if quantity in ("u", "r"):
                rows = re.findall(r"(?m)^\s*(\d+)\s+G\s+(\S+)", content)
                values = {int(label): float(value) for label, value in rows}
            else:
                require(re.search(r"(?m)^\s+1\s+0\s+GRID\s*$", content),
                        f"Missing fixture element in {key}")
                rows = re.findall(r"(?m)^ +([1-8]) +([+\-\d.E]+) +(?:[+\-\d.E]+ +){5}([+\-\d.E]+) *$", content)
                values = {int(label): float(first if quantity == "sx" else last)
                          for label, first, last in rows}
            require(set(values) == set(range(1, 9)) and len(rows) == 8,
                    f"Wrong or duplicate F06 label scope: {key}")
            observed[key] = values
    expected_keys = set()
    report = []
    for case, initial_time in (("LOAD PAST YIELD", 0), ("UNLOAD", 1)):
        increments = []
        for increment in range(1, 5):
            time = initial_time + increment / 4
            stress = 150 * increment / 4 if initial_time == 0 else 150 - 100 * increment / 4
            plastic = max(0., stress - 100) / 10000 if initial_time == 0 else 0.005
            expected_keys.update((case, time, key) for key in tables)
            u = observed[case, time, "u"][2] * 1000
            fx = sum(observed[case, time, "r"].values())
            compare([u], 100 * (stress / 100000 + plastic), f"{case} {time} Ux")
            compare([fx], -stress * 100, f"{case} {time} Fx")
            compare([x / 1e6 for x in observed[case, time, "sx"].values()], stress, f"{case} {time} Sxx")
            compare(observed[case, time, "p"].values(), plastic, f"{case} {time} plastic strain")
            increments.append({"time": time, "ux_mm": u, "reaction_N": fx,
                               "stress_MPa": observed[case, time, "sx"][1] / 1e6,
                               "plastic_strain": observed[case, time, "p"][1]})
        report.append({"subcase": case, "increments": increments})
    require(set(observed) == expected_keys, "Unexpected F06 result states")
    return report


def verify_live_402(live, case_root, job_result, f06_steps):
    path, name = live["native_result"]["ref"]
    attached = Path(path) / name
    require(attached.resolve() == (case_root / job_result.name).resolve()
            and digest(attached) == digest(job_result), "Live result differs from solved OP2")
    require(live["model_inspection"]["matching_work_and_display"],
            "Live Model Inspection did not confirm the reopened SIM")
    states = live["native_result"]["values"]
    require(len(states) == len(f06_steps), "Wrong live loadcase count")
    for state, expected_name, f06 in zip(states, ("LOAD PAST YIELD", "UNLOAD"), f06_steps):
        case, labels, displacement, unit = state
        times = [float(re.search(r"Time\s*=\s*(\S+)\s+s$", label)[1]) for label in labels]
        require(case == expected_name and times == [x["time"] for x in f06["increments"]],
                f"Wrong live result states: {state}")
        require(unit in ("Meter", "MilliMeter"), f"Unexpected live displacement unit: {unit}")
        compare([displacement * (1000 if unit == "Meter" else 1)],
                f06["increments"][-1]["ux_mm"], f"{case} live terminal displacement")


def verify(job, case_root, sequence, batch_only=False):
    native = json.loads((case_root / "reopen-and-export.json").read_text(encoding="utf-8"))
    require(str(sequence) in native["type"], "Wrong reopened solution")
    if not batch_only:
        live = json.loads((case_root / "live/receipt.json").read_text(encoding="utf-8"))
        require(live["original_roles_restored"] and live["backend_pids"]["designcenter"] and
                live["backend_pids"]["designcenter"] == live["backend_pids"]["simcenter3d"] and
                live["readback"]["sim"] == native["sim"] and live["readback"]["fem"] == native["fem"],
                "Missing exact live source binding or role restoration")
    require(all(digest(case_root / name) == value for name, value in native["file_sha256"].items()),
            "Saved files changed after reopen")
    deck = job / native["deck"]
    require(digest(deck) == native["deck_sha256"], "Solved file differs from native export")
    f06 = deck.with_suffix(".f06")
    solver_log = deck.with_suffix(".log").read_text(encoding="utf-8", errors="replace")
    f06_text = f06.read_text(encoding="utf-8", errors="replace")
    op2 = deck.with_suffix(".op2")
    require("END OF JOB" in f06_text and "FATAL" not in f06_text
            and re.search(r"Analysis complete\s+0\s*$", solver_log, re.M)
            and op2.stat().st_size > 0, "Missing or unsuccessful solver completion")
    result = {"sequence": sequence, "deck_sha256": digest(deck), "f06_sha256": digest(f06),
              "op2_sha256": digest(op2), "native_reopen": True,
              "live_reopen": "NOT_CHECKED" if batch_only else "VERIFIED"}
    if sequence == 402:
        result["f06_steps"] = verify_402_f06(f06_text)
        if not batch_only:
            verify_live_402(live, case_root, op2, result["f06_steps"])

    if sequence == 101:
        checks = (("ux-", "mm", {(2,)}, "X", .05), ("rx-", "N", {(1,)}, "X", -1000.),
                  ("sx-", "MPa", {(1,)}, "XX", 10.))
        result["outputs"] = {}
        for prefix, units, entities, component, expected in checks:
            values = read_quantity(job, prefix, units, entities, component, r"Static Step 1")
            compare(values, expected, prefix)
            result["outputs"][prefix.rstrip("-")] = values[0]
        return result

    element_results = {(1,)} if sequence == 106 else {(1, i) for i in range(1, 9)}
    effective_state = "Non-Linear Step" if sequence == 106 else "Increment"
    result["steps"] = []
    for case in (1, 2):
        actual = []
        case_header = "LOAD PAST YIELD" if case == 1 else "UNLOAD"
        for increment in range(1, 5):
            stress = 150 * increment / 4 if case == 1 else 150 - 100 * increment / 4
            plastic = max(0., stress - 100) / 10000 if case == 1 else 0.005
            expected = 100 * (stress / 100000 + plastic)
            state = rf"{case_header}.*{effective_state} {increment},"
            values = read_quantity(job, f"u{case}-*{effective_state} {increment},", "mm", {(2,)}, "X", state)
            compare(values, expected, state)
            actual.append(values[0])
        checks = (("sx", "MPa", element_results, "XX", [150., 50.][case - 1]),
                  ("p", "mm/mm", element_results, "Scalar", 0.005),
                  ("r", "N", {(1,), (4,), (5,), (8,)}, "X", [-15000., -5000.][case - 1]))
        step = {"subcase": case, "displacement_mm": actual}
        for label, units, entities, component, expected in checks:
            values = read_quantity(job, f"{label}{case}-", units, entities, component, state)
            if label == "r":
                values = [sum(values)]
            compare(values, expected, f"subcase {case} {label}")
            step[label] = values[0]
        result["steps"].append(step)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sequence", type=int, choices=(101, 106, 401, 402))
    parser.add_argument("case_root", type=Path)
    parser.add_argument("job", type=Path)
    parser.add_argument("--batch-only", action="store_true",
                        help="Verify saved files and numerical results without a live receipt.")
    args = parser.parse_args()
    print(json.dumps(verify(args.job, args.case_root, args.sequence, args.batch_only), indent=2))
