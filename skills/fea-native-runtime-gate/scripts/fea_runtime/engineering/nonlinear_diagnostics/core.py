# SPDX-License-Identifier: Apache-2.0
# Imported from FEA Expert Agent Plugin, fea_agent/nonlinear_diagnostics/core.py
"""Bounded Nastran evidence parser; no INCLUDE resolution, deck execution or repair.

Known Case Control and nonlinear control semantics are documented for 2606.
Unknown model cards are preserved as opaque evidence, never declared valid.
The optional iteration CSV is an explicitly FEA-owned interchange format, not
a fabricated native .f06 dialect. Its vendor-error columns are not recomputed.
"""

from __future__ import annotations

from collections.abc import Callable
import csv
from dataclasses import dataclass
import hashlib
import io
import math
import re


RELEASE = "PL20251024315120185"
DOCS = {
    "NLPARM_CASE": "en-US.PL20251024315120185.QRG.id509686",
    "NLPARM": "en-US.PL20251024315120185.QRG.id508411",
    "NLCNTL_CASE": "en-US.PL20251024315120185.QRG.xid609427",
    "NLCNTL": "en-US.PL20251024315120185.QRG.xid612333",
    "NLCNTL2": "en-US.PL20251024315120185.QRG.xid1270968",
    "SEQDEP": "en-US.PL20251024315120185.QRG.xid609430",
    "PRELOAD401": "en-US.PL20251024315120185.multi_step_nonlinear.xid924582",
    "PRELOAD402": "en-US.PL20251024315120185.multi_step_nonlinear.xid1603002",
    "ITERATION401": "en-US.PL20251024315120185.multi_step_nonlinear.xid612610",
    "CONVERGENCE401": "en-US.PL20251024315120185.multi_step_nonlinear.xid612588",
    "CONTACT401": "en-US.PL20251024315120185.multi_step_nonlinear.xid1201098",
}
MAX_BYTES = 2_000_000
MAX_LINES = 30_000
_REAL = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?\Z")
_COMPACT = re.compile(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))([+-]\d+)\Z")


class DiagnosticError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class BulkRecord:
    name: str
    fields: tuple[str, ...]
    lines: tuple[int, ...]
    format: str


@dataclass(frozen=True)
class Subcase:
    identifier: int
    local: dict[str, str]
    effective: dict[str, str]
    line: int


@dataclass(frozen=True)
class DeckEvidence:
    solution: int
    subcases: tuple[Subcase, ...]
    records: tuple[BulkRecord, ...]
    sha256: str
    unresolved_includes: tuple[int, ...]
    unreviewed_executive: tuple[int, ...]


@dataclass(frozen=True)
class LogSummary:
    subcase: int | None
    accumulated_iteration: int
    current_iteration: int
    equilibrium: bool | None
    contact: bool | None
    bolt: bool | None
    line: int


@dataclass(frozen=True)
class LogEvidence:
    sha256: str
    summaries: tuple[LogSummary, ...]
    events: tuple[tuple[str, int], ...]
    unknown_nonempty_lines: int


def _bounded(text: str) -> list[str]:
    if len(text.encode("utf-8")) > MAX_BYTES or "\x00" in text:
        raise DiagnosticError("INPUT_LIMIT", "Source evidence exceeds the byte limit or contains NUL.")
    lines = text.splitlines()
    if len(lines) > MAX_LINES or any(len(line) > 2048 for line in lines):
        raise DiagnosticError("INPUT_LIMIT", "Source evidence exceeds the line/width limit.")
    return lines


def _real(value: str) -> float:
    if len(value) > 64:
        raise DiagnosticError("INVALID_NUMBER", "Numeric token exceeds its bound.")
    normalized = value.replace("D", "E").replace("d", "e")
    if not _REAL.fullmatch(normalized):
        compact = _COMPACT.fullmatch(normalized)
        if compact is None:
            raise DiagnosticError("INVALID_NUMBER", "Expected finite decimal/Fortran notation, not an expression.")
        normalized = compact[1] + "E" + compact[2]
    number = float(normalized)
    if not math.isfinite(number):
        raise DiagnosticError("NONFINITE_NUMBER", "Nonfinite solver evidence is invalid.")
    mantissa = normalized.upper().split("E")[0]
    if number == 0 and any(c in "123456789" for c in mantissa):
        raise DiagnosticError("NUMERIC_UNDERFLOW", "Nonzero evidence underflows the supported representation.")
    return number


def _integer(value: str) -> int:
    if not re.fullmatch(r"[0-9]{1,10}", value) or not 1 <= int(value) <= 2_147_483_647:
        raise DiagnosticError("INVALID_ID", "Expected a positive bounded integer ID.")
    return int(value)


def _bulk(lines: list[tuple[int, str]]) -> tuple[BulkRecord, ...]:
    result: list[BulkRecord] = []
    name = ""
    fields: list[str] = []
    source_lines: list[int] = []
    current_format = ""
    expected_label = ""
    for number, line in lines:
        if "," in line:
            tokens = [part.strip() for part in line.split(",")]
            head = tokens[0].upper()
            fmt = "FREE"
            data = tokens[1:]
            label = ""
            if data and data[-1].startswith("+") and not _REAL.fullmatch(data[-1]):
                label = data.pop()
        else:
            head = line[:8].strip().upper()
            fmt = "LARGE" if "*" in head else "SMALL"
            width = 16 if fmt == "LARGE" else 8
            data = [line[start:start + width].strip() for start in range(8, 72, width)]
            label = line[72:80].strip() if len(line) > 72 else ""
            if len(line) > 80 and line[80:].strip():
                raise DiagnosticError("CARD_WIDTH", "Fixed-format noncomment data after column 80 is not accepted.")
        continuation = not head or head.startswith(("+", "*"))
        if continuation:
            if fmt == "FREE" and head and not re.fullmatch(r"\+[A-Z0-9_-]{0,7}", head):
                raise DiagnosticError("INVALID_FREE_CONTINUATION", "Free-field continuation uses a bounded plus label or a blank first field.")
            if not name or fmt != current_format:
                raise DiagnosticError("ORPHAN_OR_MIXED_CONTINUATION", "Continuation must belong to the same record and field format.")
            if expected_label and head != expected_label.upper():
                raise DiagnosticError("CONTINUATION_LABEL_MISMATCH", "Continuation labels do not match.")
            if len(source_lines) >= 64:
                raise DiagnosticError("CONTINUATION_LIMIT", "One Bulk Data card exceeds 64 source lines.")
            fields.extend(data)
            source_lines.append(number)
        else:
            if expected_label:
                raise DiagnosticError("MISSING_CONTINUATION", "A declared continuation was not supplied.")
            if name:
                result.append(BulkRecord(name, tuple(fields), tuple(source_lines), current_format))
            name = head.rstrip("*")
            if not re.fullmatch(r"[A-Z][A-Z0-9]{0,7}", name):
                raise DiagnosticError("INVALID_CARD_NAME", "Unsupported Bulk Data record name.")
            fields, source_lines, current_format = data, [number], fmt
        expected_label = label
    if expected_label:
        raise DiagnosticError("MISSING_CONTINUATION", "Last card has an unresolved continuation.")
    if name:
        result.append(BulkRecord(name, tuple(fields), tuple(source_lines), current_format))
    if len(result) > 15_000:
        raise DiagnosticError("CARD_LIMIT", "Too many Bulk Data records.")
    return tuple(result)


def parse_deck(text: str) -> DeckEvidence:
    lines = _bounded(text)
    stage = "EXECUTIVE"
    sol: int | None = None
    global_scope: dict[str, str] = {}
    local_scope = global_scope
    raw_cases: list[tuple[int, dict[str, str], int]] = []
    bulk_lines: list[tuple[int, str]] = []
    includes: list[int] = []
    executive: list[int] = []
    for number, raw in enumerate(lines, 1):
        line = raw.split("$", 1)[0].rstrip()
        stripped = line.strip()
        upper = stripped.upper()
        if not stripped:
            continue
        if upper.startswith("INCLUDE"):
            includes.append(number)
            continue
        if stage == "DONE":
            raise DiagnosticError("TRAILING_DECK_DATA", "Noncomment data follows ENDDATA.")
        if stage == "EXECUTIVE":
            match = re.fullmatch(r"SOL\s+(\d+)", upper)
            if match:
                if sol is not None:
                    raise DiagnosticError("DUPLICATE_SOLUTION", "Exactly one solution sequence is allowed.")
                sol = int(match[1])
                if sol not in {106, 401, 402}:
                    raise DiagnosticError("UNSUPPORTED_SOLUTION", "This parser diagnoses SOL106/401/402 only.")
            elif upper == "CEND" and sol is not None:
                stage = "CASE"
            else:
                executive.append(number)
        elif stage == "CASE":
            if upper == "BEGIN BULK":
                stage = "BULK"
                continue
            match = re.fullmatch(r"SUBCASE\s*(?:=\s*)?(\d+)", upper)
            if match:
                identifier = _integer(match[1])
                if any(identifier == case[0] for case in raw_cases) or len(raw_cases) >= 128:
                    raise DiagnosticError("SUBCASE_ID_OR_LIMIT", "Subcases must be unique and within the bounded profile.")
                local_scope = {}
                raw_cases.append((identifier, local_scope, number))
                continue
            match = re.fullmatch(r"([A-Z][A-Z0-9_]*(?:\([^=]*\))?)\s*=\s*([^=]+)", upper)
            if match is None:
                raise DiagnosticError("UNSUPPORTED_CASE_SYNTAX", f"Cannot interpret Case Control at line {number}.")
            key, value = match[1].strip(), match[2].strip()
            if key in local_scope:
                raise DiagnosticError("DUPLICATE_CASE_SELECTION", "Repeated Case Control selection in one scope is ambiguous.")
            local_scope[key] = value
        elif upper == "ENDDATA":
            stage = "DONE"
        else:
            bulk_lines.append((number, line))
    if sol is None or stage != "DONE" or not raw_cases:
        raise DiagnosticError("INCOMPLETE_DECK", "Require SOL, CEND, explicit subcases, BEGIN BULK and ENDDATA.")
    cases = tuple(Subcase(identifier, dict(local), global_scope | local, number) for identifier, local, number in raw_cases)
    return DeckEvidence(sol, cases, _bulk(bulk_lines), hashlib.sha256(text.encode()).hexdigest(), tuple(includes), tuple(executive))


def parse_f06(text: str) -> LogEvidence:
    """Extract documented diagnostic identifiers and aligned EQU/CON/BLT columns.

    A table is recognized only with its actual header positions and numeric first
    two iteration columns. Missing/unrecognized output remains missing evidence.
    """
    lines = _bounded(text)
    summaries: list[LogSummary] = []
    events: list[tuple[str, int]] = []
    columns: dict[str, int] = {}
    subcase: int | None = None
    unknown = 0
    tokens = {
        "%%%E01-OP2BO01": "BOLT_ELEMENT_FAMILY_ERROR",
        "%%%E01-OP2BO02": "BOLT_DIRECTION_REQUIRED",
        "%%%E06-OP2BO03": "BOLT_CUT_INVALID",
        "%%%E08-OP2BO03": "BOLT_DIRECTION_REQUIRED",
        "%%%W01-OP2BO03": "BOLT_CUT_AXIS_WARNING",
        "USER FATAL MESSAGE": "SOLVER_FATAL_MESSAGE",
        "SYSTEM FATAL MESSAGE": "SOLVER_FATAL_MESSAGE",
    }
    for number, line in enumerate(lines, 1):
        upper = line.upper()
        matched = False
        case_match = re.search(r"\bSUBCASE\s*(?:=|NO\.?\s*)?\s*(\d+)\b", upper)
        if case_match:
            subcase = _integer(case_match[1])
            columns = {}
            matched = True
        for token, code in tokens.items():
            if token in upper:
                events.append((code, number))
                matched = True
        matches = {m[0]: m.start() for m in re.finditer(r"\b(?:EQU|CON|BLT)\b", upper)}
        if "EQU" in matches:
            columns = matches
            matched = True
        elif columns:
            first = min(columns.values())
            prefix = line[:first].split()
            if len(prefix) >= 2 and all(re.fullmatch(r"\d+", t) for t in prefix[:2]):
                flags: dict[str, bool | None] = {}
                valid = True
                for name, offset in columns.items():
                    token = line[offset:offset + len(name)].strip().lower()
                    if token not in {"y", "n", "-"}:
                        valid = False
                        break
                    flags[name] = None if token == "-" else token == "y"
                if valid:
                    summaries.append(LogSummary(subcase, _integer(prefix[0]), _integer(prefix[1]),
                                                flags.get("EQU"), flags.get("CON"), flags.get("BLT"), number))
                    matched = True
        if line.strip() and not matched:
            unknown += 1
    return LogEvidence(hashlib.sha256(text.encode()).hexdigest(), tuple(summaries), tuple(events), unknown)


def _pairs(record: BulkRecord) -> dict[str, str]:
    result: dict[str, str] = {}
    position = 1
    while position < len(record.fields):
        name = record.fields[position].upper()
        position += 1
        if not name:
            continue
        if position >= len(record.fields) or not record.fields[position]:
            raise DiagnosticError("MISSING_CONTROL_VALUE", f"Missing value for {record.name} parameter {name}.")
        if name in result:
            raise DiagnosticError("DUPLICATE_CONTROL_PARAMETER", "A nonlinear control parameter is defined twice.")
        result[name] = record.fields[position].upper()
        position += 1
    return result


def _controls(deck: DeckEvidence) -> dict[tuple[str, int], dict[str, str]]:
    result: dict[tuple[str, int], dict[str, str]] = {}
    nlp_fields = ("ID", "NINC", "DT", "KMETHOD", "KSTEP", "MAXITER", "CONV", "INTOUT",
                  "EPSU", "EPSP", "EPSW", "MAXDIV", "MAXQN", "MAXLS", "FSTRESS", "LSTOL",
                  "MAXBIS", "", "", "", "MAXR", "", "RTOLB")
    for record in deck.records:
        if record.name not in {"NLPARM", "NLCNTL", "NLCNTL2"}:
            continue
        if not record.fields:
            raise DiagnosticError("MISSING_CONTROL_ID", "Nonlinear control card has no ID.")
        key = (record.name, _integer(record.fields[0]))
        if record.name == "NLPARM":
            if key in result:
                raise DiagnosticError("DUPLICATE_NLPARM", "One NLPARM ID cannot have conflicting definitions.")
            result[key] = {name: value.upper() for name, value in zip(nlp_fields, record.fields, strict=False) if name and value}
        else:
            values = _pairs(record)
            if key in result and result[key].keys() & values.keys():
                raise DiagnosticError("DUPLICATE_CONTROL_PARAMETER", "Parameter repeated across same-ID control records.")
            result.setdefault(key, {}).update(values)
    for (card, _), values in result.items():
        if "CONV" in values and (not set(values["CONV"]) <= {"U", "P", "W"} or len(set(values["CONV"])) != len(values["CONV"])):
            raise DiagnosticError("INVALID_CONVERGENCE_FLAGS", "CONV must select unique U/P/W flags.")
        for name in ("EPSU", "EPSP", "EPSW", "PRCR", "PRCE", "PRDR", "PRDE", "REFP", "REFU", "REFE"):
            if name in values and _real(values[name]) <= 0:
                raise DiagnosticError("INVALID_CONTROL_TOLERANCE", "Convergence tolerances and references must be positive.")
        if card == "NLPARM":
            if values.get("KMETHOD", "AUTO") not in {"AUTO", "SEMI", "ITER"}:
                raise DiagnosticError("INVALID_STIFFNESS_METHOD", "Unsupported NLPARM stiffness update method.")
            if "NINC" in values and not 1 <= _integer(values["NINC"]) < 1000:
                raise DiagnosticError("INVALID_INCREMENT_COUNT", "NLPARM NINC must lie between 1 and 999.")
        if "MAXITER" in values:
            maximum = _integer(values["MAXITER"])
            if card == "NLCNTL" and maximum > 50:
                raise DiagnosticError("INVALID_SOL401_ITERATION_LIMIT", "Documented SOL401 MAXITER upper bound is 50.")
        if "MAXBIS" in values:
            count = _real(values["MAXBIS"])
            if not count.is_integer() or (card == "NLPARM" and not -10 <= count <= 10) or (card == "NLCNTL" and not 0 < count <= 10) or (card == "NLCNTL2" and count < 0):
                raise DiagnosticError("INVALID_FAMILY_BISECTION_LIMIT", "MAXBIS domains differ between SOL106, SOL401 and SOL402.")
        if card == "NLCNTL2" and "RSUB" in values:
            number = _real(values["RSUB"])
            if not number.is_integer() or number < -1:
                raise DiagnosticError("INVALID_RESTART_SUBCASE", "RSUB must be -1, 0 or a preceding subcase ID.")
    return result


CSV_COLUMNS = ("subcase", "increment", "iteration", "accumulated_iteration", "load_factor",
               "force_error", "displacement_error", "work_error", "residual_norm_n",
               "contact_change_fraction", "penetration_ratio", "contact_closed_count",
               "artificial_energy_j", "strain_energy_j", "external_force_n", "reaction_force_n", "claimed_converged")


def _trace(text: str) -> list[dict[str, float | int | bool]]:
    lines = _bounded(text)
    if not lines or lines[0] != "FEA_EXPERT_ITERATION_CSV_V2":
        raise DiagnosticError("TRACE_FORMAT", "Iteration interchange must identify its FEA-owned format explicitly.")
    reader = csv.DictReader(io.StringIO("\n".join(lines[1:])))
    if reader.fieldnames != list(CSV_COLUMNS):
        raise DiagnosticError("TRACE_COLUMNS", "Iteration CSV has an unknown, duplicated or reordered column contract.")
    result: list[dict[str, float | int | bool]] = []
    seen: set[tuple[int, int]] = set()
    last_accum: dict[int, int] = {}
    for row in reader:
        if None in row or any(v is None or v == "" for v in row.values()):
            raise DiagnosticError("TRACE_ROW", "Every numerical observation must be explicit.")
        record: dict[str, float | int | bool] = {}
        for name in CSV_COLUMNS:
            value = row[name]
            if name in {"subcase", "increment", "iteration", "accumulated_iteration"}:
                record[name] = _integer(value)
            elif name == "claimed_converged":
                if value not in {"true", "false"}:
                    raise DiagnosticError("TRACE_BOOLEAN", "Use literal true/false for a convergence claim.")
                record[name] = value == "true"
            else:
                record[name] = _real(value)
        sid, accumulated = int(record["subcase"]), int(record["accumulated_iteration"])
        if (sid, accumulated) in seen or accumulated <= last_accum.get(sid, 0):
            raise DiagnosticError("TRACE_ORDER", "Accumulated iteration must increase uniquely within each subcase.")
        seen.add((sid, accumulated))
        last_accum[sid] = accumulated
        for name in ("force_error", "displacement_error", "work_error", "residual_norm_n", "penetration_ratio",
                     "contact_closed_count", "artificial_energy_j", "strain_energy_j"):
            if float(record[name]) < 0:
                raise DiagnosticError("NEGATIVE_TRACE_MAGNITUDE", "Error, energy and count magnitudes cannot be negative.")
        if not 0 <= float(record["contact_change_fraction"]) <= 1:
            raise DiagnosticError("CONTACT_CHANGE_FRACTION", "Contact change fraction must lie in [0,1].")
        if not float(record["contact_closed_count"]).is_integer():
            raise DiagnosticError("CONTACT_COUNT", "Closed-contact count must be an integer.")
        result.append(record)
        if len(result) > 10000:
            raise DiagnosticError("TRACE_LIMIT", "Iteration record budget exhausted.")
    if not result:
        raise DiagnosticError("TRACE_EMPTY", "No iteration observations were supplied.")
    return result


def _object(value: object, required: set[str], optional: set[str] | None = None) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(k, str) for k in value):
        raise DiagnosticError("INVALID_OBJECT", "Expected a JSON object.")
    data: dict[str, object] = {str(k): v for k, v in value.items()}
    if not required <= data.keys() or data.keys() - required - (optional or set()):
        raise DiagnosticError("OBJECT_FIELDS", "Missing or unknown request fields.")
    return data


def _string(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise DiagnosticError("INVALID_TEXT", "Expected nonempty source text or identifier.")
    return value


def _positive(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DiagnosticError("INVALID_POLICY", "Expected a positive finite policy number.")
    try:
        number = float(value)
    except OverflowError as exc:
        raise DiagnosticError("INVALID_POLICY", "Policy number is outside the supported range.") from exc
    if not math.isfinite(number) or number <= 0:
        raise DiagnosticError("INVALID_POLICY", "Expected a positive finite policy number.")
    return number


def _force_projection(value: object, frame_id: str) -> dict[str, object]:
    projection = _object(value, {"frame_id", "unit_axis", "convention"})
    if _string(projection["frame_id"]) != frame_id:
        raise DiagnosticError("TRACE_FORCE_FRAME_MISMATCH", "Force components must use the exact declared case frame.")
    if projection["convention"] != "SIGNED_DOT_PRODUCTS_IN_NEWTONS":
        raise DiagnosticError("TRACE_FORCE_CONVENTION", "Force columns must be signed dot products, never vector magnitudes.")
    raw_axis = projection["unit_axis"]
    if not isinstance(raw_axis, list) or len(raw_axis) != 3:
        raise DiagnosticError("TRACE_FORCE_AXIS_INVALID", "A force projection requires exactly three finite unit-axis components.")
    axis: list[float] = []
    for value in raw_axis:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise DiagnosticError("TRACE_FORCE_AXIS_INVALID", "Projection components must be finite numbers, not Boolean or text aliases.")
        try:
            number = float(value)
        except OverflowError as exc:
            raise DiagnosticError("TRACE_FORCE_AXIS_INVALID", "Projection component exceeds the finite numeric range.") from exc
        if not math.isfinite(number):
            raise DiagnosticError("TRACE_FORCE_AXIS_INVALID", "Projection components must be finite.")
        axis.append(number)
    if not math.isclose(math.hypot(*axis), 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise DiagnosticError("TRACE_FORCE_AXIS_INVALID", "Projection axis must already have unit length; silent normalization is forbidden.")
    return {"frame_id": frame_id, "unit_axis": axis, "convention": projection["convention"]}


def diagnose_request(payload: object) -> dict[str, object]:
    data = _object(payload, {"schema", "identity", "deck_text", "log_text", "requirements"}, {"iteration_csv", "iteration_identity"})
    if data["schema"] != "fea.nonlinear-diagnosis.v2":
        raise DiagnosticError("SCHEMA_MISMATCH", "Expected fea.nonlinear-diagnosis.v2.")
    identity = _object(data["identity"], {"model_id", "model_revision", "mesh_revision", "owner_id", "case_id", "frame_id",
                                               "solver_release_sku", "deck_sha256", "log_sha256"})
    if identity["solver_release_sku"] != RELEASE:
        raise DiagnosticError("UNSUPPORTED_RELEASE", "Control semantics are verified only for the exact Nastran2606 SKU.")
    for value in identity.values():
        _string(value)
    deck = parse_deck(_string(data["deck_text"]))
    log = parse_f06(_string(data["log_text"]))
    if deck.sha256 != identity["deck_sha256"] or log.sha256 != identity["log_sha256"]:
        raise DiagnosticError("ARTIFACT_HASH_MISMATCH", "Actual deck/log bytes differ from the declared case evidence.")
    if ("iteration_csv" in data) != ("iteration_identity" in data):
        raise DiagnosticError("TRACE_IDENTITY_REQUIRED", "Iteration interchange requires its separate source identity and hash.")
    force_projection: dict[str, object] | None = None
    if "iteration_identity" in data:
        trace_identity = _object(data["iteration_identity"], {"case_identity", "csv_sha256", "origin", "force_projection"})
        if trace_identity["case_identity"] != identity:
            raise DiagnosticError("TRACE_SOURCE_IDENTITY_MISMATCH", "Iteration evidence belongs to another model, mesh, frame, case or deck/log revision.")
        if trace_identity["origin"] not in {"MANUFACTURED_TEST_TRACE", "ADAPTER_EXPORT"}:
            raise DiagnosticError("TRACE_ORIGIN", "Identify manufactured data or an adapter export without claiming authentication.")
        if trace_identity["csv_sha256"] != hashlib.sha256(_string(data["iteration_csv"]).encode()).hexdigest():
            raise DiagnosticError("TRACE_HASH_MISMATCH", "Iteration CSV bytes differ from the source fingerprint.")
        force_projection = _force_projection(trace_identity["force_projection"], _string(identity["frame_id"]))
    requirements = _object(data["requirements"], {"contact_required", "preload_required", "required_load_subcases",
                                                    "max_force_balance_fraction", "force_balance_absolute_n", "max_artificial_energy_fraction"},
                           {"target_load_factors", "load_factor_tolerance"})
    if type(requirements["contact_required"]) is not bool or type(requirements["preload_required"]) is not bool:
        raise DiagnosticError("INVALID_REQUIREMENT", "Contact/preload requirements must be explicit booleans.")
    raw_required = requirements["required_load_subcases"]
    if not isinstance(raw_required, list) or any(type(v) is not int or v <= 0 for v in raw_required):
        raise DiagnosticError("INVALID_REQUIREMENT", "Required service-load subcases must be integer IDs.")
    required_load = {int(v) for v in raw_required}
    case_ids = {c.identifier for c in deck.subcases}
    if not required_load <= case_ids:
        raise DiagnosticError("UNKNOWN_REQUIRED_SUBCASE", "Requested subcases are absent from the effective deck.")
    balance_fraction = _positive(requirements["max_force_balance_fraction"])
    balance_absolute = _positive(requirements["force_balance_absolute_n"])
    energy_fraction = _positive(requirements["max_artificial_energy_fraction"])
    targets: dict[int, float] = {}
    target_tolerance = 0.0
    if ("target_load_factors" in requirements) != ("load_factor_tolerance" in requirements):
        raise DiagnosticError("TARGET_LOAD_POLICY", "Target load factors require an explicit comparison tolerance.")
    if "target_load_factors" in requirements:
        raw_targets = requirements["target_load_factors"]
        if not isinstance(raw_targets, dict) or not raw_targets:
            raise DiagnosticError("TARGET_LOAD_POLICY", "Target load factors must map subcase IDs to finite factors.")
        for key, value in raw_targets.items():
            sid = _integer(_string(key))
            if sid not in case_ids or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise DiagnosticError("TARGET_LOAD_POLICY", "A target must identify an existing subcase and a finite factor.")
            targets[sid] = float(value)
        target_tolerance = _positive(requirements["load_factor_tolerance"])
    controls = _controls(deck)
    findings: list[dict[str, object]] = []

    def add(code: str, severity: str, confidence: str, evidence: object, hypothesis: str,
            falsifier: str, document: str | None = None) -> None:
        findings.append({"code": code, "severity": severity, "confidence": confidence, "evidence": evidence,
                         "hypothesis": hypothesis, "discriminating_next_check": falsifier,
                         "document_id": DOCS.get(document) if document else None})

    if deck.unresolved_includes:
        add("UNRESOLVED_INCLUDE", "BLOCKER", "OBSERVED", list(deck.unresolved_includes),
            "The effective model/control data are incomplete.", "Resolve includes through the authorized artifact provider; rehash the expanded deck.")
    if deck.unreviewed_executive:
        add("EXECUTIVE_OPTIONS_UNREVIEWED", "REVIEW", "OBSERVED", list(deck.unreviewed_executive),
            "Executive options may alter control semantics.", "Review these exact source lines before treating case-control extraction as complete.")
    effective_controls: dict[int, dict[str, str]] = {}
    case_reports: list[dict[str, object]] = []
    previous_preload = False
    prior_cases: set[int] = set()
    for case in deck.subcases:
        selector = "NLPARM" if deck.solution == 106 else "NLCNTL"
        card = "NLPARM" if deck.solution == 106 else ("NLCNTL" if deck.solution == 401 else "NLCNTL2")
        selected = case.effective.get(selector)
        values: dict[str, str] = {}
        if selected is None:
            add("MISSING_NONLINEAR_CONTROL_SELECTION", "BLOCKER", "OBSERVED", {"subcase": case.identifier, "selector": selector},
                "The intended nonlinear iteration policy is not selected.", "Select and inspect the documented family-specific control ID.", selector + "_CASE")
        else:
            selected_id = _integer(selected)
            values = controls.get((card, selected_id), {})
            if not values:
                add("WRONG_OR_MISSING_NONLINEAR_CONTROL_CARD", "BLOCKER", "OBSERVED",
                    {"subcase": case.identifier, "selected_id": selected_id, "required_bulk_card": card},
                    "A control for another solution family or an absent set is selected.",
                    "Resolve this ID to the required Bulk Data card; do not rename a SOL401 card into a SOL402 control.", selector + "_CASE")
        effective_controls[case.identifier] = values
        analysis = case.effective.get("ANALYSIS", "STATICS" if deck.solution == 106 else "UNRESOLVED")
        dependent = case.effective.get("SEQDEP", "YES")
        if dependent not in {"YES", "NO"}:
            raise DiagnosticError("INVALID_SEQDEP", "SEQDEP must be YES or NO.")
        if deck.solution == 402 and dependent == "NO" and "RSUB" in values:
            restored_id = int(_real(values["RSUB"]))
            if restored_id > 0 and (restored_id not in prior_cases or restored_id >= case.identifier):
                raise DiagnosticError("INVALID_RESTART_SUBCASE", "A restored RSUB must identify an actual preceding subcase.")
        if deck.solution == 106 and "NLCNTL" in case.effective:
            add("CONTROL_FAMILY_MISMATCH", "BLOCKER", "OBSERVED", {"subcase": case.identifier},
                "SOL106 does not use the multistep NLCNTL selection.", "Audit the selected NLPARM policy and intended solver family.", "NLCNTL_CASE")
        if deck.solution in {401, 402} and "NLPARM" in case.effective:
            add("CONTROL_FAMILY_MISMATCH", "BLOCKER", "OBSERVED", {"subcase": case.identifier},
                "A SOL106 nonlinear control has been carried into a multistep solution.", "Inspect the NLCNTL selection and family-specific bulk entry.", "NLCNTL_CASE")
        if deck.solution == 401 and "BOLTLD" in case.effective and analysis != "PRELOAD":
            add("BOLT_LOAD_IN_SOL401_SERVICE_SUBCASE", "BLOCKER", "DOCUMENTED", {"subcase": case.identifier},
                "SOL401 rejects BOLTLD outside an ANALYSIS=PRELOAD subcase.", "Move actual pretension application into a preload subcase; retain its state via dependent service steps.", "PRELOAD401")
        if analysis == "PRELOAD":
            if "BOLTLD" not in case.effective:
                add("PRELOAD_SELECTION_MISSING", "BLOCKER", "OBSERVED", {"subcase": case.identifier},
                    "A preload step has no selected bolt loading.", "Verify the selected bolt set and its physical cut/axis membership.", "PRELOAD401" if deck.solution == 401 else "PRELOAD402")
            if "LOAD" in case.local or "DLOAD" in case.local:
                add("SERVICE_LOAD_DEFINED_IN_PRELOAD", "BLOCKER", "DOCUMENTED", {"subcase": case.identifier},
                    "Service loading was explicitly defined in a preload subcase.", "Review whether a previous dependent static load should be retained or a separate service step is intended.", "PRELOAD401" if deck.solution == 401 else "PRELOAD402")
            previous_preload = True
        elif previous_preload and dependent == "NO":
            restored = deck.solution == 402 and values.get("RSUB", "0") != "0"
            add("PRELOAD_STATE_RESET_REQUIRES_REVIEW" if restored else "PRELOAD_STATE_LOST", "REVIEW" if restored else "BLOCKER", "DOCUMENTED",
                {"subcase": case.identifier, "SEQDEP": dependent, "RSUB": values.get("RSUB")},
                "The service step does not inherit the preceding preloaded state automatically.",
                "Prove the actual restored subcase identity and retained bolt strain/contact state; compare zero-service bolt force and deformation.", "SEQDEP")
        if case.identifier in required_load and not ({"LOAD", "DLOAD"} & case.effective.keys()):
            add("REQUIRED_SERVICE_LOAD_NOT_SELECTED", "BLOCKER", "OBSERVED", {"subcase": case.identifier},
                "An intended service load is absent; sequential state inheritance does not retain every preceding static load selection.",
                "Compare effective per-subcase load resultants with the intended load history.", "PRELOAD401" if deck.solution == 401 else "PRELOAD402")
        if deck.solution == 106 and values.get("KMETHOD") == "ITER" and values.get("KSTEP") == "1" and "U" in values.get("CONV", ""):
            add("SOL106_DISPLACEMENT_CRITERION_SUBSTITUTED", "REVIEW", "DOCUMENTED", {"subcase": case.identifier},
                "Full Newton SOL106 substitutes work convergence for requested displacement convergence.",
                "Inspect actual EPSW and solver-reported active criteria before interpreting a U-only request.", "NLPARM")
        if deck.solution == 106 and values.get("MAXBIS") == "0" and _real(values.get("MAXDIV", "3")) > 0:
            add("BEST_ATTAINABLE_CONTINUATION_ENABLED", "REVIEW", "DOCUMENTED", {"subcase": case.identifier},
                "SOL106 can continue after a nonconverged increment when bisection is unavailable and MAXDIV is positive.",
                "Inspect every accepted increment's actual convergence and equilibrium; normal process completion is insufficient.", "NLPARM")
        if deck.solution == 402 and _real(values.get("PRDR", values.get("PRCR", "0.001"))) > _real(values.get("PRCR", "0.001")):
            add("RELAXED_FORCE_CONVERGENCE_ENABLED", "REVIEW", "DOCUMENTED", {"subcase": case.identifier, "PRCR": values.get("PRCR"), "PRDR": values.get("PRDR")},
                "A late iteration can use a looser force criterion.", "Compare the accepted final residual with the original project criterion and the relaxed solver criterion separately.", "NLCNTL2")
        case_reports.append({"subcase": case.identifier, "source_line": case.line, "analysis": analysis,
                             "effective_case_control": case.effective, "control_card": card,
                             "selected_control_id": selected, "explicit_control_parameters": values})
        prior_cases.add(case.identifier)
    if requirements["preload_required"] and not previous_preload:
        add("REQUIRED_PRELOAD_STEP_ABSENT", "BLOCKER", "OBSERVED", {}, "No preload step exists in the effective sequence.",
            "Reconstruct pretension application and lock state from the selected solver family before service loading.")
    for code, line in log.events:
        add(code, "REVIEW" if code.endswith("WARNING") else "BLOCKER", "OBSERVED", {"log_line": line},
            "The solver output reports a concrete model/solution defect.", "Inspect the cited bolt membership, cut plane and coordinate axis; do not hide it by increasing iteration limits.",
            "PRELOAD402" if code.startswith("BOLT_") else None)
    for summary in log.summaries:
        if summary.subcase is not None and summary.subcase not in case_ids:
            add("LOG_SUBCASE_NOT_IN_DECK", "BLOCKER", "OBSERVED", {"subcase": summary.subcase, "log_line": summary.line},
                "The log and deck may represent different cases.", "Reconcile actual submitted deck hash and job artifact ownership.")
    supported_summaries = log.summaries if deck.solution == 401 else ()
    if log.summaries and deck.solution != 401:
        add("SUMMARY_DIALECT_UNVERIFIED_FOR_SOLUTION", "REVIEW", "DOCUMENTED", {"solution": deck.solution},
            "The fetched EQU/CON/BLT summary semantics are specific to SOL401.",
            "Use the release-specific result adapter for this solver family; do not borrow another family's convergence table.", "ITERATION401")
    last_summary: dict[int | None, LogSummary] = {}
    for summary in supported_summaries:
        last_summary[summary.subcase] = summary
    if None in last_summary:
        add("UNBOUND_CONVERGENCE_SUBCASE", "REVIEW", "OBSERVED", {"log_line": last_summary[None].line},
            "A parsed convergence table has no bound subcase identity.", "Recover its subcase context from the exact log before comparing it with a result state.", "ITERATION401")
    for summary_sid, summary in last_summary.items():
        failures = []
        if summary.equilibrium is not True:
            failures.append("EQU")
        if requirements["contact_required"] and summary.contact is not True:
            failures.append("CON")
        if requirements["preload_required"] and summary.bolt is False:
            failures.append("BLT")
        if failures:
            add("INCOMPLETE_NONLINEAR_CONVERGENCE", "BLOCKER", "OBSERVED", {"subcase": summary_sid, "log_line": summary.line, "failed_or_missing": failures},
                "A converged equilibrium column does not prove contact or bolt convergence.",
                "Check the final accepted increment and every applicable EQU/CON/BLT summary, including contact relative displacement.", "ITERATION401")
    trace: list[dict[str, float | int | bool]] = []
    target_checks: list[dict[str, object]] = []
    checked_claims = 0
    if "iteration_csv" in data:
        if force_projection is None:
            raise DiagnosticError("TRACE_FORCE_PROJECTION_REQUIRED", "Signed force columns require a frame-bound projection contract.")
        trace = _trace(_string(data["iteration_csv"]))
        if any(int(row["subcase"]) not in case_ids for row in trace):
            raise DiagnosticError("TRACE_SUBCASE_MISMATCH", "Iteration evidence references a subcase absent from the deck.")
        summaries, conflicting_states = _align_trace(trace, supported_summaries, add)
        checked_claims = _diagnose_trace(trace, deck.solution, effective_controls, summaries, requirements,
                                         balance_fraction, balance_absolute, energy_fraction, force_projection,
                                         not deck.unreviewed_executive, add)
        target_checks = _check_targets(trace, targets, target_tolerance, deck.solution, requirements,
                                       last_summary, summaries, conflicting_states, add)
    if not supported_summaries:
        add("CONVERGENCE_TABLE_NOT_PARSED", "REVIEW", "OBSERVED", {"unrecognized_lines": log.unknown_nonempty_lines},
            "This bounded parser did not establish final solver convergence.", "Supply a supported aligned summary or a qualified artifact adapter; absence of a fatal string is not convergence proof.")
    if targets and not trace:
        add("TARGET_STATE_EVIDENCE_MISSING", "REVIEW", "OBSERVED", {"subcases": sorted(targets)},
            "Required final load states have no iteration/result evidence.", "Acquire the exact accepted target-state observations before reporting completion.")
        target_checks = [{"subcase": sid, "target_load_factor": target, "status": "INCOMPLETE",
                          "latest_trace_state": None, "aligned_log_line": None,
                          "reason_codes": ["TARGET_STATE_EVIDENCE_MISSING"]} for sid, target in targets.items()]
    severities = {"BLOCKER": 0, "REVIEW": 1, "HYPOTHESIS": 2}
    findings.sort(key=lambda f: (severities[str(f["severity"])], str(f["code"])))
    for rank, item in enumerate(findings, 1):
        item["rank"] = rank
    return {"schema": "fea.nonlinear-diagnosis-report.v2", "identity": identity, "solution": deck.solution,
            "status": "SOURCE_CHECKS_FAIL" if any(f["severity"] == "BLOCKER" for f in findings) else "INVESTIGATION_READY",
            "findings": findings, "effective_subcases": case_reports, "parsed_bulk_card_count": len(deck.records),
            "target_state_checks": target_checks,
            "review_required": any(f["severity"] in {"REVIEW", "HYPOTHESIS"} for f in findings),
            "opaque_model_card_names": sorted({r.name for r in deck.records} - {"NLPARM", "NLCNTL", "NLCNTL2"}),
            "log_summary_count": len(log.summaries), "iteration_observation_count": len(trace),
            "force_balance": {"scope": "ONE_DECLARED_SIGNED_COMPONENT" if checked_claims else "NOT_ASSESSED",
                              "evaluated_claimed_states": checked_claims,
                              "projection": force_projection, "full_vector_assessed": False, "moment_balance_assessed": False},
            "summary_format_documented_for_solution": 401,
            "iteration_csv_sha256": hashlib.sha256(str(data["iteration_csv"]).encode()).hexdigest() if "iteration_csv" in data else None,
            "native_status": "NOT_RUN", "solver_status": "NOT_RUN", "engineering_status": "NOT_RUN",
            "engineering_accepted": False, "source_authentication": "UNVERIFIED_CALLER_SOURCE",
            "parser_scope": "CONTROL_SELECTION_AND_BOUNDED_F06_DIAGNOSTICS_NOT_GENERAL_DECK_VALIDATION",
            "iteration_format": "FEA_OWNED_INTERCHANGE_NOT_NATIVE_F06", "source_documents": DOCS}


# Callable signature is explicit to keep diagnostic rendering out of numerical checks.
AddFinding = Callable[[str, str, str, object, str, str, str | None], None]


def _align_trace(trace: list[dict[str, float | int | bool]], summaries: tuple[LogSummary, ...],
                 add: AddFinding) -> tuple[dict[tuple[int | None, int], LogSummary], set[tuple[int | None, int]]]:
    """Reconcile identity before borrowing a log row's convergence flags.

    Repeated identical printout is harmless. Conflicting rows or iteration
    counters cannot be disambiguated by accepting the last occurrence.
    """
    indexed: dict[tuple[int | None, int], LogSummary] = {}
    conflicts: set[tuple[int | None, int]] = set()
    for summary in summaries:
        key = (summary.subcase, summary.accumulated_iteration)
        old = indexed.get(key)
        if old and (old.current_iteration, old.equilibrium, old.contact, old.bolt) != (
                summary.current_iteration, summary.equilibrium, summary.contact, summary.bolt):
            conflicts.add(key)
            add("CONFLICTING_CONVERGENCE_SUMMARY", "BLOCKER", "OBSERVED",
                {"subcase": key[0], "accumulated_iteration": key[1], "log_lines": [old.line, summary.line]},
                "The same solver iteration has incompatible summary records.",
                "Separate restart/run artifacts and recover the unique accepted result-state identity.", "ITERATION401")
        indexed[key] = summary
    for row in trace:
        key = (int(row["subcase"]), int(row["accumulated_iteration"]))
        observation_summary = indexed.get(key)
        if observation_summary and observation_summary.current_iteration != int(row["iteration"]):
            conflicts.add(key)
            add("TRACE_LOG_ITERATION_IDENTITY_MISMATCH", "BLOCKER", "OBSERVED",
                {"subcase": key[0], "accumulated_iteration": key[1], "trace_iteration": row["iteration"],
                 "log_iteration": observation_summary.current_iteration, "log_line": observation_summary.line},
                "Matching accumulated counters conceal different current iteration identities.",
                "Re-export the same subcase, increment attempt and result state; do not reuse this log convergence flag.", "ITERATION401")
    return {key: summary for key, summary in indexed.items() if key not in conflicts}, conflicts


def _check_targets(trace: list[dict[str, float | int | bool]], targets: dict[int, float], tolerance: float,
                   solution: int, requirements: dict[str, object], last_summary: dict[int | None, LogSummary],
                   aligned: dict[tuple[int | None, int], LogSummary], conflicts: set[tuple[int | None, int]],
                   add: AddFinding) -> list[dict[str, object]]:
    """Check the latest observed state; an earlier achieved target is not final.

    SOURCE_TARGET_ALIGNED means only that these source artifacts identify the
    same claimed-converged target. Independent physical/control findings still
    apply; neither these bytes nor their matching counters authenticate a run.
    """
    checks: list[dict[str, object]] = []
    for sid, target in targets.items():
        rows = [row for row in trace if int(row["subcase"]) == sid]
        reasons: list[str] = []
        rejected = False
        last = rows[-1] if rows else None
        summary = None if last is None else aligned.get((sid, int(last["accumulated_iteration"])))
        if last is None:
            reasons.append("TARGET_STATE_EVIDENCE_MISSING")
            add(reasons[-1], "REVIEW", "OBSERVED", {"subcase": sid, "target_load_factor": target},
                "No observed final state exists for a required target subcase.",
                "Obtain the actual accepted result-step record for this target.", None)
        else:
            if abs(float(last["load_factor"]) - target) > tolerance:
                rejected = True
                reasons.append("TARGET_LOAD_NOT_REACHED")
                add(reasons[-1], "BLOCKER", "COMPUTED",
                    {"subcase": sid, "observed_load_factor": last["load_factor"], "target_load_factor": target},
                    "The latest observed state is not the requested final load state.",
                    "Reconcile stopping/restart conditions and inspect the accepted result at the intended target factor.", None)
                if any(bool(row["claimed_converged"]) and abs(float(row["load_factor"]) - target) <= tolerance for row in rows[:-1]):
                    reasons.append("TARGET_STATE_ROLLED_BACK")
                    add(reasons[-1], "BLOCKER", "OBSERVED", {"subcase": sid, "latest_accumulated_iteration": last["accumulated_iteration"]},
                        "An earlier claimed-converged target was followed by a different observed load state.",
                        "Resolve whether this is rollback, unloading or a mixed restart; bind the requested final result explicitly.", None)
            if not bool(last["claimed_converged"]):
                rejected = True
                reasons.append("TARGET_STATE_NOT_CONVERGED")
                add(reasons[-1], "BLOCKER", "OBSERVED",
                    {"subcase": sid, "increment": last["increment"], "accumulated_iteration": last["accumulated_iteration"]},
                    "The latest target observation explicitly does not claim convergence.",
                    "Recover the accepted final increment or diagnose the unfinished increment; an earlier successful row cannot complete it.", None)
            key = (sid, int(last["accumulated_iteration"]))
            if key in conflicts:
                rejected = True
                reasons.append("TARGET_STATE_IDENTITY_CONFLICT")
            elif solution != 401:
                reasons.append("TARGET_SUMMARY_DIALECT_UNVERIFIED")
            elif summary is None:
                reasons.append("TARGET_CONVERGENCE_SUMMARY_MISSING")
                add(reasons[-1], "REVIEW", "OBSERVED", {"subcase": sid, "accumulated_iteration": key[1]},
                    "No supported solver summary corroborates this exact target iteration.",
                    "Obtain the same subcase/current/accumulated-iteration summary; do not substitute another step's success.", "ITERATION401")
            elif last_summary.get(sid) != summary:
                reasons.append("TARGET_LOG_TRACE_STATE_MISMATCH")
                add(reasons[-1], "REVIEW", "OBSERVED", {"subcase": sid, "trace_accumulated_iteration": key[1],
                                                       "latest_log_line": last_summary[sid].line},
                    "The final log summary and final exported observation represent different solver states.",
                    "Reconcile the latest accepted state across both artifacts before declaring the target complete.", "ITERATION401")
            if summary and (summary.equilibrium is not True
                            or (requirements["contact_required"] and summary.contact is not True)
                            or (requirements["preload_required"] and summary.bolt is False)):
                rejected = True
                reasons.append("TARGET_CONVERGENCE_CONTRADICTED")
        checks.append({"subcase": sid, "target_load_factor": target,
                       "status": "REJECTED" if rejected else ("INCOMPLETE" if reasons else "SOURCE_TARGET_ALIGNED"),
                       "latest_trace_state": None if last is None else {key: last[key] for key in (
                           "increment", "iteration", "accumulated_iteration", "load_factor", "claimed_converged")},
                       "aligned_log_line": summary.line if summary else None, "reason_codes": reasons})
    return checks


def _diagnose_trace(trace: list[dict[str, float | int | bool]], solution: int,
                    controls: dict[int, dict[str, str]], log_by_iteration: dict[tuple[int | None, int], LogSummary], requirements: dict[str, object],
                    balance_fraction: float, balance_absolute: float, energy_fraction: float,
                    force_projection: dict[str, object], executive_resolved: bool, add: AddFinding) -> int:
    groups: dict[tuple[int, int], list[dict[str, float | int | bool]]] = {}
    for row in trace:
        groups.setdefault((int(row["subcase"]), int(row["increment"])), []).append(row)
    checked_claims = 0
    for (sid, increment), rows in groups.items():
        last = rows[-1]
        values = controls[sid]
        if bool(last["claimed_converged"]):
            checked_claims += 1
            summary = log_by_iteration.get((sid, int(last["accumulated_iteration"])))
            if summary and (summary.equilibrium is False or (requirements["contact_required"] and summary.contact is not True) or summary.bolt is False):
                add("CONVERGENCE_CLAIM_CONTRADICTS_LOG", "BLOCKER", "OBSERVED", {"subcase": sid, "increment": increment, "log_line": summary.line},
                    "The imported convergence claim conflicts with the corresponding solver summary.", "Discard this claimed state and reconcile the actual accepted increment.", "ITERATION401")
            force_key, work_key = ("PRCR", "PRCE") if solution == 402 else ("EPSP", "EPSW")
            active = values.get("CONV", "")
            if solution == 401 and requirements["contact_required"]:
                active = "UP" if executive_resolved else ""
            if solution == 106 and values.get("KMETHOD") == "ITER" and values.get("KSTEP") == "1":
                active = active.replace("U", "W")
            if solution == 402:
                # The bounded fetched pages do not establish every acceptance
                # branch; do not invent an AND/OR rule for PRCR and PRCE.
                # Independent force and energy checks below still apply.
                active = ""
            for flag, parameter, column in (("P", force_key, "force_error"), ("U", "EPSU", "displacement_error"), ("W", work_key, "work_error")):
                if flag in active and parameter in values and float(last[column]) > _real(values[parameter]):
                    add("CLAIMED_CONVERGED_ABOVE_EXPLICIT_TOLERANCE", "BLOCKER", "OBSERVED",
                        {"subcase": sid, "increment": increment, "criterion": flag, "observed": last[column], "explicit_limit": values[parameter]},
                        "A reported converged state violates an explicitly selected convergence requirement.",
                        "Reconcile active versus relaxed criteria and inspect the exact accepted result step.", "NLCNTL2" if solution == 402 else ("NLPARM" if solution == 106 else "NLCNTL"))
            external, reaction = float(last["external_force_n"]), float(last["reaction_force_n"])
            defect = abs(external + reaction)
            force_scale = max(abs(external), abs(reaction))
            allowed_defect = balance_absolute + balance_fraction * force_scale
            if defect > allowed_defect:
                add("FALSE_CONVERGENCE_FORCE_BALANCE", "BLOCKER", "COMPUTED",
                    {"subcase": sid, "increment": increment, "defect_n": defect, "allowed_defect_n": allowed_defect,
                     "external_force_n": external, "reaction_force_n": reaction, "force_projection": force_projection},
                    "Signed force balance along the declared frame-bound axis fails independently of the convergence label.",
                    "Audit every relevant external resultant on the same declared axis and exact step. This check establishes neither full 3D force nor moment balance.", None)
            artificial, strain = float(last["artificial_energy_j"]), float(last["strain_energy_j"])
            if artificial > energy_fraction * strain:
                add("ARTIFICIAL_ENERGY_DOMINATES_ACCEPTANCE_BUDGET", "BLOCKER", "COMPUTED",
                    {"subcase": sid, "increment": increment, "artificial_energy_j": artificial, "strain_energy_j": strain},
                    "Numerical stabilization contributes more energy than the project allows.",
                    "Repeat with reduced stabilization while preserving physical constraints and load path; compare QoI and energy fractions.", None)
        if len(rows) >= 3:
            first = rows[0]
            first_norm, last_norm = float(first["residual_norm_n"]), float(last["residual_norm_n"])
            reduction = last_norm / first_norm if first_norm > 0 else (1.0 if last_norm == 0 else math.inf)
            changes = max(float(r["contact_change_fraction"]) for r in rows)
            if changes >= 0.2 and reduction >= 0.5:
                add("CONTACT_CHATTER_OR_EXCESSIVE_INCREMENT", "HYPOTHESIS", "INFERRED",
                    {"subcase": sid, "increment": increment, "maximum_contact_change_fraction": changes, "residual_reduction": reduction if math.isfinite(reduction) else None},
                    "Large active-set changes accompany poor residual reduction; penalty stiffness or load increments may be too aggressive.",
                    "Halve the increment at fixed contact parameters, then vary penalty at fixed increment; compare contact states, penetration and QoI to discriminate causes.", "CONTACT401" if solution == 401 else None)
            if float(last["penetration_ratio"]) > 1 and reduction < 0.2:
                add("PENETRATION_PERSISTS_AFTER_EQUILIBRIUM_IMPROVES", "HYPOTHESIS", "INFERRED",
                    {"subcase": sid, "increment": increment, "penetration_ratio": last["penetration_ratio"]},
                    "Contact enforcement remains insufficient although global residual improves.",
                    "Inspect local penetration scales and contact normals; change penalty independently and verify force/energy/QoI sensitivity.", "CONTACT401" if solution == 401 else None)
            if float(first["contact_closed_count"]) > 0 and float(last["contact_closed_count"]) < 0.5 * float(first["contact_closed_count"]) and reduction > 1:
                add("CONTACT_LOAD_PATH_LOSS", "HYPOTHESIS", "INFERRED",
                    {"subcase": sid, "increment": increment, "closed_before": first["contact_closed_count"], "closed_after": last["contact_closed_count"]},
                    "Loss of most active contact accompanies a growing residual.",
                    "Inspect the emerging rigid motion, retained pretension and interface orientation before adding numerical stiffness.", "CONTACT401" if solution == 401 else None)
    return checked_claims
