---
name: fea-dynamics
description: "Analyze assembly mass/inertia, mounts, modal subspaces, harmonic and real transient 3D field response. Resolve stress/time histories, energy and time-step accuracy before fatigue; route stationary spectra, cyclic, rotor, aeroelastic or acoustic questions to their explicit methods and limits."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Dynamics

Compose component transforms and mass properties. Verify effective stiffness, constraints, operating state and unit/frame conventions. A mode, RMS value and harmonic or transient amplitude describe different states.

- For unloaded, unprestressed SOL 103 use the [free-free workflow](references/sol103-free-free.md) and run the verified deck through [Solution Sequence](../fea-solver-investigation/references/solution-sequence.md).
- For harmonic or mounted-assembly dynamics, use [assembly dynamics](references/engineering-method.md). Check complex phase, transfer work, damping assumptions, frequency sampling, mass and coordinate mapping.
- For actual complete transient histories, use [transient field histories](references/transient-field-history.md), [BatchPost](../batchpost-actions/SKILL.md) and [durability](../fea-durability/SKILL.md). Check signed integration-point tensors, time-grid refinement and peak/reversal resolution.
- For stationary correlated spectra, use [random response](../fea-random-response/SKILL.md). For cyclic, shock/DDAM, rotor gyroscopy, aeroelastic and acoustic checks, use [specialized dynamics](references/advanced-dynamics.md). Require qualified solver scope and exact result state.
