# SPDX-License-Identifier: Apache-2.0
# Imported from FEA Expert Agent Plugin, fea_agent/artifacts/op2.py
"""OP2 physical-state and recovery-location preservation without averaging."""
from __future__ import annotations

import importlib
from pathlib import Path

import numpy as np

from .common import ArtifactError, ArtifactLimits, Budget, dependency, logger, plain, selection


_STATE_NAMES = ("lsdvmns", "modes", "eigns", "eigrs", "eigis", "cycles", "mode_cycles", "freqs", "dts", "times", "lftsfqs", "load_steps", "load_factors")
_IDENTITIES = ("node_gridtype", "element_node", "element_layer", "element", "element_cid", "node_element", "element_names", "xxb")
_ANALYSIS = {1: "STATIC", 2: "REAL_MODES", 5: "FREQUENCY", 6: "TRANSIENT", 7: "PREBUCKLING", 8: "POSTBUCKLING", 9: "COMPLEX_MODES", 10: "NONLINEAR_STATIC", 11: "GEOMETRIC_NONLINEAR"}


def _identity(value: object, rows: slice[int, int, None], states: slice[int, int, None], nrows: int, nstates: int,
              budget: Budget, name: str) -> dict[str, object]:
    arr = np.asarray(value)
    result: dict[str, object] = {}
    attr = name.rsplit(".", 1)[-1]
    if (arr.ndim >= 2 and arr.shape[0] == nstates and arr.shape[1] == nrows
            and (arr.ndim >= 3 or attr in {"element", "element_names"})):
        arr = arr[states, rows]
        result["alignment"] = "STATE_RECOVERY_ROW"
    elif arr.ndim and arr.shape[0] == nrows:
        arr = arr[rows]
        result["alignment"] = "RECOVERY_ROW"
    elif arr.ndim >= 2 and arr.shape[0] == nstates and arr.shape[1] == nrows:
        arr = arr[states, rows]
        result["alignment"] = "STATE_RECOVERY_ROW"
    else:
        result["alignment"] = "TABLE_METADATA"
    result.update(budget.array(arr, name))
    return result


def read_op2(path: Path, options: dict[str, object], limits: ArtifactLimits, budget: Budget) -> dict[str, object]:
    dependency("pyNastran", "1.4.1")
    module = importlib.import_module("pyNastran.op2.op2")
    model = module.OP2(debug=None, log=logger())
    if "result_names" in options:
        model.set_results(options["result_names"])
    if "subcases" in options:
        model.set_subcases(options["subcases"])
    model.read_op2(str(path), combine=False, build_dataframe=False, skip_undefined_matrices=False)
    tables: list[dict[str, object]] = []
    other: list[dict[str, object]] = []
    eigenvalues: list[dict[str, object]] = []
    count = 0
    for name in model.get_table_types():
        try:
            collection = model.get_result(name)
        except (AttributeError, KeyError):
            continue
        if not isinstance(collection, dict):
            continue
        for key, value in collection.items():
            if len(tables) + len(other) + len(eigenvalues) >= limits.max_tables:
                raise ArtifactError("TABLE_LIMIT")
            data = getattr(value, "data", None)
            if not isinstance(data, np.ndarray) or data.ndim != 3:
                if name in {"eigenvalues", "eigenvalues_fluid"}:
                    row: dict[str, object] = {"name": name, "key": plain(key), "class": type(value).__name__}
                    for attr in ("mode", "modes", "extraction_order", "eigenvalues", "radians", "cycles", "generalized_mass", "generalized_stiffness", "damping"):
                        data_attr = getattr(value, attr, None)
                        if data_attr is not None:
                            row[attr] = budget.array(data_attr, f"{name}.{attr}")
                    eigenvalues.append(row)
                else:
                    other.append({"name": name, "key": plain(key), "class": type(value).__name__,
                                  "status": "NOT_NORMALIZED", "reason": "Not a supported three-axis recovery array"})
                continue
            nstates, nrows, ncomponents = data.shape
            count += nstates * nrows
            if count > limits.max_entities * 20 or nrows > limits.max_entities:
                raise ArtifactError("RESULT_ENTITY_LIMIT", name)
            rows = selection(options, nrows, "row")
            states = selection(options, nstates, "state")
            headers = list(value.get_headers())
            if len(headers) != ncomponents:
                raise ArtifactError("COMPONENT_LAYOUT_MISMATCH", name)
            code = int(value.analysis_code)
            record: dict[str, object] = {
                "name": name, "key": plain(key), "class": type(value).__name__,
                "subcase_id": int(value.isubcase), "analysis_code": code,
                "analysis_kind": _ANALYSIS.get(code, "UNRESOLVED"), "components": headers,
                "shape": list(data.shape), "selection": {"row_start": rows.start, "row_stop": rows.stop,
                "state_start": states.start, "state_stop": states.stop},
                "data": budget.array(data[states, rows, :], f"{name}.data"),
                "metadata": {attr: plain(getattr(value, attr, None)) for attr in
                             ("table_name", "title", "subtitle", "label", "element_name", "element_type",
                              "sort_method", "sort_code", "format_code", "s_code", "stress_bits", "thermal")},
                "states": [], "identity": {},
                "frame": ("SCALAR_NO_VECTOR_FRAME" if ncomponents == 1 and name in {"temperatures", "thermal_load_vectors"}
                          else "GRID_CD_REQUIRES_MODEL" if getattr(value, "node_gridtype", None) is not None
                          else "AS_WRITTEN_REQUIRES_ELEMENT_RESULT_CONVENTION"),
                "recovery_policy": "NO_AVERAGING_NO_ABSOLUTE_ENVELOPE_NO_PLY_COLLAPSE"}
            # The full digest makes a bounded selection traceable to the whole
            # upstream table, independent of serialization or complex convention.
            from .common import array_digest
            record["full_data_sha256"] = array_digest(data)
            state_rows: list[dict[str, object]] = []
            for i in range(states.start or 0, states.stop or 0):
                state: dict[str, object] = {"index": i, "analysis_kind": record["analysis_kind"],
                                           "primary_axis_name": str(getattr(value, "name", "UNRESOLVED"))}
                axis = getattr(value, "_times", None)
                state["primary_axis_value"] = plain(axis[i]) if axis is not None and len(axis) == nstates else None
                for attr in _STATE_NAMES:
                    attr_value = getattr(value, attr, None)
                    if attr_value is not None and hasattr(attr_value, "__len__") and len(attr_value) == nstates:
                        state[attr] = plain(attr_value[i])
                state_rows.append(state)
            record["states"] = state_rows
            identity: dict[str, object] = {}
            for attr in _IDENTITIES:
                value_attr = getattr(value, attr, None)
                if value_attr is not None:
                    identity[attr] = _identity(value_attr, rows, states, nrows, nstates, budget, f"{name}.{attr}")
            record["identity"] = identity
            record["location_status"] = "PRESERVED" if identity else "UNRESOLVED"
            if "fiber_distance" in headers:
                record["shell_layer_semantics"] = "SIGNED_FIBER_DISTANCE_PER_RECOVERY_ROW"
            elif "fiber_curvature" in headers:
                record["shell_layer_semantics"] = "FIBER_CURVATURE_NOT_DISTANCE"
            elif "element_layer" in identity:
                record["shell_layer_semantics"] = "ELEMENT_PLY_ID"
            tables.append(record)
    return {"kind": "NASTRAN_RESULTS", "reader": {"name": "pyNastran", "version": "1.4.1"},
            "tables": tables, "eigenvalues": eigenvalues, "uninterpreted_tables": other,
            "detected_binary_table_names": plain(getattr(model, "table_names", [])),
            "selection": {"result_names": options.get("result_names"), "subcases": options.get("subcases")},
            "coverage": "UPSTREAM_SUPPORTED_TABLES_ONLY", "solver_completion": "NOT_ESTABLISHED",
            "warnings": ["OP2 file contents do not prove solver convergence or matching model revision"],
            "limits": ["Frame, units and deck/job identity need independently supplied evidence",
                       "pyNastran-supported records are normalized; uninterpreted records are explicit",
                       "NaN becomes JSON null with nonfinite counts; it is never replaced by zero",
                       "Element-node, ply and state identities are retained without averaging"]}
