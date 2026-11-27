# SPDX-License-Identifier: Apache-2.0
# Imported from FEA Expert Agent Plugin, fea_agent/mesh_vvuq/core.py
"""Pure stdlib geometric and refinement calculations for bounded source-only FEA.

Supported mesh cells: planar-oriented TRI3 and linear TET4. All coordinates
are SI metres. This module cannot authenticate an FEM, solver, or validation.
"""
from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass

Vec3 = tuple[float, float, float]

# Computational bounds, independent of caller-declared engineering tolerances.
# Dense coordinate clouds can have O(N**2) real output even with spatial search.
MAX_COINCIDENCE_CANDIDATES = 1_000_000
MAX_COINCIDENCE_PAIRS = 20_000


@dataclass(frozen=True, slots=True)
class Node:
    node_id: str
    xyz_m: Vec3
    owner: str


@dataclass(frozen=True, slots=True)
class Element:
    element_id: str
    family: str
    node_ids: tuple[str, ...]
    owner: str
    property_id: str
    reference_normal: Vec3 | None = None


@dataclass(frozen=True, slots=True)
class MeshPolicy:
    profile_id: str
    provenance: str
    min_area_m2: float
    min_volume_m3: float
    max_aspect_ratio: float
    min_normal_alignment: float
    coincidence_tolerance_m: float
    expected_components: int


@dataclass(frozen=True, slots=True)
class CellMetrics:
    element_id: str
    family: str
    edge_lengths_m: tuple[float, ...] | None
    area_m2: float | None
    signed_reference_area_m2: float | None
    normal: Vec3 | None
    signed_det_j_m3: float | None
    signed_volume_m3: float | None
    absolute_volume_m3: float | None
    aspect_ratio_longest_edge_over_shortest_altitude: float | None
    findings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MeshAssessment:
    status: str
    cells: tuple[CellMetrics, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    connected_components: int
    orphan_nodes: tuple[str, ...]
    coincident_node_pairs: tuple[tuple[str, str], ...]
    evaluated_cells: int
    coincidence_scan_complete: bool
    coincidence_candidate_checks: int
    coincidence_candidate_limit: int
    coincidence_pair_limit: int


@dataclass(frozen=True, slots=True)
class _CoincidenceScan:
    pairs: tuple[tuple[str, str], ...]
    candidate_checks: int
    incomplete_reason: str | None


def _coincidence_candidates(
    nodes: tuple[Node, ...], tolerance: float,
) -> Iterator[tuple[Node, Node]]:
    """Deterministic spatial candidates, including floating-point boundaries.

    Exact-coordinate buckets handle zero tolerance. Positive-tolerance cells
    have exact width 2*tolerance: the padding preserves pairs whose distance
    rounds down to the inclusive tolerance at a cell boundary. Integer-ratio
    division avoids both rounded cell indices and x/tolerance overflow for
    finite coordinates and subnormal tolerances. Final acceptance is always
    math.dist <= tolerance, not the cell membership.
    """
    ordered = sorted(nodes, key=lambda node: node.node_id)
    if tolerance == 0:
        exact: dict[Vec3, list[Node]] = {}
        for node in ordered:
            for previous in exact.get(node.xyz_m, ()):
                yield previous, node
            exact.setdefault(node.xyz_m, []).append(node)
        return

    tolerance_num, tolerance_den = tolerance.as_integer_ratio()

    def cell_coordinate(value: float) -> int:
        numerator, denominator = value.as_integer_ratio()
        return numerator * tolerance_den // (denominator * tolerance_num * 2)

    cells: dict[tuple[int, int, int], list[Node]] = {}
    for node in ordered:
        ix, iy, iz = (cell_coordinate(value) for value in node.xyz_m)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for previous in cells.get((ix + dx, iy + dy, iz + dz), ()):
                        yield previous, node
        cells.setdefault((ix, iy, iz), []).append(node)


def _coincident_nodes(nodes: tuple[Node, ...], tolerance: float) -> _CoincidenceScan:
    pairs: list[tuple[str, str]] = []
    checks = 0
    incomplete_reason = None
    for first, second in _coincidence_candidates(nodes, tolerance):
        if checks >= MAX_COINCIDENCE_CANDIDATES:
            incomplete_reason = "COINCIDENCE_CANDIDATE_LIMIT_REACHED"
            break
        checks += 1
        if math.dist(first.xyz_m, second.xyz_m) <= tolerance:
            if len(pairs) >= MAX_COINCIDENCE_PAIRS:
                incomplete_reason = "COINCIDENCE_PAIR_LIMIT_REACHED"
                break
            pairs.append((first.node_id, second.node_id))
    return _CoincidenceScan(tuple(sorted(pairs)), checks, incomplete_reason)


def _subtract(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def _dot(a: Vec3, b: Vec3) -> float:
    return math.fsum(x*y for x, y in zip(a, b, strict=True))


def _length(a: Vec3) -> float:
    return math.hypot(*a)


def _checked(x: float) -> float:
    if not math.isfinite(x):
        raise ValueError("UNREPRESENTABLE_MESH_GEOMETRY")
    return x


def _tri(a: Vec3, b: Vec3, c: Vec3) -> tuple[float, Vec3]:
    v = _cross(_subtract(b, a), _subtract(c, a))
    size = _checked(0.5 * _length(v))
    return size, v


def _tet(a: Vec3, b: Vec3, c: Vec3, d: Vec3) -> float:
    return _checked(_dot(_subtract(b, a), _cross(_subtract(c, a), _subtract(d, a))))


def _shape(points: tuple[Vec3, ...], family: str, volume: float,
           area: float) -> tuple[tuple[float, ...], float | None]:
    lengths = tuple(_checked(math.dist(points[i], points[j]))
                    for i in range(len(points)) for j in range(i + 1, len(points)))
    if min(lengths) <= 0 or not math.isfinite(max(lengths)):
        return lengths, None
    if family == "TRI3":
        altitude = 2 * area / max(lengths)
    else:
        a, b, c, d = points
        face_areas = (_tri(a, b, c)[0], _tri(a, b, d)[0],
                      _tri(a, c, d)[0], _tri(b, c, d)[0])
        altitude = 3 * abs(volume) / max(face_areas) if max(face_areas) > 0 else 0.0
    return lengths, (_checked(max(lengths) / altitude) if altitude > 0 else None)


def _component_count(elements: tuple[Element, ...], present: set[str]) -> int:
    parent: dict[str, str] = {}

    def root(key: str) -> str:
        parent.setdefault(key, key)
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    for element in elements:
        ids = [item for item in element.node_ids if item in present]
        if not ids:
            continue
        anchor = root(ids[0])
        for item in ids[1:]:
            parent[root(item)] = anchor
    return len({root(node_id) for node_id in parent})


def assess_mesh(nodes: tuple[Node, ...], elements: tuple[Element, ...],
                policy: MeshPolicy, property_bindings: frozenset[tuple[str, str]],
                intentional_duplicates: frozenset[tuple[str, str]]) -> MeshAssessment:
    """Compute geometry and topology, never infer solver/vendor acceptance."""
    if not nodes or not elements or policy.expected_components < 1:
        raise ValueError("EMPTY_OR_INVALID_MESH")
    if (not policy.provenance.strip() or not policy.profile_id.strip()
        or policy.min_area_m2 < 0 or policy.min_volume_m3 < 0
        or policy.max_aspect_ratio <= 0 or not 0 <= policy.min_normal_alignment <= 1
        or policy.coincidence_tolerance_m < 0):
        raise ValueError("INVALID_MESH_POLICY")
    all_scalars = (policy.min_area_m2, policy.min_volume_m3,
                   policy.max_aspect_ratio, policy.min_normal_alignment,
                   policy.coincidence_tolerance_m)
    if not all(math.isfinite(x) for x in all_scalars):
        raise ValueError("NONFINITE_MESH_POLICY")
    by_id = {node.node_id: node for node in nodes}
    if len(by_id) != len(nodes) or any(not node.node_id or not node.owner for node in nodes):
        raise ValueError("INVALID_NODE_IDENTITIES")
    if any(not all(math.isfinite(x) for x in n.xyz_m) for n in nodes):
        raise ValueError("INVALID_NODE_COORDINATES")
    ids = [e.element_id for e in elements]
    if len(set(ids)) != len(ids) or any(not eid for eid in ids):
        raise ValueError("DUPLICATE_ELEMENT_IDENTITIES")
    allowed = {tuple(sorted(pair)) for pair in intentional_duplicates}
    if any(len(pair) != 2 or pair[0] == pair[1] or any(i not in ids for i in pair)
           for pair in allowed):
        raise ValueError("INVALID_INTENTIONAL_DUPLICATES")

    blockers: list[str] = []
    warnings: list[str] = []
    used: set[str] = set()
    seen: dict[tuple[str, tuple[str, ...]], str] = {}
    cells: list[CellMetrics] = []
    families = {e.family for e in elements}
    if len(families) != 1:
        blockers.append("MIXED_ELEMENT_FAMILIES_UNSUPPORTED")
    for element in elements:
        issues: list[str] = []
        if element.family not in {"TRI3", "TET4"}:
            issues.append("UNSUPPORTED_ELEMENT_FAMILY")
        if len(element.node_ids) != {"TRI3": 3, "TET4": 4}.get(element.family, -1):
            issues.append("INVALID_CONNECTIVITY_ARITY")
        if len(set(element.node_ids)) != len(element.node_ids):
            issues.append("REPEATED_NODE_INDEX")
        if any(item not in by_id for item in element.node_ids):
            issues.append("MISSING_NODE")
        if (element.owner, element.property_id) not in property_bindings:
            issues.append("PROPERTY_UNBOUND")
        if any(by_id[item].owner != element.owner
               for item in element.node_ids if item in by_id):
            issues.append("CROSS_OWNER_CONNECTIVITY")
        key = (element.family, tuple(sorted(element.node_ids)))
        if key in seen:
            pair = tuple(sorted((element.element_id, seen[key])))
            if pair in allowed:
                warnings.append("INTENTIONAL_TOPOLOGY_DUPLICATE:" + ":".join(pair))
            else:
                issues.append("DUPLICATE_TOPOLOGY")
        else:
            seen[key] = element.element_id
        used.update(item for item in element.node_ids if item in by_id)

        lengths: tuple[float, ...] | None = None
        area: float | None = None
        signed_area: float | None = None
        normal: Vec3 | None = None
        det: float | None = None
        vol: float | None = None
        aspect: float | None = None
        if not any(issue in issues for issue in
                   ("UNSUPPORTED_ELEMENT_FAMILY", "INVALID_CONNECTIVITY_ARITY",
                    "REPEATED_NODE_INDEX", "MISSING_NODE")):
            pts = tuple(by_id[item].xyz_m for item in element.node_ids)
            if element.family == "TRI3":
                area, area_vector = _tri(pts[0], pts[1], pts[2])
                lengths, aspect = _shape(pts, element.family, 0, area)
                if area <= policy.min_area_m2 or area == 0:
                    issues.append("DEGENERATE_OR_TOO_SMALL_TRI3")
                else:
                    normal = (area_vector[0]/(2*area), area_vector[1]/(2*area),
                              area_vector[2]/(2*area))
                    ref = element.reference_normal
                    if ref is None or _length(ref) == 0:
                        issues.append("REFERENCE_NORMAL_REQUIRED")
                    else:
                        projection = _dot(area_vector, ref) / _length(ref)
                        signed_area = 0.5 * _checked(projection)
                        alignment = projection / (2 * area)
                        if alignment <= 0:
                            issues.append("REVERSED_TRI3_ORIENTATION")
                        elif alignment < policy.min_normal_alignment:
                            issues.append("TRI3_REFERENCE_NORMAL_MISALIGNMENT")
            else:
                det = _tet(pts[0], pts[1], pts[2], pts[3])
                vol = det / 6
                lengths, aspect = _shape(pts, element.family, vol, 0)
                if abs(vol) <= policy.min_volume_m3 or vol == 0:
                    issues.append("DEGENERATE_OR_TOO_SMALL_TET4")
                if det < 0:
                    issues.append("INVERTED_TET4")
                if element.reference_normal is not None:
                    issues.append("TET4_REFERENCE_NORMAL_NOT_APPLICABLE")
            if aspect is None or aspect > policy.max_aspect_ratio:
                issues.append("ASPECT_RATIO_POLICY_FAILURE")
        if issues:
            blockers.extend(element.element_id + ":" + issue for issue in issues)
        cells.append(CellMetrics(element.element_id, element.family, lengths, area,
                                 signed_area, normal, det, vol,
                                 abs(vol) if vol is not None else None,
                                 aspect, tuple(issues)))

    orphans = tuple(sorted(set(by_id) - used))
    if orphans:
        blockers.append("ORPHAN_NODES:" + ",".join(orphans))
    coincidence = _coincident_nodes(nodes, policy.coincidence_tolerance_m)
    if coincidence.pairs:
        blockers.extend("COINCIDENT_NODES:" + ":".join(pair) for pair in coincidence.pairs)
    if coincidence.incomplete_reason is not None:
        warnings.append(coincidence.incomplete_reason)
    actual_components = _component_count(elements, set(by_id))
    if actual_components != policy.expected_components:
        blockers.append("CONNECTED_COMPONENT_COUNT_MISMATCH")
    status = ("SOURCE_CHECKS_FAIL" if blockers else
              "INDETERMINATE" if coincidence.incomplete_reason else "SOURCE_CHECKS_PASS")
    return MeshAssessment(status,
                          tuple(cells), tuple(blockers), tuple(warnings),
                          actual_components, orphans, coincidence.pairs, len(cells),
                          coincidence.incomplete_reason is None,
                          coincidence.candidate_checks,
                          MAX_COINCIDENCE_CANDIDATES, MAX_COINCIDENCE_PAIRS)


@dataclass(frozen=True, slots=True)
class StudyIdentity:
    solver_family: str
    solver_release: str
    model_id: str
    material_id: str
    bc_id: str
    loadcase_id: str
    frame_id: str
    location_id: str
    recovery: str
    averaging: str
    quantity: str
    component: str
    qoi_id: str
    h_definition: str
    dimension: str


@dataclass(frozen=True, slots=True)
class Level:
    mesh_id: str
    mesh_revision: str
    identity: StudyIdentity
    h_m: float
    qoi_si: float
    governing_location_id: str


@dataclass(frozen=True, slots=True)
class ConvergencePolicy:
    absolute_tolerance_si: float
    relative_tolerance: float
    safety_factor: float
    max_order_spread: float
    asymptotic_basis: str
    singularity_review: str
    provenance: str


@dataclass(frozen=True, slots=True)
class ConvergenceAssessment:
    status: str
    findings: tuple[str, ...]
    observed_orders: tuple[float, ...]
    refinement_ratio: float | None
    richardson_limit_si: float | None
    estimated_fine_error_si: float | None
    conservative_gci_error_si: float | None
    permitted_error_si: float | None
    fine_value_si: float | None
    quantity_dimension: str


def assess_convergence(levels: tuple[Level, ...], policy: ConvergencePolicy,
                       expected_identity: StudyIdentity | None = None) -> ConvergenceAssessment:
    """Constant-r, monotone, nonzero-difference Richardson source study.

    p_i = ln(|(q_i-q_(i+1))/(q_(i+1)-q_(i+2))|)/ln(r);
    q_inf = q_f + (q_f-q_m)/(r**p-1);
    GCI_absolute = safety_factor * |q_inf-q_f|.  Three levels do NOT prove
    asymptotic behavior or physical validation.
    """
    if len(levels) < 3:
        raise ValueError("THREE_REFINEMENT_LEVELS_REQUIRED")
    values = (policy.absolute_tolerance_si, policy.relative_tolerance,
              policy.safety_factor, policy.max_order_spread)
    if (not all(math.isfinite(x) for x in values)
        or policy.absolute_tolerance_si < 0 or policy.relative_tolerance < 0
        or policy.safety_factor <= 1 or policy.max_order_spread < 0
        or not policy.provenance.strip()):
        raise ValueError("INVALID_CONVERGENCE_POLICY")
    for item in levels:
        if (not item.mesh_id or not item.mesh_revision
            or item.h_m <= 0 or not math.isfinite(item.h_m)
            or not math.isfinite(item.qoi_si)):
            raise ValueError("INVALID_REFINEMENT_LEVEL")
    findings: list[str] = []
    identity = levels[0].identity
    if expected_identity is not None and any(
        level.identity != expected_identity for level in levels
    ):
        findings.append("TOP_LEVEL_STUDY_IDENTITY_MISMATCH")
    if any(level.identity != identity for level in levels[1:]):
        findings.append("PHYSICAL_IDENTITY_DRIFT")
    if len({level.mesh_id for level in levels}) != len(levels):
        findings.append("DUPLICATE_MESH_ID")
    if any(level.governing_location_id != identity.location_id for level in levels):
        findings.append("GOVERNING_LOCATION_CHANGED")
    if policy.singularity_review != "CLEARED":
        findings.append("SINGULARITY_NOT_CLEARED")
    if not policy.asymptotic_basis.strip():
        findings.append("ASYMPTOTIC_EVIDENCE_MISSING")
    ratios = [levels[i].h_m / levels[i+1].h_m for i in range(len(levels)-1)]
    if any(r <= 1 or not math.isfinite(r) for r in ratios):
        findings.append("REFINEMENT_NOT_STRICTLY_DECREASING")
    if all(r > 1 and math.isfinite(r) for r in ratios) and any(
        not math.isclose(r, ratios[0], rel_tol=1e-10, abs_tol=0)
        for r in ratios[1:]
    ):
        findings.append("NONCONSTANT_REFINEMENT_RATIO_UNSUPPORTED")
    q = [level.qoi_si for level in levels]
    delta = [q[i]-q[i+1] for i in range(len(q)-1)]
    signal = max(abs(x) for x in q)
    floor = 64 * math.ulp(signal) if signal else 0.0
    if any(d == 0 or abs(d) <= floor for d in delta):
        findings.append("ZERO_OR_UNRESOLVED_DIFFERENCES")
    if any((delta[i] > 0) != (delta[i+1] > 0) for i in range(len(delta)-1)):
        findings.append("NONMONOTONIC_QOI")
    orders: list[float] = []
    if not findings:
        r = ratios[0]
        for i in range(len(delta)-1):
            order = (math.log(abs(delta[i])) - math.log(abs(delta[i+1]))) / math.log(r)
            if not math.isfinite(order) or order <= 0:
                findings.append("NONPOSITIVE_OR_UNDEFINED_ORDER")
                break
            orders.append(order)
        if orders and max(orders)-min(orders) > policy.max_order_spread:
            findings.append("OBSERVED_ORDER_UNSTABLE")
    if findings:
        return ConvergenceAssessment("INDETERMINATE", tuple(findings),
                                     tuple(orders), None, None, None, None, None,
                                     None if "TOP_LEVEL_STUDY_IDENTITY_MISMATCH" in findings else q[-1],
                                     expected_identity.dimension if expected_identity is not None else identity.dimension)
    p = orders[-1]
    factor = math.expm1(p * math.log(ratios[0]))
    if not math.isfinite(factor) or factor <= 0:
        findings.append("RICHARDSON_DENOMINATOR_UNRESOLVED")
        return ConvergenceAssessment("INDETERMINATE", tuple(findings),
                                     tuple(orders), ratios[0], None, None,
                                     None, None, q[-1], identity.dimension)
    correction = (q[-1] - q[-2]) / factor
    extrapolated = q[-1] + correction
    error = abs(correction)
    gci = policy.safety_factor * error
    allowed = policy.absolute_tolerance_si + policy.relative_tolerance*abs(extrapolated)
    if not all(math.isfinite(x) for x in (extrapolated, error, gci, allowed)):
        raise ValueError("UNREPRESENTABLE_CONVERGENCE_RESULT")
    passed = gci <= allowed
    if not passed:
        findings.append("FINE_GRID_GCI_EXCEEDS_BUDGET")
    return ConvergenceAssessment("SOURCE_CHECKS_PASS" if passed else "SOURCE_CHECKS_FAIL",
                                 tuple(findings), tuple(orders), ratios[0], extrapolated,
                                 error, gci, allowed, q[-1], identity.dimension)
