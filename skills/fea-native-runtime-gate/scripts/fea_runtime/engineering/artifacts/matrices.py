# SPDX-License-Identifier: Apache-2.0
# Imported from FEA Expert Agent Plugin, fea_agent/artifacts/matrices.py
"""OP4 matrix extraction preserving sparse structure and complex entries."""
from __future__ import annotations

import importlib
from pathlib import Path

import numpy as np

from .common import ArtifactError, ArtifactLimits, Budget, dependency, logger, plain, selection


def read_op4(path: Path, options: dict[str, object], limits: ArtifactLimits, budget: Budget) -> dict[str, object]:
    dependency("pyNastran", "1.4.1")
    module = importlib.import_module("pyNastran.op4.op4")
    sparse = importlib.import_module("scipy.sparse")
    matrices = module.OP4(debug=None, log=logger()).read_op4(str(path), matrix_names=options.get("matrix_names"))
    if len(matrices) > limits.max_tables:
        raise ArtifactError("TABLE_LIMIT")
    output = []
    for name, matrix in matrices.items():
        value = matrix.data
        if max(value.shape) > limits.max_entities:
            raise ArtifactError("MATRIX_DIMENSION_LIMIT", name)
        is_sparse = sparse.issparse(value)
        coo = sparse.coo_matrix(value)
        coo.sum_duplicates()
        coo.eliminate_zeros()
        if coo.nnz > limits.max_entities * 20:
            raise ArtifactError("MATRIX_ENTRY_LIMIT", name)
        order = np.lexsort((coo.col, coo.row))
        rows = selection(options, value.shape[0], "row")
        keep = (coo.row[order] >= rows.start) & (coo.row[order] < rows.stop)
        index = order[keep]
        row: dict[str, object] = {"name": name, "form": int(matrix.form), "shape": list(value.shape),
                                 "dtype": str(value.dtype), "upstream_storage": "SPARSE" if is_sparse else "DENSE",
                                 "nonzero_count": int(coo.nnz), "selection": {"row_start": rows.start, "row_stop": rows.stop},
                                 "row_indices": budget.array(coo.row[index], f"{name}.row"),
                                 "column_indices": budget.array(coo.col[index], f"{name}.column"),
                                 "entries": budget.array(coo.data[index], f"{name}.entries"),
                                 "index_base": 0, "implicit_entries": "ZERO",
                                 "dof_mapping": "NOT_ENCODED_BY_OP4", "units": "NOT_ENCODED_BY_OP4",
                                 "finite": bool(np.all(np.isfinite(coo.data)))}
        if value.shape[0] == value.shape[1] and np.all(np.isfinite(coo.data)):
            csr = coo.tocsr()
            norm = float(np.linalg.norm(csr.data))
            delta = csr - csr.T
            hermitian_delta = csr - csr.conjugate().T
            transpose_error = float(np.linalg.norm(delta.data)) / max(norm, float(np.finfo(float).tiny))
            row["relative_transpose_asymmetry"] = transpose_error
            row["relative_hermitian_asymmetry"] = float(np.linalg.norm(hermitian_delta.data)) / max(norm, float(np.finfo(float).tiny))
            row["diagonal"] = budget.array(csr.diagonal()[rows], f"{name}.diagonal")
            row["declared_symmetric_form_consistent"] = (
                transpose_error < 1e-6 if int(matrix.form) == 6 else None)
        output.append(row)
    return {"kind": "NASTRAN_MATRICES", "reader": {"name": "pyNastran", "version": "1.4.1"},
            "matrices": output, "requested_names": plain(options.get("matrix_names")),
            "limits": ["OP4 matrix names and forms do not establish physical K/M/C roles",
                       "No node/DOF order, constraints, frame or units are inferred",
                       "Symmetry is a data diagnostic, not proof of positive definiteness or model validity",
                       "Sparse duplicate entries are summed; implicit entries are zero"]}
