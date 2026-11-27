# SPDX-License-Identifier: Apache-2.0
# Extracted from FEA Expert Agent Plugin solver_linked/deck.py and types.py.
"""Numerical token parser for the embedded independent F06 reader."""

import math
import re


class FrameError(ValueError):
    """The input cannot support the requested bounded calculation."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(code + (": " + detail if detail else ""))
        self.code = code


def real(token: str, default: float | None = None) -> float:
    if not token and default is not None:
        return default
    if len(token) > 64:
        raise FrameError("FRAME_NUMBER_INVALID")
    token = token.replace("D", "E").replace("d", "e")
    if not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]+)?", token):
        match = re.fullmatch(r"([+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))([+-][0-9]+)", token)
        if match is None:
            raise FrameError("FRAME_NUMBER_INVALID")
        token = match[1] + "E" + match[2]
    value = float(token)
    if not math.isfinite(value):
        raise FrameError("FRAME_NUMBER_NONFINITE")
    if value == 0 and any(c in "123456789" for c in token.upper().split("E")[0]):
        raise FrameError("FRAME_NUMBER_UNDERFLOW")
    return value


def integer(token: str) -> int:
    if not re.fullmatch(r"[0-9]{1,10}", token) or not 1 <= int(token) <= 2_147_483_647:
        raise FrameError("FRAME_ID_INVALID")
    return int(token)
