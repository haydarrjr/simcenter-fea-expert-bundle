#!/usr/bin/env python3
"""Stage canonical skills for packaging: rewrite links leaving skills/ to plain text."""
from __future__ import annotations

import argparse
import posixpath
import re
import sys
from pathlib import Path
from urllib.parse import unquote

PREFIX = "fea_expert_agent_plugin"
LINK_RE = re.compile(
    r"""(?P<bang>!?)\[(?P<text>[^\]]*)\]\(\s*(?P<target><[^>]*>|[^)\s]*)"""
    r"""(?P<title>\s+(?:"[^"]*"|'[^']*'))?\s*\)"""
)
CODE_SPAN_RE = re.compile(r"(`+)(?:(?!\1).)+?\1")
FENCE_RE = re.compile(r"^\s{0,3}(```|~~~)")
MD_SUFFIXES = (".md", ".markdown")
BOM = b"\xef\xbb\xbf"
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#")
ABS_RE = re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/](?![\\/])|(?<![\w.])/(?:home|Users)/")


def _split_lines(text: str) -> list[str]:
    return re.findall(r"[^\n]*\n|[^\n]+", text)


def _frontmatter_len(lines: list[str]) -> int:
    if lines and lines[0].rstrip("\r\n") == "---":
        for i in range(1, len(lines)):
            if lines[i].rstrip("\r\n") == "---":
                return i + 1
    return 0


def _resolve(rel_path: str, target: str) -> str | None:
    """Resolved posix path relative to source root, or None if not a path link."""
    t = target.strip()
    if t.startswith("<") and t.endswith(">"):
        t = t[1:-1].strip()
    if not t or t.lower().startswith(SKIP_PREFIXES) or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:(?![\\/])", t):
        return None
    t = unquote(re.split(r"[#?]", t, maxsplit=1)[0])
    if not t:
        return None
    if t.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", t):
        return "ABS:" + posixpath.basename(t.replace("\\", "/"))
    return posixpath.normpath(posixpath.join(posixpath.dirname(rel_path), t.replace("\\", "/")))


def _strip_dot_segments(path: str) -> str:
    """Remove only leading './' segments (never other leading dots, e.g. '.github')."""
    while path.startswith("./"):
        path = path[2:]
    return path


def _is_markdown(rel: str) -> bool:
    return rel.casefold().endswith(MD_SUFFIXES)


def _inside_skills(resolved: str) -> bool:
    return resolved.startswith("skills/")


def _rewrite_line(rel_path: str, line: str, counter: list[int]) -> str:
    def sub(m: re.Match) -> str:
        resolved = _resolve(rel_path, m.group("target"))
        if resolved is None:
            return m.group(0)
        text = m.group("text")
        if resolved.startswith("ABS:"):
            path = resolved[4:]
        elif _inside_skills(resolved):
            return m.group(0)
        else:
            path = resolved
            while path.startswith("../"):
                path = path[3:]
            path = _strip_dot_segments(path)
        counter[0] += 1
        return f"{text} (source: {PREFIX}/{path})" if text else f"(source: {PREFIX}/{path})"

    # protect inline code spans
    out, pos = [], 0
    for cm in CODE_SPAN_RE.finditer(line):
        out.append(LINK_RE.sub(sub, line[pos:cm.start()]))
        out.append(cm.group(0))
        pos = cm.end()
    out.append(LINK_RE.sub(sub, line[pos:]))
    return "".join(out)


def _transform(rel_path: str, data: bytes) -> tuple[bytes, int]:
    if not _is_markdown(rel_path):
        return data, 0
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data, 0
    lines = _split_lines(text)
    start = _frontmatter_len(lines)
    counter = [0]
    fence = None
    for i in range(start, len(lines)):
        fm = FENCE_RE.match(lines[i])
        if fm:
            if fence is None:
                fence = fm.group(1)
            elif fm.group(1) == fence:
                fence = None
            continue
        if fence is None:
            lines[i] = _rewrite_line(rel_path, lines[i], counter)
    return "".join(lines).encode("utf-8"), counter[0]


def transform(rel_path: str, data: bytes) -> bytes:
    return _transform(rel_path, data)[0]


def _links(rel_path: str, data: bytes):
    """Yield (target, resolved) for non-code links in a markdown file."""
    lines = _split_lines(data.decode("utf-8", errors="replace"))
    fence = None
    for i in range(_frontmatter_len(lines), len(lines)):
        fm = FENCE_RE.match(lines[i])
        if fm:
            fence = fm.group(1) if fence is None else (None if fm.group(1) == fence else fence)
            continue
        if fence:
            continue
        stripped = CODE_SPAN_RE.sub("", lines[i])
        for m in LINK_RE.finditer(stripped):
            yield m.group("target"), _resolve(rel_path, m.group("target"))


def _frontmatter_fields(data: bytes) -> dict[str, str] | None:
    lines = _split_lines(data.decode("utf-8", errors="replace"))
    n = _frontmatter_len(lines)
    if not n:
        return None
    body = [l.rstrip("\r\n") for l in lines[1:n - 1]]
    fields: dict[str, str] = {}
    i = 0
    while i < len(body):
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", body[i])
        i += 1
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val[:1] in ("|", ">"):
            parts = []
            while i < len(body) and (body[i].startswith((" ", "\t")) or not body[i].strip()):
                parts.append(body[i].strip())
                i += 1
            val = " ".join(p for p in parts if p)
        elif len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        fields[key] = val
    return fields


def _audit_files(files: dict[str, bytes]) -> list[str]:
    problems: list[str] = []
    for rel in sorted(files):
        data = files[rel]
        if _is_markdown(rel):
            if data.startswith(BOM):
                problems.append(f"{rel}: UTF-8 BOM not allowed (frontmatter would not parse)")
            for target, resolved in _links(rel, data):
                if resolved is None:
                    continue
                if resolved.startswith("ABS:") or not _inside_skills(resolved):
                    problems.append(f"{rel}: link outside skills/: {target}")
                elif resolved not in files:
                    problems.append(f"{rel}: broken sibling link: {target}")
            text = data.decode("utf-8", errors="replace")
            if ABS_RE.search(text):
                problems.append(f"{rel}: absolute path present")
        parts = rel.split("/")
        if len(parts) == 3 and parts[2] == "SKILL.md":
            fm = _frontmatter_fields(data)
            if fm is None:
                problems.append(f"{rel}: missing frontmatter")
                continue
            if fm.get("name") != parts[1]:
                problems.append(f"{rel}: frontmatter name {fm.get('name')!r} != dir {parts[1]!r}")
            desc = fm.get("description", "")
            if not desc:
                problems.append(f"{rel}: empty description")
            elif len(desc) > 1024:
                problems.append(f"{rel}: description too long ({len(desc)} > 1024)")
    return problems


def _read_tree(root: Path) -> dict[str, bytes]:
    base = root / "skills"
    files: dict[str, bytes] = {}
    for p in sorted(base.rglob("*")):
        if p.is_file():
            files[p.relative_to(root).as_posix()] = p.read_bytes()
    return files


def audit(root: Path) -> list[str]:
    return _audit_files(_read_tree(Path(root)))


def report(source: Path) -> int:
    files = _read_tree(source)
    staged, total = {}, 0
    for rel, data in files.items():
        new, n = _transform(rel, data)
        staged[rel] = new
        if n:
            print(f"{n:4d}  {rel}")
            total += n
    print(f"total rewritten links: {total}")
    problems = _audit_files(staged)
    print(f"audit problems after transform: {len(problems)}")
    for p in problems:
        print("  " + p)
    return 1 if problems else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report", help="dry run: rewritten link counts and audit")
    r.add_argument("--source", required=True, type=Path)
    args = ap.parse_args(argv)
    return report(args.source)


if __name__ == "__main__":
    sys.exit(main())
