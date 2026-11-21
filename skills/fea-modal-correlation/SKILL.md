---
name: fea-modal-correlation
description: "Compare mode shapes or modal subspaces across simulations or test data."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Modal correlation

Compare actual labeled modes in the same model/reference frame and physical state. Align observation coordinates, DOF types, units and sensor or mesh mapping. For a mode pair, compute mass-weighted or observation-weighted MAC only if the weight basis is valid. For a repeated/close cluster, compare subspace dimension and principal angles or singular values using the same weighted orthonormal basis.

Read [correlation method](references/engineering-method.md) and [free-free SOL 103](../fea-dynamics/references/sol103-free-free.md). Use original eigenspectrum and qualified modal vector export; visual agreement alone cannot verify quantitative correlation. Preserve unresolved correspondence, insufficient spatial coverage and normalization limits.
