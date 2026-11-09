---
name: fea-materials-properties
description: "Evaluate constitutive assumptions, effective material/property ownership, temperature dependence, orthotropy and laminate coupling. Use for stiffness and thermal load-path decisions; distinguish average stress from strength, fatigue and ply-failure claims."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Materials Properties

Resolve FEM material, property and SIM override ownership before using values. Keep E, G, Poisson ratio, expansion, temperature reference and shear conventions consistent. Use the implemented joint and tensor methods where applicable; general laminate and material-assignment APIs remain explicit gaps.

## Engineering method and resources

- [Constitutive and laminate method](references/engineering-method.md).
- Joint mechanics implementation (source: fea_expert_agent_plugin/docs/engineering/bolted-joint-workflow.md).
- Verified API scope (source: fea_expert_agent_plugin/docs/engineering/vendor-api-workflows.md).
- [Durability](../fea-durability/SKILL.md) for actual pyLife rainflow and FKM nonlinear assessment of signed uniaxial elastic histories. Supply cyclic/material/surface evidence; already-plastic tensor histories need a separate strain-life route.

## Executable starting point

```sh
python -m fea_agent assess-joint examples/engineering_v2/joint_flange8_thermal_service.json
```

Differential bolt/member thermal expansion changes locked preload from 20 kN to 36.957 kN. A [0/90] laminate can have equal membrane stiffnesses while a nonzero B matrix still couples extension to bending.

## Executable continuum and laminate composition

Use `fea_analyze_laminate` with `fea-composite-laminates` for actual ABD/thermal
coupling and ply-surface stress. Preserve bottom-to-top ordering, material axes
and each side of a ply interface. Reversing a stack preserves A/D and reverses
B; an apparently correct membrane stiffness cannot detect a wrong stack.
Use `fea_solve_continuum` with `fea-continuum-thermomechanics` for the explicit
isotropic-solid/SPD-conductivity subset. The current solid strain screen is
not a yield, temperature-dependent property or finite-rotation validation.
A PCOMP record readable by the artifact reader does not make the solid solver
a laminate shell solver. See the implemented physics and assumptions (source: fea_expert_agent_plugin/docs/engineering/multiphysics-v3.md).

## Completion boundary

Return the calculated or evidence-backed decision, its physical assumptions, the strongest falsifier exercised, and the specific unresolved dependency. Use qualified Engineering Desktop Runtime capabilities for native effects; this skill and source calculations do not create host authority. Preserve separate source, native, solver and engineering outcomes.
