#!/usr/bin/env python3
"""Read-only inventory of a scoped Nastran text deck; not a solver input validator."""

import argparse
from collections import Counter
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import stat


class DeckError(ValueError):
    """Malformed, unresolved, or unsupported deck syntax."""


@dataclass(frozen=True)
class Source:
    file: str
    line: int

    def error(self, detail):
        return DeckError(f"{self.file}:{self.line}: {detail}")

    def summary(self):
        return {"file": self.file, "line": self.line}


@dataclass(frozen=True)
class Card:
    name: str
    fields: tuple[str, ...]
    source: Source

    def at(self, n):
        return self.fields[n - 1] if n <= len(self.fields) else ""

    def summary(self):
        return {"name": self.name, "fields": self.fields, **self.source.summary()}


@dataclass(frozen=True)
class Control:
    value: str
    options: tuple[str, ...]
    source: Source

    def summary(self):
        return {"value": self.value, "options": self.options, **self.source.summary()}


@dataclass
class Deck:
    entry: str
    solution: int = 0
    global_control: dict[str, Control] = field(default_factory=dict)
    subcases: dict[int, dict[str, Control]] = field(default_factory=dict)
    cards: list[Card] = field(default_factory=list)
    files: dict[str, dict] = field(default_factory=dict)
    includes: list[dict] = field(default_factory=list)
    enddata_suffix: str | None = None

    def effective(self):
        if not self.subcases:
            return {None: self.global_control.copy()}
        return {sid: self.global_control | local for sid, local in self.subcases.items()}

    def summary(self, show_cards=False):
        summary = {
            "status": "TEXT_INVENTORIED",
            "entry": self.entry,
            "sol": self.solution,
            "files": self.files,
            "includes": self.includes,
            "enddata_suffix": self.enddata_suffix,
            "global_control": {key: item.summary() for key, item in self.global_control.items()},
            "subcases": [
                {"id": sid, "effective": {key: item.summary() for key, item in effective.items()}}
                for sid, effective in self.effective().items()
            ],
            "bulk_counts": dict(sorted(Counter(card.name for card in self.cards).items())),
        }
        if show_cards:
            summary["cards"] = [card.summary() for card in self.cards]
        return summary


INCLUDE = re.compile(r""" *INCLUDE +(?:'([^']+)'|"([^"]+)") *(?:\$.*)?""", re.I)
WINDOWS_DEVICE = re.compile(r"(?:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\..*)?", re.I)
HASH = re.compile(r"[0-9a-f]{64}", re.I)
MAX_BYTES = 64 * 1024 * 1024
MAX_EXPANDED_BYTES = 128 * 1024 * 1024
MAX_INCLUDE_DEPTH = 32


class Closure:
    def __init__(self, root, deck, allow_includes, expected_hashes):
        self.root = root
        self.deck = deck
        self.allow_includes = allow_includes
        self.expected = expected_hashes
        if self.expected is not None and (
            not isinstance(self.expected, dict)
            or any(not isinstance(path, str) or not isinstance(sha, str) or not HASH.fullmatch(sha)
                   for path, sha in self.expected.items())
        ):
            raise DeckError("expected closure must be an object mapping relative paths to SHA-256")
        self.snapshots = {}
        self.expanded_bytes = 0

    def target(self, parent, filename, source):
        parts = re.split(r"[/\\]", filename)
        if (
            PureWindowsPath(filename).anchor
            or any(not part or part != part.strip() or re.search(r'[:$%*?<>|"\x00-\x1f]', part)
                   or WINDOWS_DEVICE.fullmatch(part)
                   or (part not in {".", ".."} and part.endswith(".")) for part in parts)
        ):
            raise source.error("unsupported INCLUDE path; use a literal relative filename")
        target = parent
        for index, part in enumerate(parts):
            if part == "..":
                if target == self.root:
                    raise source.error("INCLUDE escapes the authorized root")
                target = target.parent
            elif part != ".":
                target = target / part
                resolved = target.resolve()
                if resolved != target:
                    raise source.error("INCLUDE aliases or escapes the authorized root")
                target = resolved
                if index + 1 < len(parts) and not target.is_dir():
                    raise source.error("unresolved INCLUDE path")
        return target

    def lines(self, path, stack=(), via=None):
        name = path.relative_to(self.root).as_posix()
        source = via or Source(name, 1)
        if path in stack:
            raise source.error(f"cyclic INCLUDE of {name}")
        if len(stack) > MAX_INCLUDE_DEPTH:
            raise source.error("INCLUDE nesting exceeds the supported depth")
        if path not in self.snapshots:
            if self.expected is not None and name not in self.expected:
                raise source.error(f"{name} is absent from the expected closure")
            try:
                if not stat.S_ISREG(path.stat().st_mode):
                    raise source.error(f"{name} is not a regular file")
                with path.open("rb") as stream:
                    raw = stream.read(MAX_BYTES + 1)
            except OSError as exc:
                raise source.error(f"cannot read {name}: {exc.strerror}") from exc
            if len(raw) > MAX_BYTES:
                raise source.error(f"{name} exceeds the supported text file size")
            sha = hashlib.sha256(raw).hexdigest()
            if self.expected is not None and sha != self.expected[name].lower():
                raise source.error(f"SHA-256 mismatch for {name}")
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise source.error(f"{name} is not supported UTF-8 deck text") from exc
            if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", text):
                raise source.error(f"{name} contains non-text control characters")
            self.deck.files[name] = {"sha256": sha, "bytes": len(raw)}
            self.snapshots[path] = text

        self.expanded_bytes += self.deck.files[name]["bytes"]
        if self.expanded_bytes > MAX_EXPANDED_BYTES:
            raise source.error("expanded INCLUDE closure exceeds the supported size")
        for number, line in enumerate(re.split(r"\r\n|\n|\r", self.snapshots[path]), 1):
            source = Source(name, number)
            if re.match(r"\s*INCLUDE\b", line, re.I):
                match = INCLUDE.fullmatch(line)
                if not match:
                    raise source.error("unsupported INCLUDE syntax; use one quoted relative path")
                if not self.allow_includes:
                    raise source.error("INCLUDE requires an explicit authorized root")
                yield source, None  # Flush a bulk card before traversing an INCLUDE.
                target = self.target(path.parent, match[1] or match[2], source)
                self.deck.includes.append({**source.summary(), "target": target.relative_to(self.root).as_posix()})
                yield from self.lines(target, (*stack, path), source)
                yield source, None
            else:
                text = line.partition("$")[0].rstrip(" ")
                if text.strip():
                    if "\t" in text or not text.isascii():
                        raise source.error("active deck records require ASCII without tabs")
                    yield source, text


CARD_NAME = re.compile(r"[A-Z][A-Z0-9]{0,7}")
CONTINUATION = re.compile(r"[+*][A-Z0-9_]{0,7}")
BULK_DIRECTIVES = {
    "ALTER", "BEGIN", "CEND", "DO", "ELSE", "ELSEIF", "END", "ENDDO", "ENDIF",
    "IF", "INCLUDE", "SOL", "SUBCASE",
}


def _bulk_record(text, source):
    free = "," in text
    parts = text.split(",") if free else None
    head = (parts[0] if parts is not None else text[:8]).strip().upper()
    large = head.startswith("*") or head.endswith("*")
    width = 16 if large else 8
    capacity = 64 // width
    marker = ""
    if parts is not None:
        values = parts[1:]
        if len(values) == capacity + 1:
            marker = values.pop().strip().upper()
        if len(values) > capacity:
            raise source.error("unsupported free-field record width")
    else:
        values = [text[i:i + width] for i in range(8, 72, width)]
        marker = text[72:80].strip().upper()
        if text[80:].strip():
            raise source.error("unexpected fixed-field text after column 80")
    if marker and not CONTINUATION.fullmatch(marker):
        raise source.error("unsupported continuation marker or excess free fields")
    values = tuple(value.strip() for value in values)
    fields = values + ("",) * (capacity - len(values))
    return head, (free, large), fields, marker


class Bulk:
    def __init__(self, cards):
        self.cards = cards
        self.pending = None
        self.fields = []
        self.layout = None
        self.marker = ""

    def flush(self):
        if self.pending is None:
            return
        name, source = self.pending
        if self.marker:
            raise source.error(f"missing continuation for {name} ({self.marker})")
        while self.fields and not self.fields[-1]:
            self.fields.pop()
        self.cards.append(Card(name, tuple(self.fields), source))
        self.pending = None

    def add(self, source, text):
        head, layout, fields, marker = _bulk_record(text, source)
        if not head or CONTINUATION.fullmatch(head):
            if self.pending is None or layout != self.layout:
                raise source.error("orphaned or mixed-format bulk continuation")
            if head[1:] != self.marker[1:]:
                raise source.error("bulk continuation ID does not match the previous record")
            self.fields.extend(fields)
        else:
            self.flush()
            name = head.removesuffix("*")
            if not CARD_NAME.fullmatch(name) or name in BULK_DIRECTIVES or name == "ENDDATA":
                raise source.error("unsupported bulk record or directive")
            self.pending = (name, source)
            self.fields = list(fields)
            self.layout = layout
        self.marker = marker


CASE_ASSIGNMENT = re.compile(r"([A-Z][A-Z0-9]*)(?:\s*\(([^()]*)\))?\s*=\s*(.+)", re.I)
TEXT_CONTROL = {"TITLE", "SUBTITLE", "LABEL"}
OUTPUT_CONTROL = {
    "DISPLACEMENT", "SPCFORCES", "MPCFORCES", "STRESS", "STRAIN", "FORCE",
    "OLOAD", "GPFORCE", "ACCELERATION", "VELOCITY", "ESE",
}
SELECTORS = {
    "METHOD", "CMETHOD", "SPC", "MPC", "LOAD", "DLOAD", "STATSUB", "TEMPERATURE",
    "SUPORT1", "TSTEP", "TSTEPNL", "NLPARM", "IC", "BOLTLD", "BCSET", "FREQUENCY",
}
PROFILE_SOLIDS = {"CTETRA", "CPENTA", "CPYRAM", "CHEXA"}
PROFILE_DEFINITIONS = {
    "GRID", "PSOLID", "MAT1", "MATT1", "TABLEM1", "EIGRL", "PARAM",
    # These set definitions are not selected implicitly in the supported profile.
    "SPC", "SPC1", "SPCADD", "MPC", "MPCADD", "LOAD", "FORCE", "FORCE1", "FORCE2",
    "MOMENT", "MOMENT1", "MOMENT2", "GRAV", "PLOAD", "PLOAD2", "PLOAD4", "TEMP", "TEMPD",
}
POSITIVE_INT = re.compile(r"[1-9][0-9]{0,8}")
ENDDATA = re.compile(r"ENDDATA(?: +([0-9A-F]{8}))?", re.I)


def _case_control(source, text):
    if text.upper() == "OUTPUT":
        return "OUTPUT", Control("", (), source)
    if match := re.fullmatch(r"SET +([1-9][0-9]{0,8}) *= *([0-9A-Z ,]+)", text, re.I):
        return f"SET {match[1]}", Control(match[2], (), source)
    match = CASE_ASSIGNMENT.fullmatch(text)
    if not match:
        raise source.error("unsupported Case Control record")
    name = match[1].upper()
    value = match[3].strip()
    options = tuple(option.strip().upper() for option in match[2].split(",")) if match[2] is not None else ()
    if not value or ";" in value or any(not re.fullmatch(r"[A-Z0-9]+", option) for option in options):
        raise source.error("unsupported Case Control value or option")
    if name in SELECTORS:
        if not POSITIVE_INT.fullmatch(value) and value.upper() not in {"NONE", "ALL"}:
            raise source.error(f"unsupported {name} selector")
    elif name in OUTPUT_CONTROL:
        if not POSITIVE_INT.fullmatch(value) and value.upper() not in {"NONE", "ALL"}:
            raise source.error(f"unsupported {name} output selector")
    elif name == "ECHO":
        if value.upper() not in {"NONE", "SORT", "UNSORT", "BOTH"}:
            raise source.error("unsupported ECHO value")
    elif name not in TEXT_CONTROL:
        raise source.error(f"unsupported Case Control keyword {name}")
    if options and name not in OUTPUT_CONTROL | {"STATSUB", "TEMPERATURE"}:
        raise source.error(f"unsupported options on {name}")
    key = f"{name}({','.join(options)})" if options and name in SELECTORS else name
    return key, Control(value, options, source)


def _deck_closure(path, root, expected_hashes):
    try:
        entry = Path(path).resolve(strict=True)
        scope = Path(root).resolve(strict=True) if root is not None else entry.parent
    except (OSError, RuntimeError) as exc:
        raise DeckError(f"cannot resolve deck or root: {exc}") from exc
    if not scope.is_dir() or not entry.is_relative_to(scope):
        raise DeckError("entry deck is outside the authorized directory")
    deck = Deck(entry.relative_to(scope).as_posix())
    return entry, deck, Closure(scope, deck, root is not None, expected_hashes)


def _verify_closure(deck, expected_hashes):
    if expected_hashes is not None and deck.files.keys() != expected_hashes.keys():
        raise DeckError("expected hashes contain files outside the effective INCLUDE closure")


def read_deck(path, *, root=None, expected_hashes=None):
    """Parse one complete deck from a hashed snapshot of its authorized text closure."""
    entry, deck, closure = _deck_closure(path, root, expected_hashes)
    bulk = Bulk(deck.cards)
    phase = "executive"
    control = deck.global_control
    for source, text in closure.lines(entry):
        if phase == "end":
            raise source.error("active text after ENDDATA")
        if text is None:
            bulk.flush()
            continue
        stripped = text.strip()
        upper = stripped.upper()
        if phase == "executive":
            if upper == "CEND" and source.file == deck.entry and deck.solution:
                phase = "case"
            elif match := re.fullmatch(r"SOL +([1-9][0-9]{0,3})", upper):
                if deck.solution:
                    raise source.error("duplicate Executive SOL")
                deck.solution = int(match[1])
            elif not re.fullmatch(r"ID *,? *[A-Z0-9_., /\\-]+|TIME +[1-9][0-9]*(?: *, *[0-9]+)?", upper):
                raise source.error("unsupported Executive Control record or missing SOL")
        elif phase == "case":
            if re.fullmatch(r"BEGIN +BULK", upper) and source.file == deck.entry:
                phase = "bulk"
            elif match := re.fullmatch(r"SUBCASE +([1-9][0-9]{0,8})", upper):
                sid = int(match[1])
                if sid in deck.subcases:
                    raise source.error("duplicate SUBCASE ID")
                control = deck.subcases[sid] = {}
            else:
                key, item = _case_control(source, stripped)
                if key in control:
                    raise source.error(f"duplicate {key} in the same Case Control scope")
                control[key] = item
        elif match := ENDDATA.fullmatch(stripped):
            if source.file != deck.entry:
                raise source.error("ENDDATA belongs in the entry deck")
            bulk.flush()
            deck.enddata_suffix = match[1]
            phase = "end"
        else:
            bulk.add(source, text)
    if phase != "end":
        raise DeckError(f"{deck.entry}: incomplete text deck; require SOL, CEND, BEGIN BULK and ENDDATA")
    _verify_closure(deck, expected_hashes)
    return deck


def observe_deck(path, *, root=None, expected_hashes=None):
    """Locate advanced records without interpreting effective sets or admitting a job."""
    entry, deck, closure = _deck_closure(path, root, expected_hashes)
    records = []
    counts = Counter()
    phase = "executive"
    subcase = None
    pending = None
    for source, text in closure.lines(entry):
        if text is None:
            pending = None
            continue
        upper = text.strip().upper()
        if phase == "bulk" and not re.match(r"^(BEGIN|ENDDATA)\b", upper):
            head = (text.split(",", 1)[0] if "," in text else text[:8]).strip().upper()
            if CARD_NAME.fullmatch(head.removesuffix("*")):
                counts[head.removesuffix("*")] += 1
            continue
        item = {**source.summary(), "phase": phase, "record": text.strip()}
        if phase == "executive":
            if re.match(r"^(ASSIGN|INCLUDE|ALTER|NASTRAN|DBSET)\b", upper):
                item["resolution"] = "NOT_RESOLVED"
            if upper == "CEND" and source.file == deck.entry:
                phase = "case"
        elif phase == "case":
            if match := re.fullmatch(r"SUBCASE +([1-9][0-9]{0,8})", upper):
                subcase = int(match[1])
                pending = None
            item["subcase"] = subcase
            if re.fullmatch(r"BEGIN +BULK", upper) and source.file == deck.entry:
                phase = "bulk"
            elif pending is not None and re.match(r"^[0-9 ,]", upper):
                item["possible_continuation_of"] = pending
            pending = source.summary() if upper.endswith(",") else None
        elif ENDDATA.fullmatch(upper) and source.file == deck.entry:
            phase = "end"
        records.append(item)
    _verify_closure(deck, expected_hashes)
    return {
        "status": "RECORDS_OBSERVED",
        "effective_sets": "UNVERIFIED",
        "entry": deck.entry,
        "boundary_markers_seen": phase == "end",
        "files": deck.files,
        "includes": deck.includes,
        "records": records,
        "bulk_head_counts": dict(sorted(counts.items())),
    }


PROFILE_PARAMS = {
    "OIBULK": {"YES", "NO"}, "OMACHPR": {"YES", "NO"},
    "POST": {"-2", "-1", "0"}, "POSTEXT": {"YES", "NO"}, "AUTOSPC": {"NO"},
}
REAL_DISPLACEMENT_OPTIONS = {"SORT1", "SORT2", "PRINT", "PLOT", "PUNCH", "REAL"}
MANUAL_REVIEW = [
    "Verify element-to-grid connectivity, a single connected body, and element quality.",
    "Resolve property/material assignments, material constants and density, mass and units.",
    "Verify run-time overrides, solver singularity elimination and the solved rigid-body modes.",
]


def free_free_profile(deck, *, expected_nd=None):
    """Report a narrow text-profile match, not a physical free-free acceptance decision."""
    issues = []
    methods = []
    eigrl = {}
    seen_params = set()
    names = {card.name for card in deck.cards}
    if deck.solution != 103:
        issues.append("requires Executive SOL 103")
    if not names & PROFILE_SOLIDS or not {"GRID", "PSOLID", "MAT1"} <= names:
        issues.append("requires structural continuum solid elements, GRID, PSOLID and MAT1")

    def reject(item, detail):
        issues.append(str(item.source.error(detail)))

    for card in deck.cards:
        if card.name not in PROFILE_SOLIDS | PROFILE_DEFINITIONS:
            reject(card, f"{card.name} is outside the standalone solid profile")
        elif card.name == "GRID":
            if card.at(7):
                reject(card, "GRID PS is not blank (permanent constraint)")
            if card.at(2) not in {"", "0"} or card.at(6) not in {"", "0"}:
                reject(card, "GRID CP/CD must use the basic frame")
            if card.at(8) not in {"", "0"} or len(card.fields) > 8:
                reject(card, "unsupported GRID SEID or fields beyond SEID")
        elif card.name == "PSOLID":
            if card.at(7).upper() not in {"", "SMECH"} or len(card.fields) > 7:
                reject(card, "PSOLID must use structural mechanics (SMECH or blank)")
        elif card.name == "EIGRL":
            sid = card.at(1)
            if not POSITIVE_INT.fullmatch(sid) or sid in eigrl:
                reject(card, "invalid or duplicate EIGRL ID")
            else:
                eigrl[sid] = card
        elif card.name == "PARAM":
            key, value = card.at(1).upper(), card.at(2).upper()
            if key == "K6ROT":
                allowed = re.fullmatch(r"[0-9]+(?:\.[0-9]*)?", value) is not None
            elif key == "UNITSYS":
                allowed = re.fullmatch(r"[A-Z0-9-]+", value) is not None
            else:
                allowed = value in PROFILE_PARAMS.get(key, ())
            if key in seen_params or len(card.fields) != 2 or not allowed:
                reject(card, f"duplicate or unsupported PARAM {key}")
            seen_params.add(key)

    for sid, effective in deck.effective().items():
        label = f"SUBCASE {sid}" if sid is not None else "implicit case"
        for key, item in effective.items():
            if key.partition("(")[0] in SELECTORS - {"METHOD"}:
                reject(item, f"{label}: {key} selector is outside the free-free profile")
        output = effective.get("DISPLACEMENT")
        if output is None:
            issues.append(f"{label}: missing DISPLACEMENT output request")
        elif output.value.upper() != "ALL" or set(output.options) - REAL_DISPLACEMENT_OPTIONS:
            reject(output, f"{label}: requires real nodal DISPLACEMENT = ALL")
        method = effective.get("METHOD")
        if method is None:
            issues.append(f"{label}: missing METHOD")
            continue
        card = eigrl.get(method.value)
        if card is None:
            reject(method, f"{label}: METHOD {method.value} does not resolve to EIGRL")
            continue
        nd = int(card.at(4)) if POSITIVE_INT.fullmatch(card.at(4)) else None
        if card.at(2) or card.at(3) or nd is None:
            reject(card, f"{label}: requires blank EIGRL V1/V2 and positive integer ND")
        if expected_nd is not None and nd != expected_nd:
            reject(card, f"{label}: expected EIGRL ND={expected_nd}")
        if len(card.fields) > 8 or card.at(8).upper() not in {"", "MASS"}:
            reject(card, f"{label}: unsupported EIGRL option fields or normalization")
        methods.append({"subcase": sid, "method": int(method.value), "nd": nd, **card.source.summary()})

    return {
        "status": "REJECTED" if issues else "PROFILE_MATCH",
        "methods": methods,
        "issues": issues,
        "manual_review": MANUAL_REVIEW.copy(),
    }


def _unique_hashes(items):
    hashes = dict(items)
    if len(hashes) != len(items):
        raise DeckError("duplicate filename in expected closure")
    return hashes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck", type=Path, help="entry text deck")
    parser.add_argument("--root", type=Path, help="authorized directory for entry and INCLUDE closure")
    parser.add_argument("--expect-closure", type=Path, help="JSON object of relative filenames to SHA-256")
    parser.add_argument("--cards", action="store_true", help="include normalized Bulk Data in JSON")
    parser.add_argument("--free-free", action="store_true", help="check the standalone solid SOL 103 profile")
    parser.add_argument("--observe", action="store_true", help="locate advanced records without validating effective sets")
    parser.add_argument("--nd", type=int, help="expected EIGRL root count (requires --free-free)")
    args = parser.parse_args(argv)
    if args.nd is not None and (not args.free_free or args.nd < 1):
        parser.error("--nd requires --free-free and a positive root count")
    if args.observe and (args.free_free or args.cards):
        parser.error("--observe cannot be combined with --free-free or --cards")
    try:
        expected = (
            json.loads(args.expect_closure.read_text(encoding="utf-8-sig"), object_pairs_hook=_unique_hashes)
            if args.expect_closure else None
        )
        if args.expect_closure and not isinstance(expected, dict):
            raise DeckError("--expect-closure must contain a JSON object")
        if args.observe:
            result = observe_deck(args.deck, root=args.root, expected_hashes=expected)
        else:
            deck = read_deck(args.deck, root=args.root, expected_hashes=expected)
            result = deck.summary(show_cards=args.cards)
            if args.free_free:
                result["free_free"] = free_free_profile(deck, expected_nd=args.nd)
    except (DeckError, OSError, UnicodeError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "UNRESOLVED", "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 1 if args.free_free and result["free_free"]["status"] == "REJECTED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
