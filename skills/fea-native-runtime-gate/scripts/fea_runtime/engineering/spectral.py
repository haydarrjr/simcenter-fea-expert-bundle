"""Independent spectral verification using a declared native FRF and spectral grid."""

import math

from ..contracts import fields, number, sha, text


def _complex_pair(value):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("complex data require explicit real and imaginary parts")
    return complex(number(value[0]), number(value[1]))


def verify_response(payload):
    fields(payload, ("frf_identity", "input_identity", "result_identity", "phase", "convention",
                     "frequencies_hz", "input_frequencies_hz", "result_frequencies_hz", "frf",
                     "input_psd", "native_psd", "native_rms", "tolerances"))
    for name in ("frf_identity", "input_identity", "result_identity"):
        fields(payload[name], ("sha256", "unit", "frame", "entity", "quantity"))
        sha(payload[name]["sha256"])
        for key in ("unit", "frame", "entity", "quantity"):
            text(payload[name][key])
    frf, force, response = (payload[key] for key in ("frf_identity", "input_identity", "result_identity"))
    if (payload["phase"] != "exp(+iwt)" or payload["convention"] != "one-sided-per-Hz"
            or frf["entity"] != response["entity"] or frf["frame"] != response["frame"]
            or frf["quantity"] != response["quantity"]
            or frf["unit"] != response["unit"] + "/" + force["unit"]):
        raise ValueError("incompatible FRF and PSD identity, units, frame or convention")
    frequencies = payload["frequencies_hz"]
    if (type(frequencies) is not list or not 2 <= len(frequencies) <= 100000
            or any(f < 0 for f in map(number, frequencies))
            or any(b <= a for a, b in zip(frequencies, frequencies[1:]))
            or payload["input_frequencies_hz"] != frequencies or payload["result_frequencies_hz"] != frequencies):
        raise ValueError("FRF and PSD must share a strictly ordered complete physical frequency grid")
    bounds = payload["tolerances"]
    fields(bounds, ("psd_abs", "rms_abs", "relative"))
    if any(number(value) < 0 for value in bounds.values()):
        raise ValueError("spectral tolerances must be nonnegative")
    value = []
    errors = []
    for h, auto_power, observed in zip(payload["frf"], payload["input_psd"], payload["native_psd"], strict=True):
        auto_power, observed = number(auto_power), number(observed)
        if min(auto_power, observed) < 0:
            raise ValueError("PSD must be nonnegative")
        prediction = abs(_complex_pair(h)) ** 2 * auto_power
        value.append(number(prediction))
        errors.append(abs(prediction - observed))
    if len(value) != len(frequencies):
        raise ValueError("incomplete FRF or PSD coverage")
    integral = math.fsum((right - left) * (a / 2 + b / 2)
                         for left, right, a, b in zip(frequencies, frequencies[1:], value, value[1:]))
    rms = math.sqrt(number(integral))
    native = number(payload["native_rms"])
    if native < 0:
        raise ValueError("RMS must be nonnegative")
    psd_ok = all(error <= bounds["psd_abs"] + bounds["relative"] * observed
                 for error, observed in zip(errors, payload["native_psd"], strict=True))
    rms_error = abs(rms - native)
    rms_ok = rms_error <= bounds["rms_abs"] + bounds["relative"] * native
    return {"status": "MATCHED" if psd_ok and rms_ok else "DIFFERS",
            "coverage": "SINGLE_INPUT_SAMPLED_BAND", "points": len(value),
            "max_psd_absolute_error": max(errors), "rms_absolute_error": rms_error,
            "predicted_rms": rms, "native_rms": native, "units": response["unit"],
            "band_hz": [frequencies[0], frequencies[-1]]}
