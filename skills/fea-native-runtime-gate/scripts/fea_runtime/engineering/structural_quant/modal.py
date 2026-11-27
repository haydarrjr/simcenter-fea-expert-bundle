# SPDX-License-Identifier: Apache-2.0
# Imported from FEA Expert Agent Plugin, fea_agent/structural_quant/modal.py
"""Pure source checks for supplied real SOL103 eigenpairs and beam references."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .numerics import NumericRangeError, positive_product_ratio

Matrix = tuple[tuple[float, ...], ...]
Vector = tuple[float, ...]

# A floating-point algorithm guard, not a project engineering tolerance.
_ROUND_OFF = 64 * math.ulp(1.0)


class ModalError(ValueError):
    """Unsafe, unrepresentable or unsupported modal source configuration."""


@dataclass(frozen=True, slots=True)
class Mode:
    mode_id: str
    eigenvalue_per_s2: float
    frequency_hz: float
    vector: Vector
    reference_mode_id: str
    reference_vector: Vector


@dataclass(frozen=True, slots=True)
class ModalPolicy:
    max_relative_residual: float
    max_mass_norm_error: float
    max_mass_orthogonality: float
    min_matching_mac: float
    max_frequency_rel_error: float
    near_degenerate_relative_gap: float
    max_beam_frequency_rel_error: float
    min_subspace_correlation: float
    provenance: str


@dataclass(frozen=True, slots=True)
class Beam:
    mode_id: str
    mode_number: int
    youngs_modulus_pa: float
    second_moment_m4: float
    density_kg_m3: float
    area_m2: float
    length_m: float
    physical_basis: str


@dataclass(frozen=True, slots=True)
class ModeMetrics:
    mode_id: str
    frequency_derived_hz: float
    relative_frequency_discrepancy: float
    relative_eigen_residual: float
    relative_mode_action_residual: float
    mass_norm: float
    matching_mass_mac: float
    findings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SubspaceMetrics:
    mode_ids: tuple[str, ...]
    supplied_rank: int
    reference_rank: int
    squared_principal_correlations: tuple[float, ...]
    mean_squared_correlation: float
    minimum_squared_correlation: float
    meets_declared_correlation: bool


@dataclass(frozen=True, slots=True)
class ModalAssessment:
    status: str
    findings: tuple[str, ...]
    modes: tuple[ModeMetrics, ...]
    mass_orthogonality: tuple[tuple[str, str, float], ...]
    beam_reference_hz: float | None
    beam_relative_discrepancy: float | None
    subspaces: tuple[SubspaceMetrics, ...]
    normalized_mass_correlation: tuple[tuple[str, str, float], ...]


def _finite(x: float) -> float:
    if not math.isfinite(x):
        raise ModalError("NONFINITE_MODAL_SOURCE_ARITHMETIC")
    return x


def _product(numerators: tuple[float, ...], denominators: tuple[float, ...] = ()) -> float:
    try:
        return positive_product_ratio(numerators, denominators)
    except NumericRangeError as error:
        raise ModalError(str(error)) from error


def _dot(a: Vector, b: Vector) -> float:
    products = tuple(x*y for x, y in zip(a, b, strict=True))
    if any(x != 0 and y != 0 and z == 0
           for x, y, z in zip(a, b, products, strict=True)):
        raise ModalError("UNREPRESENTABLE_MODAL_PRODUCT")
    return _finite(math.fsum(products))


def _mv(matrix: Matrix, v: Vector) -> Vector:
    return tuple(_dot(row, v) for row in matrix)


def _norm(v: Vector) -> float:
    return _finite(math.hypot(*v))


def _scaled_vector(v: Vector) -> tuple[Vector, float]:
    scale = max(abs(x) for x in v)
    if scale <= 0:
        raise ModalError("ZERO_MODE_VECTOR")
    scaled = tuple(x/scale for x in v)
    if any(x != 0 and y == 0 for x, y in zip(v, scaled, strict=True)):
        raise ModalError("UNREPRESENTABLE_MODAL_VECTOR_RANGE")
    return scaled, scale


def _matrix_check(matrix: Matrix, name: str) -> tuple[Matrix, float, Matrix]:
    """Require exactly symmetric source entries; factor their scaled matrix."""
    n = len(matrix)
    if n < 1 or n > 12 or any(len(row) != n for row in matrix):
        raise ModalError("CLOSED_1_TO_12_DOF_MATRIX_REQUIRED:" + name)
    if any(not math.isfinite(x) for row in matrix for x in row):
        raise ModalError("NONFINITE_MATRIX:" + name)
    scale = max(abs(x) for row in matrix for x in row)
    if scale <= 0:
        raise ModalError("MATRIX_NOT_POSITIVE_DEFINITE:" + name)
    normalized = tuple(tuple(x/scale for x in row) for row in matrix)
    for i in range(n):
        for j in range(n):
            # A global or absolute tolerance can hide an asymmetric soft
            # block beside stiff DOFs. This closed source contract does not
            # repair supplied operators, even within apparent roundoff.
            if matrix[i][j] != matrix[j][i]:
                raise ModalError("NONSYMMETRIC_MATRIX:" + name)
            if matrix[i][j] != 0 and normalized[i][j] == 0:
                raise ModalError("UNREPRESENTABLE_MATRIX_DYNAMIC_RANGE:" + name)
    triangular = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            subtraction = _dot(tuple(triangular[i][:j]), tuple(triangular[j][:j]))
            if i == j:
                remainder = normalized[i][i] - subtraction
                if not math.isfinite(remainder) or remainder <= 0:
                    raise ModalError("MATRIX_NOT_POSITIVE_DEFINITE:" + name)
                triangular[i][j] = math.sqrt(remainder)
            else:
                triangular[i][j] = _finite((normalized[i][j]-subtraction)
                                           / triangular[j][j])
    return normalized, scale, tuple(tuple(row) for row in triangular)


def _whiten(v: Vector, triangular: Matrix) -> tuple[Vector, float]:
    # M/scale=L L.T; L.T maps the M inner product into a Euclidean one.
    whitened = tuple(_dot(tuple(row[j] for row in triangular), v)
                     for j in range(len(v)))
    norm = _norm(whitened)
    if norm <= 0:
        raise ModalError("NONPOSITIVE_MODE_MASS_NORM")
    return tuple(x/norm for x in whitened), norm


def _residual_weights(k_scale: float, m_scale: float, eigenvalue: float) -> tuple[float, float]:
    # K scale and lambda*M scale share an exponent before multiplication.
    km, ke = math.frexp(k_scale)
    mm, me = math.frexp(m_scale)
    lm, le = math.frexp(eigenvalue)
    mlm, extra = math.frexp(mm*lm)
    mle = me+le+extra
    common = max(ke, mle)
    a, b = math.ldexp(km, ke-common), math.ldexp(mlm, mle-common)
    if a <= 0 or b <= 0:
        raise ModalError("UNREPRESENTABLE_EIGENPAIR_SCALE_RANGE")
    return a, b


def _clusters(modes: tuple[Mode, ...], gap_limit: float) -> tuple[tuple[int, ...], ...]:
    groups: list[set[int]] = []
    for i, mode in enumerate(modes):
        peers = {i}
        for j, other in enumerate(modes[:i]):
            if abs(mode.eigenvalue_per_s2-other.eigenvalue_per_s2)/max(
                mode.eigenvalue_per_s2, other.eigenvalue_per_s2
            ) <= gap_limit:
                peers.add(j)
        matches = [g for g in groups if g & peers]
        for g in matches:
            peers |= g
            groups.remove(g)
        groups.append(peers)
    return tuple(tuple(sorted(g)) for g in groups if len(g) > 1)


def _orthonormal(vectors: tuple[Vector, ...]) -> tuple[Vector, ...]:
    basis: list[Vector] = []
    for v in vectors:
        residual = v
        # Twice-reorthogonalized MGS on unit whitened vectors, n <= 12.
        for _ in range(2):
            for q in basis:
                projection = _dot(residual, q)
                residual = tuple(x-projection*y for x, y in zip(residual, q, strict=True))
        norm = _norm(residual)
        if norm > _ROUND_OFF*len(v):
            basis.append(tuple(x/norm for x in residual))
    return tuple(basis)


def _symmetric_eigenvalues(matrix: Matrix) -> tuple[float, ...]:
    """Bounded Jacobi diagonalization of the <=12 square correlation Gram matrix."""
    n = len(matrix)
    a = [list(row) for row in matrix]
    for _ in range(100*n*n):
        candidates = [(abs(a[i][j]), i, j) for i in range(n) for j in range(i+1, n)]
        if not candidates:
            break
        magnitude, p, q = max(candidates)
        if magnitude <= _ROUND_OFF*n:
            break
        theta = (a[q][q]-a[p][p])/(2*a[p][q])
        t = math.copysign(1.0, theta)/(abs(theta)+math.hypot(1.0, theta))
        c = 1/math.sqrt(1+t*t)
        s = t*c
        app, aqq, apq = a[p][p], a[q][q], a[p][q]
        a[p][p], a[q][q] = app-t*apq, aqq+t*apq
        a[p][q] = a[q][p] = 0.0
        for k in range(n):
            if k != p and k != q:
                akp, akq = a[k][p], a[k][q]
                a[k][p] = a[p][k] = c*akp-s*akq
                a[k][q] = a[q][k] = s*akp+c*akq
    else:
        raise ModalError("SUBSPACE_CORRELATION_ITERATION_LIMIT")
    values = tuple(sorted(a[i][i] for i in range(n)))
    if any(x < -_ROUND_OFF*n or x > 1+_ROUND_OFF*n for x in values):
        raise ModalError("INVALID_SUBSPACE_CORRELATION_RANGE")
    return tuple(min(1.0, max(0.0, x)) for x in values)


def _subspace(
    ids: tuple[str, ...], supplied: tuple[Vector, ...], reference: tuple[Vector, ...],
    minimum: float,
) -> SubspaceMetrics:
    q, r = _orthonormal(supplied), _orthonormal(reference)
    # Eigenvalues of C C.T are squared principal correlations. Pad missing
    # ranks with zero; an average must not conceal a missing direction.
    c = tuple(tuple(_dot(x, y) for y in r) for x in q)
    n = len(ids)
    gram = tuple(tuple(_dot(c[i], c[j]) if i < len(q) and j < len(q) else 0.0
                       for j in range(n)) for i in range(n))
    values = _symmetric_eigenvalues(gram)
    meets = len(q) == n and len(r) == n and values[0] >= minimum
    return SubspaceMetrics(ids, len(q), len(r), values, math.fsum(values)/n,
                           values[0], meets)


def cantilever_frequency(beam: Beam) -> float:
    """Uniform, linear, undamped Euler-Bernoulli fixed-free modes 1 or 2."""
    beta = {1: 1.875104068711961, 2: 4.694091132974174}
    vals = (beam.youngs_modulus_pa, beam.second_moment_m4,
            beam.density_kg_m3, beam.area_m2, beam.length_m)
    if (type(beam.mode_number) is not int or beam.mode_number not in beta
        or not beam.physical_basis.strip()
        or any(not math.isfinite(x) or x <= 0 for x in vals)):
        raise ModalError("UNSUPPORTED_CANTILEVER_REFERENCE")
    return _product((beta[beam.mode_number]**2, math.sqrt(beam.youngs_modulus_pa),
                     math.sqrt(beam.second_moment_m4)),
                    (2*math.pi, beam.length_m, beam.length_m,
                     math.sqrt(beam.density_kg_m3), math.sqrt(beam.area_m2)))


def assess_modes(stiffness_n_m: Matrix, mass_kg: Matrix, modes: tuple[Mode, ...],
                 policy: ModalPolicy, beam: Beam | None) -> ModalAssessment:
    k, ks, _ = _matrix_check(stiffness_n_m, "STIFFNESS")
    m, ms, chol = _matrix_check(mass_kg, "MASS")
    n = len(k)
    if len(m) != n:
        raise ModalError("MATRIX_DIMENSION_MISMATCH")
    if not modes or len(modes) > n:
        raise ModalError("INVALID_NUMBER_OF_MODES")
    if len({mode.mode_id for mode in modes}) != len(modes):
        raise ModalError("DUPLICATE_MODE_IDS")
    limits = (policy.max_relative_residual, policy.max_mass_norm_error,
              policy.max_mass_orthogonality, policy.min_matching_mac,
              policy.max_frequency_rel_error, policy.near_degenerate_relative_gap,
              policy.max_beam_frequency_rel_error, policy.min_subspace_correlation)
    if (not policy.provenance.strip() or any(not math.isfinite(x) or x < 0 for x in limits)
        or policy.min_matching_mac > 1 or policy.min_subspace_correlation > 1
        or policy.near_degenerate_relative_gap >= 1):
        raise ModalError("INVALID_MODAL_POLICY")
    for mode in modes:
        if (not mode.mode_id.strip() or not mode.reference_mode_id.strip()
            or len(mode.vector) != n or len(mode.reference_vector) != n
            or any(not math.isfinite(x) for x in (*mode.vector, *mode.reference_vector))
            or mode.eigenvalue_per_s2 <= 0 or mode.frequency_hz <= 0
            or not math.isfinite(mode.eigenvalue_per_s2)
            or not math.isfinite(mode.frequency_hz)):
            raise ModalError("UNSUPPORTED_MODE_VECTOR_OR_EIGENVALUE")
    clusters = _clusters(modes, policy.near_degenerate_relative_gap)
    clustered = {i for cluster in clusters for i in cluster}
    nk = _norm(tuple(x for row in k for x in row))
    nm = _norm(tuple(x for row in m for x in row))
    failures: list[str] = []
    assessments: list[ModeMetrics] = []
    whitened: list[Vector] = []
    references: list[Vector] = []
    for i, mode in enumerate(modes):
        issues: list[str] = []
        if mode.reference_mode_id != mode.mode_id:
            issues.append("MODE_REFERENCE_IDENTITY_CHANGED")
        v, vs = _scaled_vector(mode.vector)
        rv, _ = _scaled_vector(mode.reference_vector)
        w, wn = _whiten(v, chol)
        rw, _ = _whiten(rv, chol)
        whitened.append(w)
        references.append(rw)
        a, b = _residual_weights(ks, ms, mode.eigenvalue_per_s2)
        kv, mv = _mv(k, v), _mv(m, v)
        ka, ma = tuple(a*x for x in kv), tuple(b*x for x in mv)
        if any(x != 0 and y == 0 for x, y in zip(kv+mv, ka+ma, strict=True)):
            raise ModalError("UNREPRESENTABLE_MODAL_ACTION_RANGE")
        residual = tuple(x-y for x, y in zip(ka, ma, strict=True))
        relative_residual = _norm(residual)/((a*nk+b*nm)*_norm(v))
        action_scale = _norm(ka)+_norm(ma)
        if action_scale <= 0:
            raise ModalError("ZERO_MODE_ACTION_RESIDUAL_SCALE")
        action_residual = _norm(residual)/action_scale
        norm = _product((ms, vs, vs, wn, wn))
        frequency_derived = math.sqrt(mode.eigenvalue_per_s2)/(2*math.pi)
        relative_frequency = abs(frequency_derived-mode.frequency_hz)/max(
            frequency_derived, mode.frequency_hz)
        mac = min(1.0, _dot(w, rw)**2)
        if relative_residual > policy.max_relative_residual:
            issues.append("EIGENPAIR_EQUATION_RESIDUAL")
        if action_residual > policy.max_relative_residual:
            issues.append("EIGENPAIR_MODE_ACTION_RESIDUAL")
        if abs(norm-1) > policy.max_mass_norm_error:
            issues.append("MODE_NOT_UNIT_MASS_NORMALIZED")
        if relative_frequency > policy.max_frequency_rel_error:
            issues.append("EIGENVALUE_FREQUENCY_INCONSISTENT")
        if i not in clustered and mac < policy.min_matching_mac:
            issues.append("MODE_REFERENCE_MAC_TOO_LOW")
        assessments.append(ModeMetrics(mode.mode_id, frequency_derived,
                                       relative_frequency, relative_residual, action_residual,
                                       norm, mac, tuple(issues)))
        failures.extend(mode.mode_id+":"+issue for issue in issues)
    ortho: list[tuple[str, str, float]] = []
    correlations: list[tuple[str, str, float]] = []
    for i, first in enumerate(modes):
        for j in range(i+1, len(modes)):
            inner = abs(_dot(whitened[i], whitened[j]))
            raw_inner = _product((inner, math.sqrt(assessments[i].mass_norm),
                                  math.sqrt(assessments[j].mass_norm))) if inner else 0.0
            ortho.append((first.mode_id, modes[j].mode_id, raw_inner))
            correlations.append((first.mode_id, modes[j].mode_id, inner))
            if raw_inner > policy.max_mass_orthogonality:
                failures.append("M_ORTHOGONALITY_EXCEEDED:"
                                + first.mode_id+":"+modes[j].mode_id)
    subspaces: list[SubspaceMetrics] = []
    reviews: list[str] = []
    if len(modes) < n:
        # No eigensolver runs here: unseen members of a repeated eigenspace
        # cannot be ruled out from just the supplied eigenvalue pairs.
        reviews.append("INCOMPLETE_MODAL_BASIS_SPECTRUM_NOT_VERIFIED")
    for cluster in clusters:
        ids = tuple(modes[i].mode_id for i in cluster)
        summary = _subspace(ids, tuple(whitened[i] for i in cluster),
                            tuple(references[i] for i in cluster),
                            policy.min_subspace_correlation)
        subspaces.append(summary)
        reviews.append("NEAR_DEGENERATE_MODES_REQUIRE_SUBSPACE_REVIEW:"+":".join(ids))
        if not summary.meets_declared_correlation:
            failures.append("MODAL_SUBSPACE_CORRELATION_OR_RANK_FAILED:"+":".join(ids))
    beam_hz: float | None = None
    beam_error: float | None = None
    if beam is not None:
        beam_hz = cantilever_frequency(beam)
        matched = next((mode for mode in modes if mode.mode_id == beam.mode_id), None)
        if matched is None:
            failures.append("BEAM_REFERENCE_MODE_MISSING")
        else:
            beam_error = _finite(abs(beam_hz-matched.frequency_hz)/beam_hz)
            if beam_error > policy.max_beam_frequency_rel_error:
                failures.append("CANTILEVER_REFERENCE_DISAGREEMENT")
    status = "SOURCE_CHECKS_FAIL" if failures else (
        "INDETERMINATE" if reviews else "SOURCE_CHECKS_PASS")
    return ModalAssessment(status, tuple(failures+reviews), tuple(assessments),
                           tuple(ortho), beam_hz, beam_error, tuple(subspaces),
                           tuple(correlations))
