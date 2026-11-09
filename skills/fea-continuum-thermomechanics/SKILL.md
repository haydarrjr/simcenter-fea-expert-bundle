---
name: fea-continuum-thermomechanics
description: "Compute and verify tet4/hex8 solid static/modal, anisotropic conduction, thermal histories and sequential thermoelastic response. Use for real solid-deck recalculation, heat balance, thermal stress, prescribed motion, MPC constraints and model-form rejection."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Continuum thermomechanics

Establish a physical quantity of interest and the admissible mathematical model.
Use `fea_solve_continuum` for supported small-strain linear solid/conduction
problems. Obtain a request through `fea_get_example`, an inspected solid deck
via `fea_prepare_continuum_from_bdf`, or explicit SI entities. Do not silently
drop unsupported cards, contacts, rotational effects or nonlinear materials.

## Engineering sequence

1. Reconcile node labels, connectivity, material IDs, global axes and SI units.
   State reference temperature, expansion coefficients, density, conductivity
   tensor and heat capacity where relevant; reject orphan/invalid entities.
2. Identify rigid-body modes, displacement/MPC compatibility and the intended
   reaction path before solving. A small algebraic residual cannot fix the
   wrong supports or a missing interface condition.
3. Choose static, unstressed modal, steady heat transfer, transient heat transfer
   or sequential thermoelastic history. Keep loads and reference states absolute
   at each step; read the explicit history inheritance rules.
4. Check mechanical force/moment/work or thermal storage/flux balance, positive
   Kelvin and source-free maximum-principle bounds. Reject a nonphysical thermal
   field before propagating it into stress; never clip it to look plausible.
5. Preserve unaveraged integration-point stress/strain/flux and node labels.
   Separate discretization, time-integration and model-form errors with a
   refinement study and an independent oracle appropriate to the QoI.

Read [equations, controls and independent checks](references/engineering-method.md).
For boundary-group loading on newly generated geometry, use
[Open meshing](../fea-open-meshing/SKILL.md). For thin laminates use
[Composite laminates](../fea-composite-laminates/SKILL.md); for local contact or
plasticity return to the appropriate nonlinear model instead of stretching this
linear source formulation.

Deliver the calculated fields and physical falsifiers, numerical and applicability
limits, and the unresolved intended-use validation. Keep source numerical
evidence distinct from archived Nastran agreement and an installed solver run.
