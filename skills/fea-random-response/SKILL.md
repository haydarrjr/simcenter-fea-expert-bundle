---
name: fea-random-response
description: "Analyze stationary random structural vibration, cross PSD, coherence, modal coverage and RMS stress/displacement. Use for correlated multi-input spectra; distinguish transient shock, rotating systems and nonlinear contact from a valid linear stationary response."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Random response

Establish the operating structure and stochastic input before integrating a
response. Preserve the full complex cross-spectral matrix, spatial force
patterns, physical units and output recovery. Compute a defensible covariance;
interpret RMS, finite-duration extremes and fatigue as different questions.

## Technical resources

- [Equations, solver implementation, applicability and worked failures](references/engineering-method.md).
- [Solver-linked artifact investigation](../fea-solver-investigation/references/engineering-method.md).
- [Advanced dynamics boundaries](../fea-dynamics/references/advanced-dynamics.md) for cyclic phase, rotor gyroscopic effects, aeroelasticity and acoustics.
- Siemens source operations (source: fea_expert_agent_plugin/docs/engineering/vendor-api-next.md) for explicitly selected solution and result states.

```sh
python -m fea_agent run-case examples/solver_linked/captured/gantry_case.json
python -m fea_agent run-case examples/solver_linked/captured/contact_wrong_model_case.json
```

The executable implementation assembles flexible three-dimensional frame
matrices, uses their complete mass-normalized modal basis and integrates all
cross terms with resonance-aware adaptive quadrature. It is a source reference
for stationary force-driven linear response. Installed Simcenter random-response
execution, base acceleration, rotor gyroscopic terms, nonlinear sliding and
fatigue life are not implemented by this command.

## Completion

Report the input spectral convention, coherence and phase, operating-state
validity, retained frequency band/basis, covariance and quadrature sensitivity.
Quantify the effect of dropping cross spectra and screen computed motion.
If the intended output is a peak, a simultaneous stress tensor, shock response
or life, supply the additional method and evidence that question needs. Do not
turn component RMS values into a physical stress envelope or grant native work.
