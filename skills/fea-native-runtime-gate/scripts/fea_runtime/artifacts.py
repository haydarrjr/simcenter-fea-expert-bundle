"""Bounded artifact metadata and byte identity checks for the controller."""

import csv
import hashlib
from itertools import islice
import os
from pathlib import Path
import stat

from .contracts import fields, identifier, relative, scoped_path, text


MAX_ARTIFACT = 2 * 1024**3


def file_identity(path):
    path = Path(path)
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        initial = os.fstat(stream.fileno())
        if not stat.S_ISREG(initial.st_mode) or initial.st_size > MAX_ARTIFACT:
            raise ValueError("artifact is not a bounded regular file")
        count = 0
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            count += len(chunk)
            if count > initial.st_size:
                raise ValueError("artifact changed during hashing")
            checksum.update(chunk)
        if count != initial.st_size or initial != os.fstat(stream.fileno()):
            # Reading may change atime, which is irrelevant to byte identity.
            after = os.fstat(stream.fileno())
            if (count != initial.st_size or (initial.st_ino, initial.st_size, initial.st_mtime_ns)
                    != (after.st_ino, after.st_size, after.st_mtime_ns)):
                raise ValueError("artifact changed during hashing")
    current = path.stat()
    if (current.st_dev, current.st_ino, current.st_mtime_ns, current.st_size) != (
            initial.st_dev, initial.st_ino, initial.st_mtime_ns, initial.st_size):
        raise ValueError("artifact path changed during hashing")
    return {"sha256": checksum.hexdigest(), "size": count}


def artifact(root, request, specification, *, observed_at):
    from fea_controller import digest

    fields(specification, ("type", "path", "tool", "build", "coverage", "parents"))
    kind = text(specification["type"])
    path = relative(specification["path"])
    scope = request["output_scope"]
    if scope != "." and not path.startswith(scope + "/"):
        raise ValueError("artifact is outside the declared operation output scope")
    parents = specification["parents"]
    if type(parents) is not list or len(parents) > 256 or len(set(map(identifier, parents))) != len(parents):
        raise ValueError("invalid artifact parents")
    value = {**specification, **file_identity(scoped_path(root, path)), "type": kind,
             "producer": [request["run_id"], request["operation_id"]],
             "tool": text(specification["tool"]), "build": text(specification["build"]),
             "coverage": text(specification["coverage"]), "observed_at": observed_at}
    return {"id": digest(value), **value}


def read_artifact(root, record, selected_fields=()):
    if file_identity(scoped_path(root, record["path"])) != {
            "sha256": record["sha256"], "size": record["size"]}:
        raise ValueError("artifact bytes no longer match the ledger")
    if selected_fields:
        if len(selected_fields) > 16 or any(key not in record for key in selected_fields):
            raise ValueError("unknown or excessive artifact fields")
        return {key: record[key] for key in selected_fields}
    return record

def csv_rows(root, record, start, count):
    if record["type"] != "batchpost.contour.csv" or not 0 <= start <= 10000 or not 1 <= count <= 25:
        raise ValueError("row retrieval is limited to bounded native contour CSV slices")
    path = scoped_path(root, record["path"])
    if record["size"] > 32 * 1024**2:
        raise ValueError("artifact exceeds the bounded CSV reader")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(islice(csv.reader(stream), start, start + count))
    if any(len(row) > 128 or any(len(value) > 4096 for value in row) for row in rows):
        raise ValueError("artifact row exceeds the projection bounds")
    return rows
