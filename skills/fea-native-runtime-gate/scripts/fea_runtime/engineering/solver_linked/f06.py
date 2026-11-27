# SPDX-License-Identifier: Apache-2.0
# Imported from FEA Expert Agent Plugin, fea_agent/solver_linked/f06.py
# Modified for the bundle to use only isolated numerical parsing.
"""Bounded reader for real formatted Nastran F06 engineering tables.

Authentic F06 layout is read directly. This is not a synthetic CSV dialect.
The reader preserves missing subcase context, physical state and printed source
precision. It does not establish file authenticity, native units, a matching
deck, solver success or result completeness by seeing a numeric table.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import math
import re

from .numbers import FrameError, integer, real

_NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+|[+-]\d+)?"
_NODE_ROW = re.compile(r"^\s*(?:0\s+)?(\d+)\s+G\s+(.+?)\s*$")


@dataclass(frozen=True)
class F06GridRow:
    grid_id: int
    components: tuple[float, ...]
    line: int


@dataclass(frozen=True)
class F06Table:
    kind: str
    subcase_id: int | None
    state_kind: str
    state_value: float | int | None
    rows: tuple[F06GridRow, ...]
    header_line: int


@dataclass(frozen=True)
class F06Eigenvalue:
    subcase_id: int | None
    mode: int
    extraction_order: int
    eigenvalue: float
    radians: float
    cycles: float
    generalized_mass: float
    generalized_stiffness: float
    line: int


@dataclass(frozen=True)
class F06Evidence:
    sha256: str
    tables: tuple[F06Table, ...]
    eigenvalues: tuple[F06Eigenvalue, ...]
    fatal_lines: tuple[int, ...]
    end_of_job_lines: tuple[int, ...]
    banner_evidence: tuple[tuple[int, str], ...]

    def to_dict(self) -> dict[str, object]:
        return {"schema": "fea.nastran-f06-evidence.v1", "sha256": self.sha256,
                "tables": [{"kind": t.kind, "subcase_id": t.subcase_id,
                            "state_kind": t.state_kind, "state_value": t.state_value,
                            "header_line": t.header_line,
                            "rows": [{"grid_id": r.grid_id, "components": list(r.components), "line": r.line} for r in t.rows]}
                           for t in self.tables],
                "eigenvalues": [{"subcase_id": r.subcase_id, "mode": r.mode,
                                 "extraction_order": r.extraction_order, "eigenvalue": r.eigenvalue,
                                 "radians": r.radians, "cycles": r.cycles, "generalized_mass": r.generalized_mass,
                                 "generalized_stiffness": r.generalized_stiffness, "line": r.line}
                                for r in self.eigenvalues],
                "fatal_lines": list(self.fatal_lines), "end_of_job_lines": list(self.end_of_job_lines),
                "complete_job_end_observed": len(self.end_of_job_lines) == 1,
                "banner_evidence": [{"line": line, "text": text} for line, text in self.banner_evidence],
                "native_authenticity": "NOT_ESTABLISHED", "units": "NOT_ENCODED_BY_F06",
                "scope": "Selected real displacement, load, SPC force, eigenvector and real-eigenvalue tables only; table selection/completeness and deck/job binding require independent project evidence"}


def _numbers(text: str, count: int) -> tuple[float, ...]:
    matches = list(re.finditer(_NUMBER, text))
    if len(matches) != count:
        raise FrameError("F06_NUMERIC_FIELD_COUNT")
    end = 0
    for match in matches:
        if text[end:match.start()].strip():
            raise FrameError("F06_NUMERIC_GARBAGE")
        end = match.end()
    if text[end:].strip():
        raise FrameError("F06_NUMERIC_GARBAGE")
    return tuple(real(match[0]) for match in matches)


def parse_f06(text: str) -> F06Evidence:
    if not isinstance(text, str) or len(text.encode()) > 10_000_000 or "\x00" in text:
        raise FrameError("F06_INPUT_LIMIT")
    lines = text.splitlines()
    if len(lines) > 100_000 or any(len(line) > 512 for line in lines):
        raise FrameError("F06_INPUT_LIMIT")
    subcase: int | None = None
    state_kind = "STATIC"
    state_value: float | int | None = None
    active = ""
    header = 0
    current_subcase: int | None = None
    current_state_kind = "STATIC"
    current_state_value: float | int | None = None
    current: list[F06GridRow] = []
    tables: list[F06Table] = []
    eigenvalues: list[F06Eigenvalue] = []
    fatal: list[int] = []
    ends: list[int] = []
    banners: list[tuple[int, str]] = []
    awaiting_header = False
    eigen_rows_this_page = 0

    def finish() -> None:
        nonlocal current, active, awaiting_header, eigen_rows_this_page
        if active in {"DISPLACEMENT", "SPCFORCES", "LOAD", "EIGENVECTOR"}:
            if not current:
                raise FrameError("F06_EMPTY_OR_TRUNCATED_TABLE", str(header))
            tables.append(F06Table(active, current_subcase, current_state_kind, current_state_value, tuple(current), header))
        if active == "EIGENVALUES" and eigen_rows_this_page == 0:
            raise FrameError("F06_EMPTY_OR_TRUNCATED_TABLE", str(header))
        current = []
        active = ""
        awaiting_header = False
        eigen_rows_this_page = 0

    for line_no, raw in enumerate(lines, 1):
        stripped = raw.strip()
        compact = re.sub(r"\s+", "", stripped.upper())
        if "FATAL" in stripped.upper() and ("MESSAGE" in stripped.upper() or "ERROR" in stripped.upper()):
            fatal.append(line_no)
        if re.search(r"\*\s*\*\s*\*\s*END OF JOB\s*\*\s*\*\s*\*", raw):
            finish()
            ends.append(line_no)
            continue
        if "NASTRAN" in raw.upper() and "PAGE" in raw.upper():
            finish()
            # Page boundaries reset physical state. A new table must show its
            # state again; a stale time/mode from the previous page is unsafe.
            state_kind, state_value = "STATIC", None
            subcase = None
            if len(banners) < 8:
                banners.append((line_no, stripped))
            continue
        match = re.fullmatch(r"\s*0?\s*SUBCASE\s+(\d+)\s*", raw, re.IGNORECASE)
        if match:
            finish()
            subcase = integer(match[1])
            continue
        state = re.search(r"\b(TIME|FREQUENCY|LOAD[ -]*(?:STEP|FACTOR|INCREMENT)|LFTSFQ)\s*=\s*(.+)$", raw, re.IGNORECASE)
        if state:
            finish()
            state_kind = re.sub(r"[ -]+", "_", state[1].upper())
            state_value = real(state[2].strip())
            continue
        # Statistical/envelope output can use the same vector heading and
        # columns as a deterministic displacement. Preserve that distinction;
        # the static investigation must never treat RMS as a load-factor state.
        statistic = re.search(r"\b(RMS|CRM|PSD|PSDF|MAXIMUM|MINIMUM|ENVELOPE)\b", raw.upper())
        if statistic or "ROOTMEANSQUARE" in compact or "POWERSPECTRALDENSITY" in compact:
            finish()
            state_kind = statistic[1] if statistic else (
                "RMS" if "ROOTMEANSQUARE" in compact else "PSD")
            state_value = None
        kind = ""
        if "DISPLACEMENTVECTOR" in compact:
            if "COMPLEX" in compact:
                raise FrameError("F06_COMPLEX_TABLE_UNSUPPORTED")
            kind = "DISPLACEMENT"
        elif "FORCESOFSINGLE-POINTCONSTRAINT" in compact:
            kind = "SPCFORCES"
        elif compact == "LOADVECTOR":
            kind = "LOAD"
        elif "REALEIGENVALUES" in compact:
            kind = "EIGENVALUES"
        elif "REALEIGENVECTORNO." in compact:
            # Spaces between the letters in N O are also collapsed by compact.
            number = re.search(r"REALEIGENVECTORNO\.(\d+)", compact)
            if number is None:
                raise FrameError("F06_MODE_NUMBER_MISSING")
            kind = "EIGENVECTOR"
            state_kind, state_value = "MODE", integer(number[1])
        if kind:
            finish()
            if ends:
                raise FrameError("F06_RESULT_AFTER_JOB_END")
            active, header = kind, line_no
            plain_titles = {"DISPLACEMENT": "DISPLACEMENTVECTOR",
                            "SPCFORCES": "FORCESOFSINGLE-POINTCONSTRAINT"}
            if kind in plain_titles and compact.lstrip("0") != plain_titles[kind] and state_kind == "STATIC":
                # Unknown qualifiers are evidence we do not know the state,
                # even when their values happen to match a static solution.
                state_kind, state_value = "UNRESOLVED", None
            current_subcase, current_state_kind, current_state_value = subcase, state_kind, state_value
            awaiting_header = True
            continue
        if not active or not stripped or stripped == "0":
            continue
        if active == "EIGENVALUES":
            if "MODE" in stripped or "ORDER" in stripped or "MASS" in stripped or "STIFFNESS" in stripped:
                continue
            fields = stripped.split()
            if len(fields) == 7 and re.fullmatch(r"\d+", fields[0]) and re.fullmatch(r"\d+", fields[1]):
                numbers = [real(x) for x in fields[2:]]
                eigenvalue, radians, cycles, generalized_mass, generalized_stiffness = numbers
                if min(radians, cycles, generalized_mass) < 0:
                    raise FrameError("F06_MODAL_SCALARS_INVALID")
                # Printed quantities have about seven significant digits. Never
                # compare these at binary-double equality or erase negative modes.
                if eigenvalue >= 0 and (not math.isclose(radians ** 2, eigenvalue, rel_tol=3e-6, abs_tol=1e-12)
                                       or not math.isclose(2 * math.pi * cycles, radians, rel_tol=3e-6, abs_tol=1e-12)):
                    raise FrameError("F06_MODAL_FREQUENCY_CONTRADICTION")
                if not math.isclose(eigenvalue * generalized_mass, generalized_stiffness, rel_tol=3e-6, abs_tol=1e-12):
                    raise FrameError("F06_MODAL_MASS_STIFFNESS_CONTRADICTION")
                item = F06Eigenvalue(current_subcase, integer(fields[0]), integer(fields[1]),
                                     eigenvalue, radians, cycles, generalized_mass, generalized_stiffness, line_no)
                if any(old.subcase_id == item.subcase_id and old.mode == item.mode for old in eigenvalues):
                    raise FrameError("F06_DUPLICATE_EIGENVALUE")
                eigenvalues.append(item)
                eigen_rows_this_page += 1
                awaiting_header = False
                continue
            if re.match(r"\s*\d+\s+\d+\s+", raw):
                raise FrameError("F06_MALFORMED_EIGENVALUE_ROW")
            if awaiting_header:
                raise FrameError("F06_EIGENVALUE_HEADER_UNSUPPORTED")
            finish()
            continue
        if "POINT ID." in raw.upper() and "TYPE" in raw.upper() and all(x in raw.upper().split() for x in ("T1", "T2", "T3", "R1", "R2", "R3")):
            awaiting_header = False
            continue
        match = _NODE_ROW.fullmatch(raw)
        if match:
            if awaiting_header:
                raise FrameError("F06_VECTOR_HEADER_MISSING")
            identifier = integer(match[1])
            if any(row.grid_id == identifier for row in current):
                raise FrameError("F06_DUPLICATE_GRID_ROW")
            current.append(F06GridRow(identifier, _numbers(match[2], 6), line_no))
            if len(current) > 10_000:
                raise FrameError("F06_TABLE_ROW_LIMIT")
            continue
        if re.match(r"\s*(?:0\s+)?\d+\s+[A-Z]\s+", raw):
            raise FrameError("F06_UNSUPPORTED_OR_MALFORMED_POINT_ROW")
        if awaiting_header:
            raise FrameError("F06_VECTOR_HEADER_UNSUPPORTED", str(line_no))
        finish()
    finish()
    if len(ends) > 1:
        raise FrameError("F06_MULTIPLE_JOBS")
    if not tables and not eigenvalues:
        raise FrameError("F06_NO_SUPPORTED_TABLES")
    # A continuation page without a repeated state label is unresolved when
    # this subcase has nonstatic tables. Resetting the label to STATIC would
    # otherwise turn an incomplete transient/modal/statistical page into a
    # falsely acceptable service result. Mixed states need an explicit reader.
    nonstatic_subcases = {table.subcase_id for table in tables if table.state_kind != "STATIC"}
    tables = [replace(table, state_kind="UNRESOLVED")
              if table.state_kind == "STATIC" and table.subcase_id in nonstatic_subcases else table
              for table in tables]
    # Repeated table headers on continuation pages can be joined by identity;
    # overlapping grid rows are ambiguous even when their printed values match.
    merged: dict[tuple[str, int | None, str, float | int | None], F06Table] = {}
    for table in tables:
        key = (table.kind, table.subcase_id, table.state_kind, table.state_value)
        if key in merged:
            previous = merged[key]
            if {r.grid_id for r in previous.rows} & {r.grid_id for r in table.rows}:
                raise FrameError("F06_AMBIGUOUS_REPEATED_TABLE")
            merged[key] = F06Table(table.kind, table.subcase_id, table.state_kind, table.state_value,
                                  previous.rows + table.rows, previous.header_line)
        else:
            merged[key] = table
    return F06Evidence(hashlib.sha256(text.encode()).hexdigest(), tuple(merged.values()), tuple(eigenvalues),
                       tuple(fatal), tuple(ends), tuple(banners))
