# SPDX-License-Identifier: Apache-2.0
# Imported from FEA Expert Agent Plugin, fea_agent/frames.py
"""Proper 3D component transformations with explicit frame provenance.

Matrices map components from ``from_frame`` to ``to_frame``: v_to = R v_from
and T_to = R T_from R^T. These are vector and rank-two tensor transformations;
there is no point translation or change of moment reference origin. Units stay
unchanged. This source-only algebra does not establish native frame identity.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


class FrameError(ValueError):
    """Invalid frame data, rotation or transformation provenance."""


Vector3 = tuple[float, float, float]
Matrix3 = tuple[Vector3, Vector3, Vector3]
_ROTATION_TOLERANCE = 1e-10


def _number(value: object) -> float:
    if type(value) not in (int, float):
        raise FrameError("INVALID_NUMBER: components must be int or float, excluding bool")
    try:
        result = float(value)
    except OverflowError as exc:
        raise FrameError("NONFINITE_NUMBER: component exceeds finite float range") from exc
    if not math.isfinite(result):
        raise FrameError("NONFINITE_NUMBER: components must be finite")
    return result


def _vector3(values: object) -> Vector3:
    if type(values) not in (tuple, list) or len(values) != 3:
        raise FrameError("INVALID_SHAPE: expected exactly three components")
    return tuple(_number(v) for v in values)


def _matrix3(values: object) -> Matrix3:
    if type(values) not in (tuple, list) or len(values) != 3:
        raise FrameError("INVALID_SHAPE: expected a 3 by 3 matrix")
    return tuple(_vector3(row) for row in values)


def _label(value: object) -> str:
    if (
        type(value) is not str
        or not value
        or len(value) > 128
        or value != value.strip()
        or any(ord(c) < 32 or ord(c) == 127 for c in value)
    ):
        raise FrameError("INVALID_ID: frame and transform IDs must be nonempty, bounded labels")
    return value


def _dot(left: Vector3, right: Vector3) -> float:
    try:
        result = math.fsum(a * b for a, b in zip(left, right, strict=True))
    except (OverflowError, ValueError) as exc:
        raise FrameError("NONFINITE_RESULT: transformation overflowed") from exc
    if not math.isfinite(result):
        raise FrameError("NONFINITE_RESULT: transformation overflowed")
    return result


def _determinant(matrix: Matrix3) -> float:
    a, b, c = matrix
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def validate_rotation(matrix: object) -> Matrix3:
    """Return immutable R only for orthonormal, right-handed 3D rotations.

    Absolute residual tolerance is 1e-10 for row/column dot products and
    determinant +1. The function never repairs, rescales or orthogonalizes input.
    """
    rotation = _matrix3(matrix)
    columns = tuple(tuple(rotation[i][j] for i in range(3)) for j in range(3))
    for axes in (rotation, columns):
        for i in range(3):
            for j in range(i, 3):
                expected = 1.0 if i == j else 0.0
                if abs(_dot(axes[i], axes[j]) - expected) > _ROTATION_TOLERANCE:
                    raise FrameError("ROTATION_NOT_ORTHONORMAL: axes must be orthonormal")
    if abs(_determinant(rotation) - 1.0) > _ROTATION_TOLERANCE:
        raise FrameError("ROTATION_NOT_PROPER: determinant must equal +1")
    return rotation


@dataclass(frozen=True)
class TransformStamp:
    """One explicit component transformation, identified by a unique event ID."""

    transform_id: str
    from_frame: str
    to_frame: str

    def __post_init__(self) -> None:
        for value in (self.transform_id, self.from_frame, self.to_frame):
            _label(value)
        if self.from_frame == self.to_frame:
            raise FrameError("SAME_FRAME: a component transformation must change frames")


def _history(history: object, current_frame: str) -> tuple[TransformStamp, ...]:
    if type(history) not in (tuple, list) or any(type(s) is not TransformStamp for s in history):
        raise FrameError("INVALID_HISTORY: expected TransformStamp records")
    stamps = tuple(history)
    if len({s.transform_id for s in stamps}) != len(stamps):
        raise FrameError("TRANSFORM_ALREADY_APPLIED: duplicate transformation event")
    for previous, current in zip(stamps, stamps[1:], strict=False):
        if previous.to_frame != current.from_frame:
            raise FrameError("BROKEN_FRAME_HISTORY: transformation chain is discontinuous")
    if stamps and stamps[-1].to_frame != current_frame:
        raise FrameError("FRAME_MISMATCH: history does not end at the record frame")
    return stamps


@dataclass(frozen=True)
class FramedVector:
    components: Vector3
    frame: str
    history: tuple[TransformStamp, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "components", _vector3(self.components))
        _label(self.frame)
        object.__setattr__(self, "history", _history(self.history, self.frame))


@dataclass(frozen=True)
class FramedTensor:
    components: Matrix3
    frame: str
    history: tuple[TransformStamp, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "components", _matrix3(self.components))
        _label(self.frame)
        object.__setattr__(self, "history", _history(self.history, self.frame))


def _next_stamp(
    record: FramedVector | FramedTensor, from_frame: str, to_frame: str, transform_id: str
) -> TransformStamp:
    stamp = TransformStamp(transform_id, from_frame, to_frame)
    if record.frame != from_frame:
        raise FrameError("FRAME_MISMATCH: record is not expressed in from_frame")
    if any(s.transform_id == transform_id for s in record.history):
        raise FrameError("TRANSFORM_ALREADY_APPLIED: this event already transformed the record")
    return stamp


def transform_vector(
    record: FramedVector,
    matrix: object,
    *,
    from_frame: str,
    to_frame: str,
    transform_id: str,
) -> FramedVector:
    """Apply v_to = R v_from, rejecting stale frames and duplicate event IDs."""
    if type(record) is not FramedVector:
        raise FrameError("UNFRAMED_VALUE: a FramedVector is required")
    stamp = _next_stamp(record, from_frame, to_frame, transform_id)
    rotation = validate_rotation(matrix)
    values = tuple(_dot(row, record.components) for row in rotation)
    return FramedVector(values, to_frame, record.history + (stamp,))


def transform_tensor(
    record: FramedTensor,
    matrix: object,
    *,
    from_frame: str,
    to_frame: str,
    transform_id: str,
) -> FramedTensor:
    """Apply T_to = R T_from R^T without changing units or tensor rank."""
    if type(record) is not FramedTensor:
        raise FrameError("UNFRAMED_VALUE: a FramedTensor is required")
    stamp = _next_stamp(record, from_frame, to_frame, transform_id)
    rotation = validate_rotation(matrix)
    columns = tuple(tuple(record.components[i][j] for i in range(3)) for j in range(3))
    intermediate = tuple(tuple(_dot(row, col) for col in columns) for row in rotation)
    values = tuple(tuple(_dot(row, r_row) for r_row in rotation) for row in intermediate)
    return FramedTensor(values, to_frame, record.history + (stamp,))
