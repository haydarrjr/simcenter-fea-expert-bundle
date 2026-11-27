# SPDX-License-Identifier: Apache-2.0
# Imported from FEA Expert Agent Plugin, fea_agent/artifacts/bdf.py
"""Broad BDF source inspection through pinned pyNastran, without solving."""
from __future__ import annotations

import importlib
from pathlib import Path
import re
from typing import Protocol, cast

import numpy as np

from .common import ArtifactError, ArtifactLimits, Budget, dependency, logger, plain, selection


_SENSITIVE_DIRECTIVES = re.compile(r"(?im)^\s*(?:INCLUDE\b|ASSIGN\b|ALTER\b|COMPILE\b|LINK\b|SYSTEM\b)")


class _Card(Protocol):
    type: str

    def raw_fields(self) -> list[object]: ...


def _card(card: object, budget: Budget, label: str) -> dict[str, object]:
    source = cast(_Card, card)
    fields = source.raw_fields()
    cost = len(fields)
    if cost > budget.remaining:
        budget.omissions.append(label)
        return {"type": str(source.type), "fields": None, "complete": False}
    budget.remaining -= cost
    return {"type": str(source.type), "fields": plain(fields), "complete": True}


def _cards(cards: object, budget: Budget, label: str, limits: ArtifactLimits) -> list[dict[str, object]]:
    values = cast(dict[object, object], cards)
    if len(values) > limits.max_entities:
        raise ArtifactError("ENTITY_LIMIT", label)
    result: list[dict[str, object]] = []
    for key, item in values.items():
        group = item if isinstance(item, list) else [item]
        for card in group:
            if budget.remaining < 2:
                budget.omissions.append(label)
                return result
            row = _card(card, budget, label)
            row["id"] = plain(key)
            result.append(row)
    return result


def read_bdf(path: Path, options: dict[str, object], limits: ArtifactLimits, budget: Budget) -> dict[str, object]:
    dependency("pyNastran", "1.4.1")
    raw = path.read_bytes()
    if b"\0" in raw:
        raise ArtifactError("BINARY_NOT_BDF", "Native Siemens FEM/SIM binaries are not Nastran bulk-data decks")
    text = raw.decode("latin1")
    if _SENSITIVE_DIRECTIVES.search(text):
        raise ArtifactError("EXTERNAL_OR_EXECUTABLE_DIRECTIVE", "Flatten INCLUDE/ASSIGN and remove executable executive directives before inspection; source files are never followed or executed")
    if any(len(line) > 4096 for line in text.splitlines()):
        raise ArtifactError("BDF_LINE_LIMIT")
    module = importlib.import_module("pyNastran.bdf.bdf")
    model = module.BDF(debug=None, log=logger(), mode=options.get("nastran_dialect", "msc"))
    model.read_bdf(str(path), validate=True, xref=False, punch=bool(options.get("punch", False)),
                   read_includes=False, encoding="latin1")
    if len(model.nodes) + len(model.elements) + len(model.masses) > limits.max_entities:
        raise ArtifactError("ENTITY_LIMIT", "BDF nodes + elements + masses")
    warnings: list[str] = []
    xref = True
    try:
        model.cross_reference()
    except Exception as exc:
        xref = False
        warnings.append(f"CROSS_REFERENCE_INCOMPLETE:{type(exc).__name__}")
    nodes = sorted(model.nodes.items())
    selected_nodes = nodes[selection(options, len(nodes), "row")]
    xyz = []
    unresolved = []
    for nid, node in selected_nodes:
        try:
            pos = np.asarray(node.get_position(), dtype=float)
            if pos.shape != (3,) or not np.all(np.isfinite(pos)):
                raise ValueError("invalid coordinate")
            xyz.append(pos.tolist())
        except Exception:
            xyz.append([float("nan")] * 3)
            unresolved.append(nid)
    node_result: dict[str, object] = {
        "count": len(nodes), "selection_start": selection(options, len(nodes), "row").start,
        "labels": budget.array([nid for nid, _ in selected_nodes], "node_labels"),
        "xyz_basic": budget.array(xyz, "node_xyz_basic"),
        "xyz_input": budget.array([n.xyz for _, n in selected_nodes], "node_xyz_input"),
        "cp": budget.array([n.Cp() for _, n in selected_nodes], "node_cp"),
        "cd": budget.array([n.Cd() for _, n in selected_nodes], "node_cd"),
        "ps": budget.array([n.ps or "" for _, n in selected_nodes], "node_ps"),
        "seid": budget.array([n.seid or 0 for _, n in selected_nodes], "node_seid"),
        "unresolved_basic_coordinates": unresolved, "identity": "GRID_LABEL",
        "coordinate_status": "PARTIAL" if unresolved else "RESOLVED_TO_BASIC"}
    elements: list[dict[str, object]] = []
    element_items = sorted(model.elements.items())
    for eid, elem in element_items[selection(options, len(element_items), "row")]:
        if budget.remaining < 24:
            budget.omissions.append("elements")
            break
        budget.remaining -= 12
        row = _card(elem, budget, "element_fields")
        row.update({"label": eid, "node_labels": plain(elem.node_ids),
                    "property_id": plain(getattr(elem, "pid", None))})
        etype = str(elem.type)
        if etype in {"CBAR", "CBEAM"}:
            row["orientation_definition"] = {name: plain(getattr(elem, name, None))
                                               for name in ("x", "g0", "offt", "bit", "wa", "wb", "pa", "pb")}
            if xref:
                try:
                    failed, axes = elem.get_axes(model)
                    if failed:
                        raise ValueError("orientation")
                    # pyNastran returns v, i, j, k, wa, wb; preserve names.
                    row["basic_axes_and_offsets"] = {name: plain(value) for name, value in
                                                     zip(("orientation_vector", "i", "j", "k", "offset_a", "offset_b"), axes, strict=True)}
                except Exception as exc:
                    row["orientation_status"] = f"UNRESOLVED:{type(exc).__name__}"
                    warnings.append(f"BEAM_ORIENTATION_UNRESOLVED:{eid}")
        if etype.startswith(("CQUAD", "CTRIA")):
            row["shell_definition"] = {name: plain(getattr(elem, name, None))
                                        for name in ("theta_mcid", "zoffset", "tflag", "T1", "T2", "T3", "T4")}
            if xref and hasattr(elem, "material_coordinate_system"):
                try:
                    length, centroid, i, j, normal = elem.material_coordinate_system()
                    row["material_frame"] = {"i": plain(i), "j": plain(j), "normal": plain(normal),
                                              "centroid": plain(centroid), "characteristic_length": plain(length)}
                except Exception as exc:
                    row["material_frame_status"] = f"UNRESOLVED:{type(exc).__name__}"
        elements.append(row)
    properties = _cards(model.properties, budget, "properties", limits)
    for row in properties:
        prop = model.properties[row["id"]]
        if str(prop.type) in {"PCOMP", "PCOMPG"}:
            row["laminate"] = {name: plain(getattr(prop, name, None))
                                for name in ("mids", "thicknesses", "thetas", "souts", "z0", "lam", "nsm", "tref", "ft", "sb")}
    def case_value(value: object) -> object:
        if isinstance(value, dict):
            return {str(key): case_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [case_value(item) for item in value]
        try:
            return plain(value)
        except ArtifactError:
            return {"upstream_type": type(value).__name__, "source_text": str(value)}
    case_control = []
    for sid, subcase in model.subcases.items():
        case_control.append({"subcase_id": int(sid), "effective_parameters": case_value(subcase.params)})
    effective_loads: list[dict[str, object]] = []
    effective_spcs: list[dict[str, object]] = []
    # pyNastran resolves inherited case control. Cyclic LOAD/SPCADD graphs are
    # rejected before invoking recursive upstream combination expansion.
    def check_cycles(collection: object, attr: str) -> None:
        graph: dict[int, list[int]] = {}
        for key, value in cast(dict[int, object], collection).items():
            cards = value if isinstance(value, list) else [value]
            graph[key] = []
            for card in cards:
                links = getattr(card, attr, [])
                for link in links:
                    if isinstance(link, int):
                        graph[key].append(link)
        done: set[int] = set()
        active: set[int] = set()
        def visit(key: int, depth: int) -> None:
            if key in active or depth > 100:
                raise ArtifactError("CYCLIC_OR_DEEP_COMBINATION", str(key))
            if key in done:
                return
            active.add(key)
            for target in graph.get(key, []):
                visit(target, depth + 1)
            active.remove(key)
            done.add(key)
        for key in graph:
            visit(key, 0)
    check_cycles(model.load_combinations, "load_ids")
    check_cycles(model.spcadds, "sets")
    for sid, subcase in model.subcases.items():
        for keyword in ("LOAD", "SPC"):
            if keyword not in subcase.params:
                continue
            setid = int(subcase.params[keyword][0])
            try:
                if keyword == "LOAD":
                    reduced, factors, is_grav = model.get_reduced_loads(setid)
                    rows = []
                    for card, factor in zip(reduced, factors, strict=True):
                        if budget.remaining < 4:
                            budget.omissions.append("effective_loads")
                            break
                        record = _card(card, budget, "effective_loads")
                        record["scale"] = float(factor)
                        rows.append(record)
                    effective_loads.append({"subcase_id": sid, "set_id": setid, "records": rows,
                                            "gravity_present": bool(is_grav), "resolved": True})
                else:
                    rows = [_card(card, budget, "effective_spcs") for card in model.get_reduced_spcs(setid)]
                    effective_spcs.append({"subcase_id": sid, "set_id": setid, "records": rows, "resolved": True})
            except ArtifactError:
                raise
            except Exception as exc:
                target = effective_loads if keyword == "LOAD" else effective_spcs
                target.append({"subcase_id": sid, "set_id": setid, "resolved": False,
                               "reason": type(exc).__name__})
                warnings.append(f"{keyword}_UNRESOLVED:{sid}")
    rejected = {"cards": len(model.reject_cards), "lines": len(model.reject_lines)}
    if any(rejected.values()):
        warnings.append("UPSTREAM_REJECTED_CARDS_PRESENT")
    additional_collections: dict[str, object] = {}
    for name in ("methods", "cMethods", "dloads", "dload_entries", "dareas", "frequencies", "tsteps", "tstepnls",
                 "nlparms", "nlpcis", "bcs", "convection_properties", "phbdys", "bctsets", "bctadds", "bctparas",
                 "bfric", "bcbodys", "bcrparas", "tables", "tables_d", "tables_m"):
        collection = getattr(model, name, None)
        if isinstance(collection, dict) and collection:
            additional_collections[name] = _cards(collection, budget, name, limits)
    return {"kind": "NASTRAN_MODEL", "solution": plain(model.sol), "dialect": str(model.nastran_format),
            "reader": {"name": "pyNastran", "version": "1.4.1"}, "nodes": node_result,
            "element_count": len(model.elements), "elements": elements,
            "card_counts": plain(model.card_count), "properties": properties,
            "parameters": _cards(model.params, budget, "parameters", limits),
            "additional_card_collections": additional_collections,
            "materials": _cards(model.materials, budget, "materials", limits),
            "thermal_materials": _cards(model.thermal_materials, budget, "thermal_materials", limits),
            "coordinate_systems": _cards(model.coords, budget, "coordinates", limits),
            "masses": _cards(model.masses, budget, "masses", limits),
            "rigid_elements": _cards(model.rigid_elements, budget, "rigid_elements", limits),
            "loads": _cards(model.loads, budget, "loads", limits),
            "load_combinations": _cards(model.load_combinations, budget, "load_combinations", limits),
            "spcs": _cards(model.spcs, budget, "spcs", limits),
            "mpcs": _cards(model.mpcs, budget, "mpcs", limits),
            "effective_case_control": case_control, "effective_static_loads": effective_loads,
            "effective_spcs": effective_spcs, "cross_reference_complete": xref,
            "rejected_record_counts": rejected, "warnings": warnings,
            "scalar_point_labels": sorted(model.spoints), "extra_point_labels": sorted(model.epoints),
            "limits": ["Parsing is not execution or proof of a well-posed model",
                       "All card families are counted; detailed fields cover the named collections only",
                       "Dynamic, thermal, contact and nonlinear records require solver-specific interpretation",
                       "No unit system is inferred; native Siemens .fem/.sim files are not decoded",
                       "External INCLUDE files and executable executive directives are refused"]}
