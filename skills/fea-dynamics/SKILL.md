---
name: fea-dynamics
description: "Analyze assembly mass/inertia, mounts, modal subspaces, harmonic and real transient 3D field response. Resolve stress/time histories, energy and time-step accuracy before fatigue; route stationary spectra, cyclic, rotor, aeroelastic or acoustic questions to their explicit methods and limits."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Dynamics

Compose component transforms and mass properties; derive mount stiffness instead of accepting an unexplained diagonal matrix. Bind the operating state and preserve mixed translational/rotational units. Check model validity, complex phase and transfer work before comparing frequencies or amplitudes.

## Select the response method

- Use [Transient field histories](references/transient-field-history.md) and `fea_solve_transient` for actual 3D linear solid response, signed integration-point tensors and time-grid checks. Use [Durability](../fea-durability/SKILL.md) for the resulting state-bound signed histories; exact energy does not establish resolved peaks or reversals.
- Use [Solver investigation](../fea-solver-investigation/SKILL.md) for flexible FE decks, FEM/SIM ownership and state-bound displacement, reaction or modal evidence. Resolve the actual support/load selection and flexible model before comparing source and solver results.
- Use [Random response](../fea-random-response/SKILL.md) for stationary force-driven cross spectra, displacement/stress RMS and covariance after the linear operating state is established. Check full-matrix spectral admissibility, load-pattern units, modal/integration coverage and whole-model motion; retain the distinction between RMS, finite-duration peaks and fatigue.
- Use [Advanced dynamics](references/advanced-dynamics.md) for cyclic phase, shock/DDAM, gyroscopic rotor behavior, aeroelasticity and acoustics. Gyroscopic reasoning requires operating speed, bearing terms and the skew-symmetric gyroscopic operator. Neither the mounted-assembly nor flexible random-response source kernel implements rotor gyroscopy, critical-speed or stability computation; this guidance does not establish native solver or Runtime capability.

## Engineering method and resources

- [Coupled assembly method](references/engineering-method.md).
- [Transient solids, energy and stress history](references/transient-field-history.md).
- [Flexible-deck and physical-result investigation](../fea-solver-investigation/references/engineering-method.md).
- [Stationary correlated random-response method](../fea-random-response/references/engineering-method.md).
- [Cyclic, random, rotor and coupled methods](references/advanced-dynamics.md).
- Result API lifecycle (source: fea_expert_agent_plugin/docs/engineering/vendor-api-workflows.md).

## Executable starting point

```sh
python -m fea_agent run-case examples/engineering_v2/assembly_case.json
python -m fea_agent run-case examples/solver_linked/captured/gantry_case.json
```

Three components and four tilted mounts produce six coupled modes around 46.04–148.70 Hz. A correct resultant force can still hide a missing interface moment; thermal loading can reverse a mount reaction.

## Completion boundary

Return the calculated or evidence-backed decision, its physical assumptions, the strongest falsifier exercised, and the specific unresolved dependency. Use qualified Engineering Desktop Runtime capabilities for native effects; this skill and source calculations do not create host authority. Preserve separate source, native, solver and engineering outcomes.
