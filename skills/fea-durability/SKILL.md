---
name: fea-durability
description: "Assess time-resolved signed FEA stress histories with actual pyLife rainflow, S-N/Miner or FKM nonlinear hysteresis and life methods. Use for load reversals, mean-stress effects, fatigue history custody and nonlinear notch assessment; diagnose missing temporal, material or multiaxial evidence before interpreting life."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Durability

Start from the complete labeled tensor history, its model and result identity,
and the requested fatigue mechanism. Read
[History assessment](references/history-assessment.md) before constructing the
request. Use `fea_assess_fatigue_history` for the implemented fixed-direction
uniaxial methods. Select the method from constitutive state and material
evidence; never turn a colored stress image or unsigned von Mises history into
a load-reversal history.

## Carry the engineering decision through

1. Bind the actual element/integration point, material, frame, tensor convention,
   physical states, SI units and expected history/model digests. Preserve the
   supplied origin as source computation or unauthenticated external evidence.
2. For source transient data, require all integration steps and a successful
   displacement **and stress** time-grid comparison. Route unresolved response
   to [Dynamics](../fea-dynamics/SKILL.md). Energy balance alone cannot qualify
   phase, peaks or counted reversals.
   A successful time comparison still needs separate spatial convergence and
   material validation. An explicit spatial projection may reduce transport
   volume while preserving all times; it cannot establish a global hotspot.
3. Verify fixed-direction uniaxial stress against the entire tensor. Treat
   multiaxial or rotating stress as an unimplemented critical-plane problem.
   Reject already-plastic input to the elastic-notch FKM route.
4. Use supplied amplitude/cycle S-N evidence for the elastic route. For FKM,
   obtain roughness, stressed surface, gradient, shape factor and probability
   assumptions independently; do not infer them from one peak stress.
5. Execute the actual optional engine. Preserve finite-record residual half
   cycles, closed/open hysteresis, the distinct `P_RAM`/`P_RAJ` results and engine
   versions. A missing engine raises `OPTIONAL_ENGINE_NOT_AVAILABLE` and states
   that fatigue was `NOT_RUN`; no assessment has been performed.
6. Return the damage or life result with its governing location, method limits,
   strongest falsifier, and remaining material/sampling/validation dependency.
   Keep `engineering_acceptance=NOT_RUN` until appropriate intended-use evidence
   exists. Miner damage below one and FKM model-based infinite life do not alone
   establish a safe component.

## Executable starting points

```sh
python -m fea_agent source-tool examples/advanced_dynamics_v4/fkm_reference.json --operation assess_fatigue_history
python tools/qualify_dynamics_v4.py --require-engines --output dist/dynamics-v4.json
```

The executable reference reproduces the documented pyLife nonlinear assessment
and separately checks the returned closed-loop strains with the Masing equation.
The source transient example demonstrates why a history with essentially exact
energy can still be rejected for fatigue. Read the
research and independent evidence (source: fea_expert_agent_plugin/docs/research/advanced-physics-v4.md)
for the actual scope and source-access record.
