# SPDX-License-Identifier: Apache-2.0
# Imported from FEA Expert Agent Plugin, fea_agent/multiphysics/modal.py
"""DOF-mapped, metric-aware comparison of degenerate modal subspaces."""

from __future__ import annotations

import math

import numpy as np
from scipy.linalg import subspace_angles  # type: ignore[import-untyped]

from ._data import Array, digest, fields, mapping, number, sequence, vector


def _basis(raw: object, name: str) -> tuple[list[str], Array, Array]:
    data = mapping(raw, name)
    fields(data, {"dof_ids", "frequencies_Hz", "vectors"}, name)
    dofs_raw = sequence(data.get("dof_ids"), "dof_ids", 10000)
    if not dofs_raw or any(not isinstance(x, str) or not x for x in dofs_raw):
        raise ValueError(
            "Modal DOF IDs must be nonempty strings including node/frame/component identity"
        )
    dofs = [str(x) for x in dofs_raw]
    if len(set(dofs)) != len(dofs):
        raise ValueError("Modal DOF IDs must be unique")
    frequencies = np.array(
        [
            number(f, "frequency_Hz", positive=True)
            for f in sequence(data.get("frequencies_Hz"), "frequencies_Hz", 128)
        ]
    )
    vectors = sequence(data.get("vectors"), "vectors", 128)
    if not len(vectors) == len(frequencies) or not vectors:
        raise ValueError("Provide one vector per positive frequency")
    matrix = np.column_stack([vector(x, len(dofs), "mode vector") for x in vectors])
    return dofs, frequencies, matrix


def compare_modal_subspaces(payload: dict[str, object]) -> dict[str, object]:
    """Compare declared mode clusters in an explicit positive inner product.

    The caller supplies a physically justified frequency cluster. This function
    never lets mixing separated frequencies masquerade as a degenerate match.
    """
    fields(
        payload,
        {
            "schema_version",
            "reference",
            "candidate",
            "metric_weights",
            "metric_matrix",
            "frequency_relative_tolerance",
            "cluster_relative_bandwidth",
            "maximum_angle_deg",
        },
        "modal comparison",
    )
    if (
        "schema_version" in payload
        and payload["schema_version"] != "fea.modal_subspace.v1"
    ):
        raise ValueError("Unsupported modal comparison schema_version")
    source_hash = digest(payload)
    ids, reference_f, reference = _basis(payload.get("reference"), "reference")
    candidate_ids, candidate_f, candidate = _basis(
        payload.get("candidate"), "candidate"
    )
    if set(ids) != set(candidate_ids):
        raise ValueError(
            "DOF identity mismatch; no positional truncation or label/index guessing"
        )
    order = {name: i for i, name in enumerate(candidate_ids)}
    candidate = candidate[[order[name] for name in ids]]
    if reference.shape[1] != candidate.shape[1]:
        raise ValueError(
            "Different cluster dimensions cannot establish modal equivalence"
        )
    if reference.shape[1] > reference.shape[0]:
        raise ValueError("More vectors than physical DOFs")
    if "metric_weights" in payload and "metric_matrix" in payload:
        raise ValueError("Supply either metric_weights or metric_matrix")
    if "metric_matrix" in payload:
        if len(ids) > 1500:
            raise ValueError(
                "Dense metric limited to 1500 DOFs; use explicit diagonal weights for larger comparisons"
            )
        raw = sequence(payload["metric_matrix"], "metric_matrix", len(ids))
        if len(raw) != len(ids):
            raise ValueError("Metric shape mismatch")
        metric = np.array([vector(x, len(ids), "metric row") for x in raw])
        if not np.allclose(metric, metric.T, rtol=1e-12, atol=0):
            raise ValueError("Metric must be symmetric")
        try:
            root = np.linalg.cholesky(metric).T
        except np.linalg.LinAlgError as exc:
            raise ValueError("Metric must be positive definite") from exc
        weighted_r, weighted_c = root @ reference, root @ candidate
        metric_name = "supplied_dense_positive_definite_metric"
    elif "metric_weights" in payload:
        weights = vector(payload["metric_weights"], len(ids), "metric_weights")
        if np.any(weights <= 0):
            raise ValueError("Metric weights must be positive")
        weighted_r = np.sqrt(weights)[:, None] * reference
        weighted_c = np.sqrt(weights)[:, None] * candidate
        metric_name = "supplied_diagonal_metric"
    else:
        raise ValueError(
            "Explicit metric required; mixed translation/rotation units cannot be silently Euclidean"
        )
    for matrix in (weighted_r, weighted_c):
        lengths = np.linalg.norm(matrix, axis=0)
        if np.any(lengths == 0):
            raise ValueError("Zero mode vector")
        matrix /= lengths
        if np.linalg.matrix_rank(matrix, tol=1e-10) != matrix.shape[1]:
            raise ValueError(
                "Linearly dependent cluster vectors cannot establish subspace agreement"
            )
    tolerance = number(
        payload.get("frequency_relative_tolerance", 0.02),
        "frequency_relative_tolerance",
    )
    bandwidth = number(
        payload.get("cluster_relative_bandwidth", 0.01), "cluster_relative_bandwidth"
    )
    angle_limit = number(payload.get("maximum_angle_deg", 5), "maximum_angle_deg")
    if (
        not 0 <= tolerance <= 0.2
        or not 0 <= bandwidth <= 0.1
        or not 0 <= angle_limit <= 45
    ):
        raise ValueError("Modal tolerances outside admitted ranges")
    relative_bandwidth = max(
        float(np.ptp(reference_f) / np.mean(reference_f)),
        float(np.ptp(candidate_f) / np.mean(candidate_f)),
    )
    if len(reference_f) > 1 and relative_bandwidth > bandwidth:
        raise ValueError(
            "NOT_A_DEGENERATE_CLUSTER: compare separated frequencies individually rather than arbitrary subspace mixing"
        )
    frequency_errors = np.abs(np.sort(candidate_f) - np.sort(reference_f)) / np.sort(
        reference_f
    )
    angles = np.asarray(subspace_angles(weighted_r, weighted_c))
    angle_degrees = np.rad2deg(angles)
    mac = np.abs(weighted_r.T @ weighted_c) ** 2
    max_angle = float(np.max(angle_degrees))
    matches = max_angle <= angle_limit and float(np.max(frequency_errors)) <= tolerance
    return {
        "schema_version": "fea.modal_subspace.result.v1",
        "evidence_level": "SOURCE_EVIDENCE_COMPARISON",
        "input_sha256": source_hash,
        "status": "MATCH_WITHIN_DECLARED_TOLERANCES" if matches else "REJECTED",
        "metric": metric_name,
        "dof_count": len(ids),
        "cluster_dimension": len(reference_f),
        "dof_ids": ids,
        "principal_angles_deg": angle_degrees.tolist(),
        "maximum_angle_deg": max_angle,
        "minimum_subspace_cosine_squared": math.cos(float(np.max(angles))) ** 2,
        "pairwise_MAC": mac.tolist(),
        "frequency_relative_errors_sorted": frequency_errors.tolist(),
        "cluster_relative_bandwidth": relative_bandwidth,
        "wrong_answer_falsifier": "Rotated/sign-reversed bases of a repeated eigenspace may have poor pairwise MAC and still span the same space; a missing direction or wrong metric must fail.",
        "limitations": [
            "Declared common DOF identity/frame and positive metric are required; no interpolation between different meshes.",
            "Only real, positive-frequency mode clusters are compared; gyroscopic complex modes and unstable/rigid modes require another formulation.",
            "Subspace agreement and frequency agreement are comparison evidence, not validation of loads/materials or an experimental model.",
        ],
        "engineering_acceptance": "NOT_RUN",
    }
