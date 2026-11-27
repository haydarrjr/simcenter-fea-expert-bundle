# SPDX-License-Identifier: Apache-2.0
# Imported from FEA Expert Agent Plugin, fea_agent/tensor_qoi/core.py
"""Pure real symmetric tensor arithmetic and location-safe source envelopes.

No result file, native model or solver is opened. Input provenance is declared,
not authenticated. Numerical agreement is not engineering acceptance.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..frames import FramedTensor


class TensorFieldError(ValueError):
    """Unsupported physical semantics or unrepresentable tensor arithmetic."""


@dataclass(frozen=True, slots=True)
class Location:
    owner: str
    entity_id: str
    location_kind: str
    location_key: str
    position_m: tuple[float, float, float]
    position_frame: str
    material_id: str
    section_side: str
    ply_id: str | None
    recovery: str
    averaging: str
    averaging_provenance: str
    parent_element_id: str | None = None


@dataclass(frozen=True, slots=True)
class ResultState:
    kind: str
    time_s: float | None
    frequency_hz: float | None
    mode_number: int | None


STATIC_STATE = ResultState("STATIC", None, None, None)


@dataclass(frozen=True, slots=True)
class Field:
    record_id: str
    kind: str
    source_model: str
    source_revision: str
    source_artifact: str
    case_id: str
    step_id: str
    state_id: str
    location: Location
    tensor: FramedTensor
    state: ResultState = STATIC_STATE


@dataclass(frozen=True, slots=True)
class Invariants:
    record_id: str
    kind: str
    frame: str
    transform_history: tuple[tuple[str, str, str], ...]
    symmetric_tensor_si: tuple[tuple[float, float, float], ...]
    principal_si: tuple[float, float, float]
    mean_si: float
    j2_si_squared: float
    von_mises_pa: float | None
    tresca_pa: float | None
    location: Location
    case_id: str
    step_id: str
    state_id: str
    source_artifact: str
    source_model: str
    source_revision: str
    state: ResultState
    dimension: str
    principal_span_si: float
    principal_resolution: str


@dataclass(frozen=True, slots=True)
class TensorAssessment:
    status: str
    records: tuple[Invariants, ...]
    governing_record_id: str | None
    governing_tensor: Invariants | None
    findings: tuple[str, ...]
    assessment_dimension: str


def _finite(x: float) -> float:
    if not math.isfinite(x):
        raise TensorFieldError("TENSOR_ARITHMETIC_RANGE")
    return x


def _product(a: float, b: float) -> float:
    value = _finite(a * b)
    if a != 0 and b != 0 and value == 0:
        raise TensorFieldError("TENSOR_ARITHMETIC_UNDERFLOW")
    return value


def _principal_symmetric3(
    tensor: tuple[tuple[float, float, float], ...],
) -> tuple[tuple[float, float, float], float, str]:
    """Return principal values and their span without hydrostatic cancellation.

    Remove Txx*I before scale-normalized Jacobi diagonalization. A hydrostatic
    offset must not control convergence or erase a represented small shear.
    The 64-rotation cap and 8-epsilon off-diagonal stopping threshold are
    numerical policies, not engineering tolerances. Repeated eigenvalues do
    not require acos of a nearly extremal determinant.
    """
    shift = tensor[0][0]
    centered = [[_finite(x - shift) if i == j else x
                 for j, x in enumerate(row)] for i, row in enumerate(tensor)]
    scale = max(abs(x) for row in centered for x in row)
    if scale == 0:
        return (shift, shift, shift), 0.0, "RESOLVED_TO_SOURCE_NUMERICAL_TOLERANCE"
    a = [[x / scale for x in row] for row in centered]
    for i in range(3):
        for j in range(3):
            if centered[i][j] != 0 and a[i][j] == 0:
                raise TensorFieldError("TENSOR_NORMALIZATION_UNDERFLOW")
    for _ in range(64):
        p, q = max(((0, 1), (0, 2), (1, 2)), key=lambda pair: abs(a[pair[0]][pair[1]]))
        off = a[p][q]
        if abs(off) <= 8 * math.ulp(1.0):
            break
        tau = (a[q][q] - a[p][p]) / (2 * off)
        tangent = math.copysign(1.0, tau) / (abs(tau) + math.hypot(1.0, tau))
        cosine = 1 / math.hypot(1.0, tangent)
        sine = tangent * cosine
        a[p][p] -= tangent * off
        a[q][q] += tangent * off
        a[p][q] = a[q][p] = 0.0
        for k in range(3):
            if k not in (p, q):
                old_p, old_q = a[k][p], a[k][q]
                a[k][p] = a[p][k] = cosine * old_p - sine * old_q
                a[k][q] = a[q][k] = sine * old_p + cosine * old_q
    else:
        raise TensorFieldError("PRINCIPAL_ITERATION_UNRESOLVED")
    offsets = sorted((_product(a[i][i], scale) for i in range(3)), reverse=True)
    span = _finite(offsets[0] - offsets[2])
    eig = [_finite(x + shift) for x in offsets]
    limit = min(64 * math.ulp(scale), 1e-12 * scale)
    resolution = ("ABSOLUTE_PRINCIPALS_ROUNDED_AT_HYDROSTATIC_SCALE"
                  if any(abs((value - shift) - offset) > limit
                         for value, offset in zip(eig, offsets, strict=True))
                  else "RESOLVED_TO_SOURCE_NUMERICAL_TOLERANCE")
    return (eig[0], eig[1], eig[2]), span, resolution


def _validate_location(loc: Location) -> None:
    """Closed v1 recovery representations, not claims about vendor support."""
    recovery_by_location = {
        "NODE": "element-nodal", "ELEMENT_CENTROID": "element-centroid",
        "INTEGRATION_POINT": "element-gauss", "CORNER": "element-corner",
        "SHELL_FACE": "shell-face",
    }
    if loc.ply_id is not None:
        raise TensorFieldError("LAMINATE_PLY_RECOVERY_UNSUPPORTED")
    if loc.location_kind not in recovery_by_location:
        raise TensorFieldError("UNSUPPORTED_RESULT_LOCATION")
    if loc.section_side not in {"NA", "TOP", "BOTTOM"}:
        raise TensorFieldError("UNSUPPORTED_SECTION_SIDE")
    if loc.location_kind == "SHELL_FACE":
        if loc.section_side not in {"TOP", "BOTTOM"}:
            raise TensorFieldError("SHELL_SECTION_SIDE_REQUIRED")
    elif loc.section_side != "NA":
        raise TensorFieldError("SECTION_SIDE_REQUIRES_SHELL_FACE_V1")
    if loc.recovery != recovery_by_location[loc.location_kind]:
        raise TensorFieldError("RECOVERY_LOCATION_COMBINATION_UNSUPPORTED_V1")
    if loc.location_kind == "NODE":
        if not loc.parent_element_id or not loc.parent_element_id.strip():
            raise TensorFieldError("UNAVERAGED_NODAL_PARENT_ELEMENT_REQUIRED")
    elif loc.parent_element_id is not None:
        raise TensorFieldError("PARENT_ELEMENT_ONLY_FOR_NODAL_RECOVERY_V1")
    if loc.averaging != "UNAVERAGED":
        raise TensorFieldError("AVERAGED_TENSOR_NOT_QUALIFIED")
    if not all(math.isfinite(x) for x in loc.position_m):
        raise TensorFieldError("NONFINITE_LOCATION")
    if not all((loc.owner, loc.entity_id, loc.location_key, loc.position_frame,
                loc.material_id, loc.recovery, loc.averaging_provenance)):
        raise TensorFieldError("INCOMPLETE_LOCATION_PROVENANCE")


def _validate_state(state: ResultState) -> None:
    if state.kind == "STATIC":
        valid = state.time_s is state.frequency_hz is state.mode_number is None
    elif state.kind == "REAL_TRANSIENT":
        valid = (state.time_s is not None and math.isfinite(state.time_s)
                 and state.time_s >= 0 and state.frequency_hz is None
                 and state.mode_number is None)
    elif state.kind == "REAL_MODAL":
        valid = (state.time_s is None and state.frequency_hz is not None
                 and math.isfinite(state.frequency_hz) and state.frequency_hz > 0
                 and type(state.mode_number) is int and state.mode_number > 0)
    else:
        valid = False
    if not valid:
        raise TensorFieldError("UNSUPPORTED_OR_INCONSISTENT_RESULT_STATE")


def evaluate_field(field: Field) -> Invariants:
    if field.kind not in {"stress", "strain"}:
        raise TensorFieldError("UNSUPPORTED_TENSOR_KIND")
    _validate_state(field.state)
    loc = field.location
    _validate_location(loc)
    t = field.tensor.components
    centered_scale = max(abs(_finite(x - t[0][0])) if i == j else abs(x)
                         for i, row in enumerate(t) for j, x in enumerate(row))
    # A large hydrostatic diagonal cannot excuse asymmetric small shears.
    asymmetry_limit = min(32 * math.ulp(centered_scale), 1e-12 * centered_scale)
    if any(abs(t[i][j] - t[j][i]) > asymmetry_limit for i in range(3) for j in range(i)):
        raise TensorFieldError("TENSOR_NOT_SYMMETRIC")
    # Exact symmetry needs no averaging. Otherwise only rotation roundoff is reconciled.
    xy = t[0][1] if t[0][1] == t[1][0] else t[0][1]/2 + t[1][0]/2
    xz = t[0][2] if t[0][2] == t[2][0] else t[0][2]/2 + t[2][0]/2
    yz = t[1][2] if t[1][2] == t[2][1] else t[1][2]/2 + t[2][1]/2
    t = ((t[0][0], xy, xz), (xy, t[1][1], yz), (xz, yz, t[2][2]))
    # Subtract the input diagonals before normalization, so adding a large
    # hydrostatic offset cannot alter a represented deviatoric difference.
    pairs = tuple(_finite(t[i][i] - t[j][j]) for i, j in ((0, 1), (1, 2), (2, 0)))
    shear = (t[0][1], t[0][2], t[1][2])
    scale = max(abs(x) for x in (*pairs, *shear))
    if scale == 0:
        j2 = equivalent = 0.0
    else:
        j2_n = (math.fsum((x / scale)**2 for x in pairs)/6
                + math.fsum((x / scale)**2 for x in shear))
        if j2_n == 0:
            raise TensorFieldError("DEVIATORIC_INVARIANT_UNDERFLOW")
        j2 = _product(_product(j2_n, scale), scale)
        equivalent = _product(math.sqrt(3*j2_n), scale)
    mean = _finite(math.fsum((t[0][0], (t[1][1]-t[0][0])/3, (t[2][2]-t[0][0])/3)))
    principal, principal_span, principal_resolution = _principal_symmetric3(t)
    vm = equivalent if field.kind == "stress" else None
    tresca = principal_span if field.kind == "stress" else None
    return Invariants(
        field.record_id, field.kind, field.tensor.frame,
        tuple((s.transform_id, s.from_frame, s.to_frame) for s in field.tensor.history),
        t, principal, mean, j2, vm, tresca, loc, field.case_id,
        field.step_id, field.state_id, field.source_artifact, field.source_model,
        field.source_revision, field.state, field.kind, principal_span, principal_resolution,
    )


def assess_tensor_fields(records: tuple[Field, ...], envelope_mode: str) -> TensorAssessment:
    if not records or len(records) > 256:
        raise TensorFieldError("INVALID_FIELD_RECORD_COUNT")
    if envelope_mode not in {"NONE", "MAX_VON_MISES"}:
        raise TensorFieldError("UNSUPPORTED_ENVELOPE_OPERATION")
    if len({item.record_id for item in records}) != len(records):
        raise TensorFieldError("DUPLICATE_FIELD_ID")
    if any(not all((item.record_id, item.source_artifact, item.case_id, item.step_id,
                    item.state_id, item.source_model, item.source_revision)) for item in records):
        raise TensorFieldError("INCOMPLETE_RESULT_PROVENANCE")
    base = records[0]
    for record in records:
        if (record.source_model, record.source_revision, record.kind) != (
                base.source_model, base.source_revision, base.kind):
            raise TensorFieldError("FIELD_IDENTITY_DRIFT")
        if record.location != base.location:
            raise TensorFieldError("MIXED_LOCATION_OWNER_MATERIAL_OR_SECTION")
        if record.tensor.frame != base.tensor.frame:
            raise TensorFieldError("UNMATCHED_TENSOR_FRAMES")
        if record.state.kind != base.state.kind:
            raise TensorFieldError("INCOMPATIBLE_RESULT_STATES")
    calculated = tuple(evaluate_field(record) for record in records)
    if envelope_mode == "NONE":
        if len(records) != 1:
            raise TensorFieldError("MULTIPLE_RECORDS_REQUIRE_EXPLICIT_ENVELOPE")
        governing = calculated[0]
    else:
        if base.kind != "stress" or len(records) < 2:
            raise TensorFieldError("VON_MISES_ENVELOPE_REQUIRES_MULTIPLE_REAL_STRESSES")
        if base.state.kind == "REAL_MODAL":
            raise TensorFieldError("ARBITRARY_MODAL_AMPLITUDE_ENVELOPE_UNSUPPORTED")
        if len({(r.case_id, r.step_id, r.state_id) for r in records}) != len(records):
            raise TensorFieldError("DUPLICATE_PHYSICAL_RESULT_STATE")
        governing = max(calculated, key=lambda item: item.von_mises_pa if item.von_mises_pa is not None else -1.0)
    return TensorAssessment("SOURCE_CHECKS_PASS", calculated, governing.record_id,
                            governing, (), base.kind)
