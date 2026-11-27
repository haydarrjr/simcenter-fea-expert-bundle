"""Independent CSV coverage checks for an exact native contour selection."""

import csv
import math
import os
from pathlib import Path

from .contracts import Blocked, scoped_path


def export_paths(root, request, binding, raw):
    data = raw.get("structuredContent") if isinstance(raw, dict) else None
    paths = data.get("written_files") if isinstance(data, dict) else None
    if not isinstance(paths, list) or len(paths) != 1 or not isinstance(paths[0], str):
        raise Blocked("exactly one reported native contour output is required")
    actual = Path(paths[0])
    prefix = scoped_path(root, binding["qualification"]["output_prefix"], exists=False)
    if (not actual.is_absolute() or not actual.is_relative_to(root) or actual.parent != prefix.parent
            or actual.suffix.lower() != ".csv"
            or not actual.name.casefold().startswith(prefix.stem.casefold() + "-")):
        raise Blocked("native contour reported a file outside the approved output prefix")
    path = scoped_path(root, actual.relative_to(root).as_posix())
    if path.stat().st_size > 32 * 1024**2:
        raise Blocked("native contour export exceeds the bounded CSV reader")
    selection = binding["qualification"]["selection"]
    catalog = binding["qualification"]["result_catalog"]
    case = next(item for item in catalog["loadcases"] if item["index"] == selection["case"])
    iteration = next(item for item in case["iterations"] if item["index"] == selection["state"])
    result = next(item for item in iteration["result_types"] if item["unique_name"] == selection["result"])
    values = read_csv(path, selection, result["name"], case["name"], iteration["description"])
    return path, values


def read_csv(path, selection, result_name, case_name, state_name):
    values = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        details = {}
        for row in reader:
            if not row:
                break
            if len(row) != 1 or ":" not in row[0]:
                raise ValueError("unexpected native CSV metadata")
            key, _, value = row[0].partition(":")
            key = key.strip()
            if key in details or len(details) >= 16:
                raise ValueError("native CSV metadata is duplicate or incomplete")
            details[key] = value.strip()
        expected = {"Result": result_name, "Result Units": selection["units"],
                    "Coordinate System": selection["frame"]}
        if any(details.get(key) != value for key, value in expected.items()):
            raise ValueError("native CSV field, units or frame differs from the selection")
        group = [cell.strip() for cell in next(reader, []) if cell.strip()]
        if group != [f"{case_name} - {state_name}"]:
            raise ValueError("native CSV does not identify the exact requested case and state")
        columns = [column.strip() for column in next(reader, [])]
        label_column = "Node ID" if selection["position"] == "Nodal" else "Elem ID"
        if (not columns or columns[0] != label_column or len(set(columns)) != len(columns)
                or selection["component"] not in columns[4:]):
            raise ValueError("native CSV entity or component coverage differs from the selection")
        component_index = columns.index(selection["component"])
        wanted = set(selection["labels"])
        for row in reader:
            if not row:
                continue
            if len(row) != len(columns) or len(values) >= len(wanted):
                raise ValueError("unexpected row count or column coverage")
            label = int(row[0])
            numbers = [float(token) for token in row[1:]]
            if label not in wanted or label in values or not all(map(math.isfinite, numbers)):
                raise ValueError("foreign, duplicate or nonfinite native CSV row")
            values[label] = numbers[component_index - 1]
    if set(values) != wanted:
        raise ValueError("native CSV is missing selected entity labels")
    return {str(label): values[label] for label in selection["labels"]}
