# SPDX-License-Identifier: Apache-2.0
# Imported from FEA Expert Agent Plugin, fea_agent/units.py
"""Explicit scalar unit conversion for source-only engineering validation.

The dimension is mandatory. Absolute temperatures and temperature differences
are different dimensions; cyclic frequency and angular speed are different
dimensions. Spectral densities are one-sided values per Hz, with an explicit
underlying quantity. These functions neither inspect nor mutate a native model.
"""

from __future__ import annotations

import math


class UnitError(ValueError):
    """A quantity is nonfinite, dimensionally ambiguous, or unsupported."""


# Each entry maps to SI using value * scale + offset. Offsets are reserved for
# absolute temperature. Unit spellings are deliberately closed and case-sensitive.
_UNITS: dict[str, dict[str, tuple[float, float]]] = {
    "length": {
        "m": (1.0, 0.0),
        "mm": (0.001, 0.0),
        "um": (1e-6, 0.0),
        "in": (0.0254, 0.0),
    },
    "force": {"N": (1.0, 0.0), "kN": (1000.0, 0.0)},
    "moment": {
        "N*m": (1.0, 0.0),
        "N*mm": (0.001, 0.0),
        "kN*m": (1000.0, 0.0),
    },
    "mass": {"kg": (1.0, 0.0), "g": (0.001, 0.0)},
    "time": {"s": (1.0, 0.0), "sec": (1.0, 0.0), "ms": (0.001, 0.0)},
    "angle": {"rad": (1.0, 0.0), "deg": (math.pi / 180.0, 0.0)},
    "absolute_temperature": {"K": (1.0, 0.0), "degC": (1.0, 273.15)},
    "temperature_difference": {"K": (1.0, 0.0), "degC": (1.0, 0.0)},
    "stress": {"Pa": (1.0, 0.0), "MPa": (1_000_000.0, 0.0)},
    "area": {"m^2": (1.0, 0.0), "mm^2": (1e-6, 0.0), "in^2": (0.0254**2, 0.0)},
    "volume": {"m^3": (1.0, 0.0), "mm^3": (1e-9, 0.0), "in^3": (0.0254**3, 0.0)},
    "second_moment": {"m^4": (1.0, 0.0), "mm^4": (1e-12, 0.0), "in^4": (0.0254**4, 0.0)},
    "strain": {"1": (1.0, 0.0)},
    "energy": {"J": (1.0, 0.0), "N*m": (1.0, 0.0), "N*mm": (0.001, 0.0)},
    "axial_stiffness": {"N/m": (1.0, 0.0), "N/mm": (1000.0, 0.0)},
    "rotational_stiffness": {"N*m/rad": (1.0, 0.0), "N*mm/rad": (0.001, 0.0)},
    "line_load": {"N/m": (1.0, 0.0), "N/mm": (1000.0, 0.0)},
    "density": {"kg/m^3": (1.0, 0.0), "kg/mm^3": (1e9, 0.0), "g/cm^3": (1000.0, 0.0)},
    "frequency": {"Hz": (1.0, 0.0), "rpm": (1.0 / 60.0, 0.0)},
    "eigenvalue": {"1/s^2": (1.0, 0.0), "1/ms^2": (1_000_000.0, 0.0)},
    "angular_speed": {
        "rad/s": (1.0, 0.0),
        "deg/s": (math.pi / 180.0, 0.0),
        "rpm": (2.0 * math.pi / 60.0, 0.0),
    },
    "acceleration": {
        "m/s^2": (1.0, 0.0),
        "mm/s^2": (0.001, 0.0),
        "in/s^2": (0.0254, 0.0),
    },
    "displacement_psd": {"m^2/Hz": (1.0, 0.0), "mm^2/Hz": (1e-6, 0.0)},
    "force_psd": {"N^2/Hz": (1.0, 0.0), "kN^2/Hz": (1e6, 0.0)},
    "stress_psd": {"Pa^2/Hz": (1.0, 0.0), "MPa^2/Hz": (1e12, 0.0)},
    "acceleration_psd": {
        "(m/s^2)^2/Hz": (1.0, 0.0),
        "(mm/s^2)^2/Hz": (1e-6, 0.0),
        "(in/s^2)^2/Hz": (0.0254**2, 0.0),
    },
}

for _rms_dimension, _base_dimension in (
    ("displacement_rms", "length"),
    ("force_rms", "force"),
    ("stress_rms", "stress"),
    ("acceleration_rms", "acceleration"),
):
    _UNITS[_rms_dimension] = dict(_UNITS[_base_dimension])


def _finite_number(value: object) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise UnitError("INVALID_NUMBER: expected an int or float, excluding bool")
    try:
        result = float(value)
    except OverflowError as exc:
        raise UnitError("NONFINITE_NUMBER: value exceeds finite float range") from exc
    if not math.isfinite(result):
        raise UnitError("NONFINITE_NUMBER: NaN and infinity are not quantities")
    return result


def _dimension_units(dimension: str) -> dict[str, tuple[float, float]]:
    if type(dimension) is not str or dimension not in _UNITS:
        raise UnitError("UNSUPPORTED_DIMENSION: an explicit supported dimension is required")
    return _UNITS[dimension]


def supported_units(dimension: str) -> tuple[str, ...]:
    """Return deterministic supported spellings for one explicit dimension."""
    return tuple(sorted(_dimension_units(dimension)))


def _scaled(number: float, factor: float) -> float:
    """Multiply once, retaining representable subnormals and rejecting erasure."""
    result = number * factor
    if not math.isfinite(result):
        raise UnitError("NONFINITE_RESULT: unit conversion overflowed")
    if number != 0 and result == 0:
        raise UnitError("RESULT_UNDERFLOW: a nonzero quantity would become zero")
    return result


def convert(value: float, from_unit: str, to_unit: str, dimension: str) -> float:
    """Convert a finite scalar without inferring its physical dimension.

    ``rpm`` means cycles/minute in ``frequency`` and angular speed in
    ``angular_speed``. Cross-dimension conversion requires the explicit helpers
    below. PSD and RMS dimensions require nonnegative values and retain the
    signal type; an ASD or a spectrum per rad/s is not accepted as a PSD per Hz.
    """
    number = _finite_number(value)
    units = _dimension_units(dimension)
    if type(from_unit) is not str or type(to_unit) is not str:
        raise UnitError("INVALID_UNIT: unit spellings must be strings")
    if from_unit not in units or to_unit not in units:
        raise UnitError("UNIT_DIMENSION_MISMATCH: unsupported unit for the stated dimension")
    if dimension.endswith(("_psd", "_rms")) and number < 0:
        raise UnitError("NEGATIVE_MAGNITUDE: PSD and RMS must be nonnegative")
    if dimension == "frequency" and number < 0:
        raise UnitError("NEGATIVE_FREQUENCY: use signed angular_speed for rotation direction")
    source_scale, source_offset = units[from_unit]
    target_scale, target_offset = units[to_unit]
    if source_offset == target_offset == 0:
        if dimension == "absolute_temperature" and number < 0:
            raise UnitError("BELOW_ABSOLUTE_ZERO: absolute temperature must be at least zero K")
        # Avoid an unnecessary SI intermediate: identity and representable
        # direct conversions must not overflow or underflow on the way to SI.
        return _scaled(number, source_scale / target_scale)
    canonical = number * source_scale + source_offset
    if not math.isfinite(canonical):
        raise UnitError("NONFINITE_RESULT: unit normalization overflowed")
    if dimension == "absolute_temperature" and canonical < 0:
        raise UnitError("BELOW_ABSOLUTE_ZERO: absolute temperature must be at least zero K")
    if from_unit == to_unit:
        return number
    # Affine temperature changes can legitimately produce zero (273.15 K to
    # 0 degC); the multiplicative underflow rule must not be applied here.
    result = (canonical - target_offset) / target_scale
    if not math.isfinite(result):
        raise UnitError("NONFINITE_RESULT: unit conversion overflowed")
    return result


def frequency_to_angular_speed(
    value: float, from_unit: str = "Hz", to_unit: str = "rad/s"
) -> float:
    """Explicitly map nonnegative cyclic frequency to angular speed using 2π."""
    number = convert(value, from_unit, from_unit, "frequency")
    convert(0.0, to_unit, to_unit, "angular_speed")
    factor = _UNITS["frequency"][from_unit][0] * (2.0 * math.pi) / _UNITS["angular_speed"][to_unit][0]
    return _scaled(number, factor)


def angular_speed_to_frequency(
    value: float, from_unit: str = "rad/s", to_unit: str = "Hz"
) -> float:
    """Convert nonnegative angular speed to cyclic frequency; never discard sign."""
    speed = convert(value, from_unit, from_unit, "angular_speed")
    if speed < 0:
        raise UnitError("NEGATIVE_FREQUENCY: choose the rotation magnitude explicitly")
    convert(0.0, to_unit, to_unit, "frequency")
    factor = _UNITS["angular_speed"][from_unit][0] / (2.0 * math.pi) / _UNITS["frequency"][to_unit][0]
    return _scaled(speed, factor)
