# SPDX-License-Identifier: Apache-2.0
# Imported from FEA Expert Agent Plugin, fea_agent/artifacts/common.py
"""Versioned, bounded data contracts for third-party engineering readers."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import importlib
import importlib.metadata
import math
from pathlib import Path
from typing import cast

import numpy as np
from numpy.typing import NDArray


class ArtifactError(ValueError):
    """A failed source read, never a solver or design acceptance decision."""

    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        self.message = message or code
        super().__init__(f"{code}: {self.message}")


@dataclass(frozen=True)
class ArtifactLimits:
    """Hard upper bounds; output selections are explicitly marked partial."""

    max_file_bytes: int = 32 * 1024 * 1024
    max_entities: int = 200_000
    max_output_values: int = 100_000
    max_tables: int = 256
    timeout_seconds: int = 30
    memory_mb: int = 2048

    def __post_init__(self) -> None:
        caps = {"max_file_bytes": 128 * 1024 * 1024, "max_entities": 2_000_000,
                "max_output_values": 1_000_000, "max_tables": 1024,
                "timeout_seconds": 120, "memory_mb": 8192}
        for key, value in asdict(self).items():
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= caps[key]:
                raise ArtifactError("INVALID_LIMIT", key)


class Budget:
    def __init__(self, limits: ArtifactLimits) -> None:
        self.remaining = limits.max_output_values
        self.omissions: list[str] = []

    def array(self, value: object, label: str) -> dict[str, object]:
        arr = np.asarray(value)
        if arr.dtype.kind not in "biufcUS":
            raise ArtifactError("UNSUPPORTED_ARRAY_DTYPE", f"{label}: {arr.dtype}")
        shape = list(arr.shape)
        result: dict[str, object] = {"shape": shape, "dtype": str(arr.dtype),
                                     "sha256": array_digest(arr)}
        cost = int(arr.size) * (2 if np.iscomplexobj(arr) else 1)
        if cost > self.remaining:
            result.update({"values": None, "complete": False, "reason": "OUTPUT_VALUE_LIMIT"})
            self.omissions.append(label)
            return result
        self.remaining -= cost
        result["complete"] = True
        if np.iscomplexobj(arr):
            result["representation"] = "REAL_IMAGINARY"
            result["real"] = plain(arr.real)
            result["imaginary"] = plain(arr.imag)
        else:
            result["values"] = plain(arr)
        if arr.dtype.kind in "fc":
            result["nonfinite_count"] = int(np.count_nonzero(~np.isfinite(arr)))
        return result


def plain(value: object) -> object:
    """JSON-safe conversion: undefined NaN becomes null, never zero."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, bytes):
        return value.decode("latin1").strip()
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, complex):
        return {"real": plain(value.real), "imaginary": plain(value.imag)}
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return plain(value.item())
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    raise ArtifactError("UNSERIALIZABLE_UPSTREAM_DATA", type(value).__name__)


def array_digest(value: NDArray[np.generic]) -> str:
    arr = np.ascontiguousarray(value)
    h = hashlib.sha256()
    h.update(str(arr.dtype).encode())
    h.update(str(arr.shape).encode())
    h.update(arr.tobytes())
    return h.hexdigest()


def dependency(name: str, version: str) -> object:
    try:
        observed = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError as exc:
        raise ArtifactError("DEPENDENCY_MISSING", f"Install {name}=={version}") from exc
    if observed != version:
        raise ArtifactError("DEPENDENCY_VERSION_UNQUALIFIED", f"{name} {observed}; qualified {version}")
    return importlib.import_module(name)


def logger() -> object:
    module = importlib.import_module("cpylog")
    return module.SimpleLogger(level="error", log_func=lambda *args: None)


def option_int(options: dict[str, object], name: str, default: int, maximum: int) -> int:
    value = options.get(name, default)
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise ArtifactError("INVALID_OPTION", name)
    return value


def selection(options: dict[str, object], size: int, axis: str) -> slice[int, int, None]:
    start = option_int(options, f"{axis}_start", 0, size)
    count = option_int(options, f"{axis}_count", size - start, size)
    return slice(start, min(size, start + count))


def read_options(options: dict[str, object] | None) -> dict[str, object]:
    value = options or {}
    allowed = {"result_names", "subcases", "row_start", "row_count", "state_start", "state_count",
               "matrix_names", "punch", "nastran_dialect", "node_label_field", "element_label_field", "dataset_indices"}
    if not isinstance(value, dict) or set(value) - allowed:
        raise ArtifactError("INVALID_OPTION", "Unknown artifact reader options")
    for name in ("result_names", "matrix_names"):
        if name in value:
            items = value[name]
            if not isinstance(items, list) or not items or len(items) > 128 or any(
                    not isinstance(item, str) or not item or len(item) > 128 for item in items):
                raise ArtifactError("INVALID_OPTION", name)
    if "subcases" in value:
        cases = value["subcases"]
        if not isinstance(cases, list) or not cases or len(cases) > 128 or any(
                isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in cases):
            raise ArtifactError("INVALID_OPTION", "subcases")
    if "dataset_indices" in value:
        indices = value["dataset_indices"]
        if not isinstance(indices, list) or not indices or len(indices) > 1024 or any(
                isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < 100000 for index in indices):
            raise ArtifactError("INVALID_OPTION", "dataset_indices")
    if "punch" in value and not isinstance(value["punch"], bool):
        raise ArtifactError("INVALID_OPTION", "punch")
    if value.get("nastran_dialect", "msc") not in {"msc", "nx", "nasa95"}:
        raise ArtifactError("INVALID_OPTION", "nastran_dialect")
    for name in ("node_label_field", "element_label_field"):
        if name in value and (not isinstance(value[name], str) or not value[name] or len(cast(str, value[name])) > 128):
            raise ArtifactError("INVALID_OPTION", name)
    return value


def source_metadata(path: Path, data: bytes, fmt: str, units: dict[str, str] | None) -> dict[str, object]:
    return {"filename": path.name, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data),
            "format": fmt, "original_bytes_modified": False,
            "units": units, "unit_evidence": "CALLER_DECLARED" if units else "NOT_ENCODED_OR_UNRESOLVED",
            "authenticity": "NOT_ESTABLISHED", "solver_execution": "NOT_RUN"}
