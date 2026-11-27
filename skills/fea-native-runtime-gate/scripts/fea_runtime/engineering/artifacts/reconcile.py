# SPDX-License-Identifier: Apache-2.0
# Imported from FEA Expert Agent Plugin, fea_agent/artifacts/reconcile.py
"""Reject inconsistent model/result identities and misleading table comparisons."""
from __future__ import annotations

import json
import math
from typing import cast

import numpy as np
from numpy.typing import NDArray

from .common import ArtifactError


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ArtifactError("ARTIFACT_CONTRACT_INVALID", label)
    return cast(dict[str, object], value)


def _list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ArtifactError("ARTIFACT_CONTRACT_INVALID", label)
    return cast(list[object], value)


def _values(value: object, label: str) -> list[object]:
    array = _object(value, label)
    if not array.get("complete") or array.get("values") is None:
        raise ArtifactError("SELECTION_INCOMPLETE", label)
    return _list(array["values"], label)


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ArtifactError("NONINTEGER_ENTITY_ID", label)
    return value


def _integers(value: object, label: str) -> NDArray[np.int64]:
    arr = np.asarray(value)
    if arr.dtype.kind not in "iu":
        raise ArtifactError("NONINTEGER_ENTITY_ID", label)
    return np.asarray(arr, dtype=np.int64)


def reconcile_model_results(model_report: dict[str, object], results_report: dict[str, object]) -> dict[str, object]:
    """Check selected entity and physical-state compatibility, not authenticity."""
    model = _object(model_report.get("payload"), "model.payload")
    results = _object(results_report.get("payload"), "results.payload")
    if model.get("kind") != "NASTRAN_MODEL" or results.get("kind") != "NASTRAN_RESULTS":
        raise ArtifactError("ARTIFACT_KIND_MISMATCH")
    findings: list[dict[str, object]] = []
    if not model_report.get("bounded_output_complete", False):
        findings.append({"severity": "UNRESOLVED", "code": "MODEL_DATA_OMITTED"})
    if not results_report.get("bounded_output_complete", False):
        findings.append({"severity": "UNRESOLVED", "code": "RESULT_DATA_OMITTED"})
    nodes = _object(model.get("nodes"), "model.nodes")
    labels = _values(nodes.get("labels"), "model.node_labels")
    if nodes.get("count") != len(labels):
        raise ArtifactError("MODEL_SELECTION_INCOMPLETE", "Reconciliation requires all model GRID labels")
    nids = set(_integer(n, "node label") for n in labels)
    elements = _list(model.get("elements"), "model.elements")
    if model.get("element_count") != len(elements):
        raise ArtifactError("MODEL_SELECTION_INCOMPLETE", "Reconciliation requires all model elements")
    by_eid = {_integer(_object(e, "element")["label"], "element label"): _object(e, "element") for e in elements}
    properties = {_integer(_object(p, "property")["id"], "property id"): _object(p, "property")
                  for p in _list(model.get("properties"), "properties")}
    subcases = {_integer(_object(s, "subcase")["subcase_id"], "subcase id") for s in _list(model.get("effective_case_control"), "case control")}
    if subcases == {0}:
        subcases.add(1)  # Nastran global-only case control is output as subcase 1.
    model_source = _object(model_report.get("source"), "model.source")
    result_source = _object(results_report.get("source"), "results.source")
    if not model_source.get("units") or not result_source.get("units"):
        findings.append({"severity": "UNRESOLVED", "code": "UNITS_NOT_ESTABLISHED"})
    elif model_source["units"] != result_source["units"]:
        findings.append({"severity": "ERROR", "code": "UNIT_DECLARATION_MISMATCH"})
    table_count = 0
    for raw_table in _list(results.get("tables"), "results.tables"):
        table = _object(raw_table, "table")
        table_count += 1
        name = str(table["name"])
        sid = _integer(table["subcase_id"], "table subcase")
        if sid not in subcases:
            findings.append({"severity": "ERROR", "code": "SUBCASE_NOT_IN_DECK", "table": name, "subcase": sid})
        expected = {101: {1}, 103: {2}, 105: {1, 7, 8}, 108: {5}, 109: {6}, 111: {2, 5}, 112: {2, 6}}.get(cast(int, model.get("solution")))
        if expected and table.get("analysis_code") not in expected:
            findings.append({"severity": "ERROR", "code": "SOLUTION_STATE_MISMATCH", "table": name})
        identity = _object(table.get("identity"), "identity")
        if not identity:
            findings.append({"severity": "UNRESOLVED", "code": "RECOVERY_IDENTITY_MISSING", "table": name})
        for key in ("node_gridtype", "element_node", "element_layer", "element"):
            if key not in identity:
                continue
            try:
                rows = _values(identity[key], key)
            except ArtifactError:
                findings.append({"severity": "UNRESOLVED", "code": "IDENTITY_SELECTION_INCOMPLETE", "table": name})
                continue
            array = _integers(rows, key)
            if key == "node_gridtype":
                for nid, gridtype in array:
                    if int(gridtype) == 1 and int(nid) not in nids:
                        findings.append({"severity": "ERROR", "code": "NODE_NOT_IN_DECK", "table": name, "node": int(nid)})
            else:
                eids = array[:, 0] if key in {"element_node", "element_layer"} else array.ravel()
                for eid in sorted(set(int(e) for e in eids)):
                    if eid not in by_eid:
                        # Energy tables may contain a total/sentinel row. Do not
                        # claim it is a physical element or silently discard it.
                        severity = "UNRESOLVED" if name.startswith("strain_energy.") else "ERROR"
                        findings.append({"severity": severity, "code": "ELEMENT_NOT_IN_DECK", "table": name, "element": eid})
                if key == "element_node":
                    for eid, nid in array:
                        if int(nid) != 0 and int(nid) not in nids:
                            findings.append({"severity": "ERROR", "code": "RECOVERY_NODE_NOT_IN_DECK", "table": name, "element": int(eid), "node": int(nid)})
                        elif int(nid) != 0 and int(eid) in by_eid:
                            connectivity = _list(by_eid[int(eid)].get("node_labels"), "element.node_labels")
                            if int(nid) not in connectivity:
                                findings.append({"severity": "ERROR", "code": "RECOVERY_NODE_NOT_IN_ELEMENT", "table": name, "element": int(eid), "node": int(nid)})
                if key == "element_layer":
                    for eid, ply in array:
                        element = by_eid.get(int(eid), {})
                        prop = properties.get(cast(int, element.get("property_id")), {})
                        if prop.get("type") == "PCOMP":
                            lam = _object(prop.get("laminate"), "laminate")
                            count = len(_list(lam.get("mids"), "laminate mids"))
                            if lam.get("lam") == "SYM":
                                count *= 2
                            if not 1 <= int(ply) <= count:
                                findings.append({"severity": "ERROR", "code": "PLY_NOT_IN_LAMINATE", "table": name, "element": int(eid), "ply": int(ply)})
    if table_count == 0:
        findings.append({"severity": "UNRESOLVED", "code": "NO_NORMALIZED_RESULT_TABLES"})
    if not model.get("cross_reference_complete", False):
        findings.append({"severity": "UNRESOLVED", "code": "MODEL_CROSS_REFERENCE_INCOMPLETE"})
    errors = sum(row["severity"] == "ERROR" for row in findings)
    unknowns = sum(row["severity"] == "UNRESOLVED" for row in findings)
    return {"schema": "fea.artifact-reconciliation.v3", "status": "REJECTED" if errors else "UNRESOLVED" if unknowns else "COMPATIBLE_SELECTED_IDENTITIES",
            "model_sha256": model_source.get("sha256"), "result_sha256": result_source.get("sha256"),
            "tables_checked": table_count, "findings": findings,
            "authentic_deck_job_binding": "NOT_ESTABLISHED", "engineering_acceptance": "NOT_ESTABLISHED",
            "limits": ["Matching labels are necessary but do not bind a result to a model revision or solver job",
                       "GRID CD and element/material frames remain source conventions; no frame equivalence is inferred",
                       "Partial OP2 output cannot establish missing-table completeness or solver convergence"]}


def _data(table: dict[str, object]) -> NDArray[np.complex128]:
    entry = _object(table.get("data"), "table.data")
    if not entry.get("complete"):
        raise ArtifactError("SELECTION_INCOMPLETE", "table values")
    if entry.get("representation") == "REAL_IMAGINARY":
        data = np.asarray(entry.get("real"), dtype=float) + 1j * np.asarray(entry.get("imaginary"), dtype=float)
    else:
        data = np.asarray(entry.get("values"), dtype=complex)
    if data.ndim != 3 or not np.all(np.isfinite(data)):
        raise ArtifactError("NONFINITE_OR_INVALID_RESULT_DATA")
    return cast(NDArray[np.complex128], data)


def _row_keys(table: dict[str, object], data: NDArray[np.complex128]) -> list[str]:
    identity = _object(table.get("identity"), "identity")
    parts: list[list[object]] = [[] for _ in range(data.shape[1])]
    for name, value in sorted(identity.items()):
        item = _object(value, name)
        if item.get("alignment") != "RECOVERY_ROW":
            continue
        rows = _values(item, name)
        if len(rows) != len(parts):
            raise ArtifactError("IDENTITY_LAYOUT_MISMATCH", name)
        for output, row in zip(parts, rows, strict=True):
            output.append([name, row])
    if not any(parts):
        raise ArtifactError("RECOVERY_IDENTITY_MISSING")
    components = _list(table.get("components"), "components")
    for name in ("fiber_distance", "fiber_curvature", "sd", "xxb"):
        if name in components:
            j = components.index(name)
            for i, output in enumerate(parts):
                if not np.all(data[:, i, j] == data[0, i, j]):
                    raise ArtifactError("STATE_DEPENDENT_RECOVERY_LOCATION")
                output.append([name, [float(data[0, i, j].real), float(data[0, i, j].imag)]])
    keys = [json.dumps(row, sort_keys=True, separators=(",", ":")) for row in parts]
    if len(set(keys)) != len(keys):
        raise ArtifactError("AMBIGUOUS_RECOVERY_IDENTITY", "Repeated element/node rows require ply, side or station evidence")
    return keys


def compare_result_tables(reference: dict[str, object], candidate: dict[str, object], *,
                          atol: float = 1e-10, rtol: float = 1e-6) -> dict[str, object]:
    """Compare fully selected, semantically matching tables by physical row ID.

    This is a source-data comparison. Unit/frame equivalence and independent
    truth are not established simply because two imported arrays agree.
    """
    if not math.isfinite(atol) or not math.isfinite(rtol) or min(atol, rtol) < 0:
        raise ArtifactError("INVALID_TOLERANCE")
    for key in ("name", "key", "subcase_id", "analysis_code", "components", "states", "frame", "shell_layer_semantics"):
        if reference.get(key) != candidate.get(key):
            return {"status": "REJECTED", "code": "PHYSICAL_STATE_MISMATCH", "field": key}
    for key in ("table_name", "element_type", "element_name", "sort_method", "s_code", "stress_bits", "thermal"):
        if _object(reference.get("metadata"), "reference.metadata").get(key) != _object(candidate.get("metadata"), "candidate.metadata").get(key):
            return {"status": "REJECTED", "code": "RESULT_CONVENTION_MISMATCH", "field": key}
    reference_identity = _object(reference.get("identity"), "reference.identity")
    candidate_identity = _object(candidate.get("identity"), "candidate.identity")
    if set(reference_identity) != set(candidate_identity):
        return {"status": "REJECTED", "code": "RECOVERY_IDENTITY_SCHEMA_MISMATCH"}
    for key in reference_identity:
        left_id = _object(reference_identity[key], key)
        right_id = _object(candidate_identity[key], key)
        if left_id.get("alignment") != right_id.get("alignment"):
            return {"status": "REJECTED", "code": "RECOVERY_IDENTITY_SCHEMA_MISMATCH", "field": key}
        if left_id.get("alignment") != "RECOVERY_ROW":
            if _values(left_id, key) != _values(right_id, key):
                return {"status": "REJECTED", "code": "RESULT_FRAME_OR_STATE_MAPPING_MISMATCH", "field": key}
    left, right = _data(reference), _data(candidate)
    if left.shape != right.shape:
        return {"status": "REJECTED", "code": "RESULT_SHAPE_MISMATCH"}
    lkeys, rkeys = _row_keys(reference, left), _row_keys(candidate, right)
    if set(lkeys) != set(rkeys):
        return {"status": "REJECTED", "code": "RECOVERY_LOCATION_MISMATCH"}
    mapping = {key: i for i, key in enumerate(rkeys)}
    right = right[:, [mapping[key] for key in lkeys], :]
    delta = np.abs(right - left)
    tolerance = atol + rtol * np.abs(left)
    failed = delta > tolerance
    worst = np.unravel_index(int(np.argmax(delta)), delta.shape) if delta.size else (0, 0, 0)
    return {"status": "REJECTED" if bool(np.any(failed)) else "TABLE_DATA_AGREEMENT", "comparison": "COMPLEX_COMPONENTS_BY_RECOVERY_ID",
            "failed_values": int(np.count_nonzero(failed)), "compared_values": int(delta.size),
            "max_absolute_difference": float(delta.max()) if delta.size else 0.0,
            "worst_state_row_component": [int(i) for i in worst], "atol": atol, "rtol": rtol,
            "unit_and_frame_equivalence": "REQUIRES_EXTERNAL_EVIDENCE", "engineering_acceptance": "NOT_ESTABLISHED"}
