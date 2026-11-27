# SPDX-License-Identifier: Apache-2.0
# Imported from FEA Expert Agent Plugin, fea_agent/multiphysics/_data.py
"""Strict, SI-only input boundary for source continuum computations."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import cast

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]


def mapping(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(k, str) for k in value):
        raise ValueError(f"{name} must be an object with string keys")
    return cast(dict[str, object], value)


def sequence(value: object, name: str, maximum: int = 50000) -> list[object]:
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError(f"{name} must be a list of at most {maximum} entries")
    return value


def number(value: object, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} must be representable as a finite number") from exc
    if not math.isfinite(result) or (positive and result <= 0):
        raise ValueError(f"{name} must be {'positive and ' if positive else ''}finite")
    return result


def integer(value: object, name: str, low: int = 1, high: int = 2**53 - 1) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def vector(value: object, size: int, name: str) -> Array:
    items = sequence(value, name, size)
    if len(items) != size:
        raise ValueError(f"{name} needs {size} components")
    return np.array([number(x, name) for x in items], dtype=float)


def fields(data: dict[str, object], allowed: set[str], name: str) -> None:
    unknown = set(data) - allowed
    if unknown:
        raise ValueError(f"Unsupported {name} fields: {', '.join(sorted(unknown))}")


def digest(payload: dict[str, object]) -> str:
    try:
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Input must be finite JSON data") from exc
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class Material:
    id: str
    young: float
    poisson: float
    density: float
    alpha: float
    conductivity: Array | None
    heat_capacity: float | None

    @property
    def elasticity(self) -> Array:
        mu = self.young / (2 * (1 + self.poisson))
        lam = self.young * self.poisson / ((1 + self.poisson) * (1 - 2 * self.poisson))
        result = np.zeros((6, 6))
        result[:3, :3] = lam
        result[:3, :3] += 2 * mu * np.eye(3)
        result[3:, 3:] = mu * np.eye(3)
        return result


@dataclass(frozen=True)
class Element:
    id: int
    kind: str
    nodes: tuple[int, ...]
    material: Material


@dataclass(frozen=True)
class Model:
    labels: tuple[int, ...]
    xyz: Array
    index: dict[int, int]
    elements: tuple[Element, ...]
    materials: tuple[Material, ...]


def read_model(payload: dict[str, object], *, thermal: bool) -> Model:
    if payload.get("units") != "SI":
        raise ValueError(
            "Declare units='SI': m, N, kg, s, Pa, W, K; no inferred conversions"
        )
    nodes = sequence(payload.get("nodes"), "nodes", 10000)
    if len(nodes) < 4:
        raise ValueError("At least four nodes are required")
    labels: list[int] = []
    coordinates: list[Array] = []
    for raw in nodes:
        node = mapping(raw, "node")
        fields(node, {"id", "xyz"}, "node")
        labels.append(integer(node.get("id"), "node.id"))
        coordinates.append(vector(node.get("xyz"), 3, "node.xyz"))
    if len(set(labels)) != len(labels):
        raise ValueError("Duplicate node label")
    index = {n: i for i, n in enumerate(labels)}
    materials: dict[str, Material] = {}
    for raw in sequence(payload.get("materials"), "materials", 256):
        item = mapping(raw, "material")
        fields(
            item,
            {
                "id",
                "young_modulus",
                "poisson_ratio",
                "density",
                "thermal_expansion",
                "conductivity",
                "specific_heat",
            },
            "material",
        )
        name = item.get("id")
        if not isinstance(name, str) or not name or name in materials:
            raise ValueError("Material IDs must be nonempty unique strings")
        nu = number(item.get("poisson_ratio"), "poisson_ratio")
        if not -1 < nu < 0.49:
            raise ValueError(
                "Displacement-only solid formulation requires -1 < nu < 0.49; nearly incompressible mixed elements are absent"
            )
        conductivity: Array | None = None
        heat_capacity: float | None = None
        if thermal or "conductivity" in item:
            if isinstance(item.get("conductivity"), list):
                rows = sequence(item["conductivity"], "conductivity", 3)
                if len(rows) != 3:
                    raise ValueError("conductivity tensor must be 3 by 3 in global XYZ")
                conductivity = np.array([vector(x, 3, "conductivity") for x in rows])
                if not np.allclose(conductivity, conductivity.T, rtol=1e-12, atol=0):
                    raise ValueError("conductivity tensor must be symmetric")
                if np.min(np.linalg.eigvalsh(conductivity)) <= 0:
                    raise ValueError("conductivity must be positive definite")
            else:
                conductivity = np.eye(3) * number(
                    item.get("conductivity"), "conductivity", positive=True
                )
        if thermal or "specific_heat" in item:
            heat_capacity = number(
                item.get("specific_heat"), "specific_heat", positive=True
            )
        materials[name] = Material(
            name,
            number(item.get("young_modulus"), "young_modulus", positive=True),
            nu,
            number(item.get("density"), "density", positive=True),
            number(item.get("thermal_expansion", 0), "thermal_expansion"),
            conductivity,
            heat_capacity,
        )
    elements: list[Element] = []
    used: set[int] = set()
    for raw in sequence(payload.get("elements"), "elements", 40000):
        item = mapping(raw, "element")
        fields(item, {"id", "kind", "nodes", "material"}, "element")
        kind = item.get("kind")
        if kind not in ("tet4", "hex8"):
            raise ValueError("Only tet4 and fully integrated hex8 solids are supported")
        count = 4 if kind == "tet4" else 8
        connectivity = tuple(
            integer(x, "element node")
            for x in sequence(item.get("nodes"), "element.nodes", count)
        )
        if len(connectivity) != count or len(set(connectivity)) != count:
            raise ValueError("Wrong element node count or repeated node")
        if not set(connectivity) <= set(index):
            raise ValueError("Element references unknown node labels")
        mat = item.get("material")
        if not isinstance(mat, str) or mat not in materials:
            raise ValueError("Element references an unknown material")
        elements.append(
            Element(
                integer(item.get("id"), "element.id"),
                str(kind),
                tuple(index[x] for x in connectivity),
                materials[mat],
            )
        )
        used.update(connectivity)
    if not elements or len({e.id for e in elements}) != len(elements):
        raise ValueError("Elements must be nonempty with unique IDs")
    if used != set(labels):
        raise ValueError("Orphan nodes are not silently omitted")
    return Model(
        tuple(labels),
        np.array(coordinates),
        index,
        tuple(elements),
        tuple(materials.values()),
    )
