# SPDX-License-Identifier: Apache-2.0
# Imported from FEA Expert Agent Plugin, fea_agent/structural_quant/numerics.py
"""Small, bounded arithmetic primitives for source structural references."""
from __future__ import annotations

import math


class NumericRangeError(ValueError):
    """A positive physical result cannot be represented by a finite float."""


def positive_product_ratio(
    numerators: tuple[float, ...], denominators: tuple[float, ...] = ()
) -> float:
    """Evaluate products without overflowing/underflowing intermediate factors.

    Exponents are accumulated as integers. A zero result from positive inputs
    is rejected: it must never become an apparently exact zero-error reference.
    """
    mantissa, exponent = 1.0, 0
    for inverse, factors in ((False, numerators), (True, denominators)):
        for factor in factors:
            if not math.isfinite(factor) or factor <= 0:
                raise NumericRangeError("POSITIVE_FINITE_FACTOR_REQUIRED")
            m, e = math.frexp(factor)
            mantissa = mantissa / m if inverse else mantissa * m
            exponent += -e if inverse else e
            mantissa, adjustment = math.frexp(mantissa)
            exponent += adjustment
    try:
        result = math.ldexp(mantissa, exponent)
    except OverflowError as error:
        raise NumericRangeError("UNREPRESENTABLE_POSITIVE_STRUCTURAL_RESULT") from error
    if not math.isfinite(result) or result <= 0:
        raise NumericRangeError("UNREPRESENTABLE_POSITIVE_STRUCTURAL_RESULT")
    return result
