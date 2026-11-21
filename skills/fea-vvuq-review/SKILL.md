---
name: fea-vvuq-review
description: "Review FEA verification, validation, mesh convergence and input or model-form uncertainty."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Vvuq Review

Bind comparisons to the same physical quantity, state, field recovery, mapping and source model. Use the [VVUQ method](references/engineering-method.md) and the [constant-ratio refinement method](references/constant-r-refinement.md) on actual mesh-series values. Declare the mesh measure and verify refinement, asymptotic behavior, monotonicity and nonzero differences before calculating Richardson extrapolation or GCI. Keep local/singular stress separate from convergent global response.

Use independent or high-precision mechanics and discriminating checks for phase, signs, DOF maps, energy and forces. Treat active-set changes separately from smooth sensitivity and distinguish material, model form, space/time discretization and uncertainty. Mark the affected comparison unverified when evidence or independent validation is missing.
