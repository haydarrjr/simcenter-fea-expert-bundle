---
name: fea-modal-correlation
description: "Compare measured, imported or recalculated modal evidence with explicit DOF maps and physical metrics. Use for repeated/nearly repeated modes, basis rotation, mode switching, mass weighting, misleading MAC and cross-model eigenvector comparisons."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Modal correlation

Treat a repeated eigenvalue as an invariant subspace. An individual eigenvector
inside that subspace is not unique. Call `fea_compare_modal_subspaces` after
establishing identical physical DOF identity and a justified cluster and metric.

1. Inspect units, frames, constraints, retained components, mass and solver states.
   Include node/frame/component in each DOF ID; reject missing/duplicate identities.
2. Select a narrow physically justified frequency cluster. Do not pool unrelated
   modes merely to improve a correlation score.
3. Declare a positive metric: full SPD mass/measurement metric or explicit
   positive weights. Distinguish rotational and translational dimensions.
4. Inspect metric rank, frequency mismatch and principal angles. Use individual
   MAC values as diagnostics alongside the subspace result, not as a substitute.
5. Challenge sign, scale, order and basis rotation invariance, then replace a
   direction or frequency to ensure a physically wrong candidate is rejected.

Read [subspace method](references/engineering-method.md). Obtain the
`repeated_modal_cluster` example through `fea_get_example`. A successful source
correlation does not establish damping, nonlinear operating state or experimental
validation. Route rotating/gyroscopic or complex non-self-adjoint modes through
their appropriate model family; this real symmetric-subspace method is bounded.
