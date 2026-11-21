---
name: fea-random-response
description: "Assess stationary vibration PSDs, correlated inputs, modal coverage and RMS response."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Random response

Establish the actual linear operating state and characterize the excitation as stationary before integrating response. Bind spatial force patterns, DOFs and axes, cross-PSD convention, units and frequency grid. Validate Hermitian symmetry and positive semidefiniteness across the full spectrum, including coherence and phase. Use [the method](references/engineering-method.md) and qualified Simcenter/Nastran outputs with [BatchPost](../batchpost-actions/SKILL.md) as supported.

Check response covariance, PSD integration and modal coverage. Distinguish RMS, finite-duration peak estimates and fatigue. Contact-state changes, rotating-system behavior and transient shocks require a suitable different analysis. Missing modal or frequency evidence leaves the corresponding verification incomplete.

Use [Nastran random response](references/nastran-random-response.md) for SOL 111 random subcases, tabular PSD/CSD and output validation. Send deterministic SOL 111 FRFs to [forced response](../fea-dynamics/references/forced-response.md) and base-motion peaks to [response spectra](../fea-dynamics/references/response-spectrum.md).
