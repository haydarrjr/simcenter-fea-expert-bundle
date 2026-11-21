"""Verify the synthetic oscillator jobs using the scoped 2612 F06 layout."""
import argparse
import hashlib
import json
from math import pi, sqrt
from pathlib import Path
import re


FREQUENCIES = tuple(5 + i / 4 for i in range(81))
NUMBER = r"[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[ED][+-]\d+)?"
GRID_X = re.compile(rf"^0?\s+1\s+G\s+({NUMBER})\s")
NEXT_X = re.compile(rf"^\s+({NUMBER})\s")


def receptance(frequency):
    omega = 2 * pi * frequency
    return 1 / complex(10000 - omega**2, 4 * omega)


def random_reference(force_psd):
    psd = [force_psd * abs(receptance(frequency))**2 for frequency in FREQUENCIES]
    variance = 0.25 * sum((a + b) / 2 for a, b in zip(psd, psd[1:]))
    return sqrt(variance)


def read_job(folder, fixture):
    deck = folder / "oscillator.dat"
    f06 = folder / "oscillator.f06"
    log = folder / "oscillator.log"
    result = folder / "oscillator.op2"
    expected = Path(__file__).with_name("fixtures") / fixture
    if deck.read_bytes() != expected.read_bytes() or not result.stat().st_size:
        raise ValueError(f"{folder}: mismatched input or empty OP2")
    text = f06.read_text(encoding="ascii", errors="replace")
    terminal = log.read_text(encoding="ascii", errors="replace")
    if ("END OF JOB" not in text or re.search(r"\bFATAL\s+MESSAGE\b", text)
            or not re.search(r"\bAnalysis complete[ \t]+0[ \t]*$", terminal, re.MULTILINE)):
        raise ValueError(f"{folder}: terminal solver evidence missing or fatal")
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (deck, f06, log, result)}
    return text, files


def harmonic(text):
    rows = []
    case = None
    frequency = None
    active = False
    lines = iter(text.splitlines())
    for line in lines:
        if match := re.search(r"\bSUBCASE\s+(\d+)\s*$", line):
            case = int(match[1])
        if match := re.fullmatch(rf"\s+FREQUENCY\s*=\s*({NUMBER})\s*", line):
            frequency = float(match[1])
            active = False
        if "C O M P L E X   D I S P L A C E M E N T" in line:
            active = True
        if active and (match := GRID_X.match(line)):
            imag = NEXT_X.match(next(lines))
            if imag is None or case != 1 or frequency is None:
                raise ValueError("unbound complex displacement row")
            rows.append((frequency, complex(float(match[1]), float(imag[1]))))
    if tuple(freq for freq, _ in rows) != FREQUENCIES:
        raise ValueError("unexpected, duplicate or missing complex response frequencies")
    errors = [abs(observed - receptance(freq)) / abs(receptance(freq)) for freq, observed in rows]
    if max(errors) > 2e-5:
        raise ValueError(f"complex response disagrees with analytic reference: {max(errors)}")
    return {"points": len(rows), "max_complex_relative_error": max(errors)}


def random(text, force_psd=2):
    in_rms = False
    random_set = None
    values = []
    for line in text.splitlines():
        if match := re.search(r"\bRANDOM\s+(\d+)\s*$", line):
            random_set = int(match[1])
            in_rms = False
        if "( ROOT MEAN SQUARE;" in line:
            in_rms = True
        if in_rms and (match := GRID_X.match(line)):
            if random_set != 50:
                raise ValueError("unbound response RMS")
            values.append(float(match[1]))
            in_rms = False
    if len(values) != 1:
        raise ValueError("expected one RMS at the requested grid")
    expected = random_reference(force_psd)
    error = abs(values[0] - expected) / expected
    if error > 2e-5:
        raise ValueError(f"RMS disagrees with analytic sampled-spectrum integral: {error}")
    return {"rms": values[0], "reference": expected, "relative_error": error}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("direct", "modal", "random"):
        parser.add_argument(arg, type=Path)
    parser.add_argument("--correlated", type=Path, help="two coincident unit inputs with positive CSD")
    args = parser.parse_args()
    jobs = [
        ("sol108", args.direct, "sol108-oscillator.txt", harmonic),
        ("sol111_harmonic", args.modal, "sol111-harmonic-oscillator.txt", harmonic),
        ("sol111_random", args.random, "sol111-oscillator.txt", random),
    ]
    if args.correlated:
        jobs.append(("sol111_correlated", args.correlated, "sol111-correlated-oscillator.txt",
                     lambda text: random(text, force_psd=6)))
    report = {}
    for label, folder, fixture, verify in jobs:
        text, hashes = read_job(folder, fixture)
        report[label] = {**verify(text), "sha256": hashes}
    print(json.dumps(report, indent=2))
