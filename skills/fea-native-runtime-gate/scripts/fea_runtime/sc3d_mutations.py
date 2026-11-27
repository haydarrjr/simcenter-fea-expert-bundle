"""Scoped NXOpen mutations for an explicitly owned standalone batch model."""

from hashlib import sha256
from itertools import combinations
import json
from math import dist, isclose, isfinite
from pathlib import Path
from statistics import median

import NXOpen
import NXOpen.CAE as CAE


def open_owned(session, path, *, display):
    parts = session.Parts
    part, status = (parts.OpenBaseDisplay if display else parts.OpenBase)(path)
    try:
        if status.NumberUnloadedParts or Path(part.FullPath) != Path(path):
            raise RuntimeError("NXOpen did not load the exact owned part and its dependencies")
    finally:
        status.Dispose()
    if display and (parts.BaseWork.Tag != part.Tag or parts.BaseDisplay.Tag != part.Tag):
        raise RuntimeError("batch work and display roles differ from the requested part")
    return part


def _one(objects, message):
    if len(objects) != 1:
        raise RuntimeError(message)
    return objects[0]


def _force_cards(card):
    # The installed NodeIDTableForce object emits fixed-width, basic-frame FORCE cards.
    # The owning deck parser remains authoritative for the independently exported deck.
    rows = []
    for line in card:
        if line[:8].strip() != "FORCE":
            continue
        fields = [line[i:i + 8].strip() for i in range(0, 64, 8)]
        if int(fields[3] or "0") != 0 or len(line) > 72:
            raise RuntimeError("only basic-frame fixed-width nodal forces are qualified")
        rows.append([int(fields[2]), *(float(value) for value in fields[4:8])])
    rows.sort()
    return rows


def _force_snapshot(sim, spec):
    selected = []
    other = []
    for solution in sim.Simulation.Solutions:
        memberships = [(None, solution.GetBcs())]
        for index in range(solution.StepCount):
            step = solution.GetStepByIndex(index)
            memberships.append((step.Name, step.GetBcs()))
        for step, conditions in memberships:
            for obj in conditions:
                card = list(obj.GetSolverCardSyntax())
                key = (solution.Name, step, obj.Name)
                if key == (spec["solution"], spec["step"], spec["name"]):
                    selected.append((obj, card))
                else:
                    other.append((obj.Tag, [list(key), obj.DescriptorName, card]))
    obj, card = _one(selected, "force is absent or ambiguous in the declared solution and step")
    if obj.DescriptorName != "NodeIDTableForce" or any(obj.Tag == tag for tag, _ in other):
        raise RuntimeError("force must be an unshared NodeIDTableForce in the selected step")
    rows = _force_cards(card)
    if [row[0] for row in rows] != spec["grid_labels"]:
        raise RuntimeError("native force targets differ from the declared grid labels")
    builder = sim.Simulation.CreateBcBuilderForBc(obj)
    try:
        scale, unit = builder.PropertyTable.GetScalarWithDataPropertyValue("ScalingForce")
        if unit is None or unit.Name != "Newton":
            raise RuntimeError("force property units differ from the qualified native profile")
    finally:
        builder.Destroy()
    # Use a hash so even a large number of other BCs keeps a compact witness.
    guard = sha256(json.dumps(sorted((row for _, row in other), key=str),
                              separators=(",", ":")).encode()).hexdigest()
    return obj, {"force_rows": rows, "native_scale": scale, "other_bcs_sha256": guard,
                 "other_bc_memberships": len(other)}


def nodal_force(session, request, save_part):
    sim = open_owned(session, request["sim"], display=True)
    if not isinstance(sim, CAE.SimPart) or not sim.FemPart or Path(sim.FemPart.FullPath) != Path(request["fem"]):
        raise RuntimeError("opened simulation has an unexpected FEM dependency")
    spec = request["load"]
    obj, before = _force_snapshot(sim, spec)
    if request["action"] == "inspect-force":
        return {"scope": before, "dirty": bool(sim.IsModified), "dependent_fem_dirty": bool(sim.FemPart.IsModified)}
    if sim.IsModified or sim.FemPart.IsModified:
        raise RuntimeError("the supported solver-backed force edit requires clean loaded parts")
    if not isclose(before["native_scale"], spec["scale_before"], rel_tol=1e-12):
        raise RuntimeError("native force scale differs from the declared baseline")
    builder = sim.Simulation.CreateBcBuilderForBc(obj)
    try:
        table = builder.PropertyTable
        _, unit = table.GetScalarWithDataPropertyValue("ScalingForce")
        table.SetScalarWithDataPropertyValue("ScalingForce", float(spec["scale_after"]), unit)
        builder.CommitBc()
    finally:
        builder.Destroy()
    _, after = _force_snapshot(sim, spec)
    ratio = spec["scale_after"] / spec["scale_before"]
    if (not isclose(after["native_scale"], spec["scale_after"], rel_tol=1e-12)
            or before["other_bcs_sha256"] != after["other_bcs_sha256"]
            or not any(a[1] != b[1] for a, b in zip(before["force_rows"], after["force_rows"], strict=True))
            or any(a[2:] != b[2:] or not isclose(a[1] * ratio, b[1], rel_tol=1e-5, abs_tol=1e-6)
                   for a, b in zip(before["force_rows"], after["force_rows"], strict=True))):
        raise RuntimeError("native FORCE magnitude, direction or guard readback did not match")
    save_part(sim)
    return {"before": before, "after": after, "saved_dirty": bool(sim.IsModified)}


def _point(point):
    return [round(float(getattr(point, axis)), 8) for axis in ("X", "Y", "Z")]


def _selected(method, reader):
    try:
        return reader(method)
    finally:
        # Older selection methods have no explicit disposal member.
        if hasattr(method, "Dispose"):
            method.Dispose()


def _region(fem, cad, spec):
    owners = {body.JournalIdentifier: body for body in cad.Bodies}
    owner, guard = (owners.get(spec[key]) for key in ("cad_body", "guard_body"))
    if owner is None or guard is None or owner.Tag == guard.Tag:
        raise RuntimeError("target and guard CAD bodies must resolve separately in the owned CAD")
    source = _one([face for face in owner.GetFaces() if face.JournalIdentifier == spec["cad_face"]],
                  "CAD face does not resolve to the declared body")
    vertices = sorted({tuple(_point(point)) for edge in source.GetEdges() for point in edge.GetVertices()})
    if [list(vertex) for vertex in vertices] != spec["face_vertices_mm"]:
        raise RuntimeError("CAD face vertices differ from the predeclared physical region")
    polygon, guard_polygon = (fem.PolygonGeometryMgr.FindPolygonBodyFromSolidBody(body)
                              for body in (owner, guard))
    if polygon is None or guard_polygon is None or polygon.Tag == guard_polygon.Tag:
        raise RuntimeError("CAD bodies do not have independent polygon owners")
    selector = fem.SmartSelectionMgr
    faces = _selected(selector.CreateRelatedFaceMethod([polygon], False), lambda method: method.GetFaces())
    face = _one([item for item in faces
                 if [actual.Tag for actual in item.GetUgfaces()] == [source.Tag]],
                "expected one polygon face bound exclusively to the exact CAD face")
    return face, guard_polygon


def _mesh_snapshot(fem, cad, spec):
    face, guard = _region(fem, cad, spec)
    selector = fem.SmartSelectionMgr
    local = _selected(selector.CreateRelatedElemMethod([face], False), lambda method: method.GetElements())
    guard_elements = _selected(selector.CreateRelatedElemMethod([guard], False), lambda method: method.GetElements())
    nodes = _selected(selector.CreateNewRelatedNodeMethodFromFace(face, False, True),
                      lambda method: method.GetNodes())
    if len(local) + len(guard_elements) + len(nodes) > 150000:
        raise RuntimeError("regional witness exceeds the supported native population")
    labels = {node.Label for node in nodes}
    guard_rows = []
    edges = {}
    for element in local:
        vertices = element.GetNodes()
        if len(vertices) != 4 or any(vertex is None for vertex in vertices):
            raise RuntimeError("region qualification requires linear tetrahedra")
        for a, b in combinations((node for node in vertices if node.Label in labels), 2):
            edges[tuple(sorted((a.Label, b.Label)))] = dist(_point(a.Coordinates), _point(b.Coordinates))
    for element in guard_elements:
        guard_rows.append([element.Label, [[node.Label, _point(node.Coordinates)] for node in element.GetNodes()]])
    if not edges or not guard_rows or any(not isfinite(length) or length <= 0 for length in edges.values()):
        raise RuntimeError("target and guard populations must both contain finite native mesh evidence")
    controls = []
    collection = fem.BaseFEModel.MeshControls
    for obj in collection:
        builder = collection.CreateBuilder(obj)
        try:
            if builder.MainType == CAE.MeshControlBuilder.Types.FaceDensitySize:
                controls.append([obj.JournalIdentifier, builder.OverallSize.Value,
                                 [item.JournalIdentifier for item in builder.Selection.GetArray()]])
        finally:
            builder.Destroy()
    report = {"polygon_face": face.JournalIdentifier, "adjacent_elements": len(local),
              "edge_count": len(edges), "median_edge_mm": median(edges.values()),
              "guard_elements": len(guard_rows), "guard_sha256": sha256(
                  json.dumps(sorted(guard_rows), separators=(",", ":")).encode()).hexdigest(),
              "face_controls": sorted(controls)}
    return face, report


def regional_mesh(session, request, save_part):
    cad = open_owned(session, request["cad"], display=False)
    fem = open_owned(session, request["fem"], display=True)
    if (not isinstance(fem, CAE.FemPart) or Path(fem.FullPathForAssociatedCadPart) != Path(request["cad"])
            or cad.PartUnits != NXOpen.BasePart.Units.Millimeters
            or fem.PartUnits != NXOpen.BasePart.Units.Millimeters):
        raise RuntimeError("regional refinement requires a standalone millimeter CAD-associated FEM")
    spec = request["region"]
    dirty_on_open = bool(fem.IsModified)
    face, before = _mesh_snapshot(fem, cad, spec)
    if request["action"] == "inspect-region":
        return {"scope": before, "dirty_on_open": dirty_on_open, "dirty": bool(fem.IsModified),
                "dependent_cad_dirty": bool(cad.IsModified)}
    if any(face.JournalIdentifier in item[2] for item in before["face_controls"]):
        raise RuntimeError("face already has a physical size control")
    builder = fem.BaseFEModel.MeshControls.CreateBuilder(None)
    try:
        builder.MainType = CAE.MeshControlBuilder.Types.FaceDensitySize
        builder.OverallSize.RightHandSide = format(spec["size_mm"], ".12g")
        if not builder.Selection.Add([face]):
            raise RuntimeError("failed to bind the face to the size control")
        control = _one(builder.CommitDensities(), "expected one scoped face control")
        control_id = control.JournalIdentifier
    finally:
        builder.Destroy()
    fem.BaseFEModel.UpdateFemodel()
    _, after = _mesh_snapshot(fem, cad, spec)
    [entry] = [value for value in after["face_controls"] if value[0] == control_id]
    if (entry[2] != [after["polygon_face"]] or not isclose(entry[1], spec["size_mm"], rel_tol=1e-10)
            or after["guard_sha256"] != before["guard_sha256"]
            or after["edge_count"] <= before["edge_count"] or after["median_edge_mm"] >= before["median_edge_mm"]
            or [value for value in after["face_controls"] if value[0] != control_id] != before["face_controls"]):
        raise RuntimeError("regeneration did not improve the selected face while preserving its guard")
    save_part(fem)
    return {"before": before, "after": after, "control_id": control_id,
            "dirty_on_open": dirty_on_open, "saved_dirty": bool(fem.IsModified)}
