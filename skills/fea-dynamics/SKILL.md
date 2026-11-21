---
name: fea-dynamics
description: "Analyze modes, FRFs, transient histories, shock spectra, modal damping or NVH source and path contributions."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Dynamics

Bind the requested quantity and the input convention, physical state, constraints, units and frame. Use the relevant method.

- For unloaded, unprestressed SOL 103 use the [free-free workflow](references/sol103-free-free.md) and run the verified deck through [Solution Sequence](../fea-solver-investigation/references/solution-sequence.md).
- For a known harmonic input or FRF, use [forced response](references/forced-response.md). For mounts, transforms and inertia, use [assembly dynamics](references/engineering-method.md).
- For actual complete transient histories, use [transient field histories](references/transient-field-history.md), [BatchPost](../batchpost-actions/SKILL.md) and [durability](../fea-durability/SKILL.md). Check signed integration-point tensors, time-grid refinement and peak/reversal resolution.
- For peak response to base excitation use [response spectra](references/response-spectrum.md). For stationary PSD/CSD and RMS use [random response](../fea-random-response/SKILL.md).
- For damping identification or a mode-set damping transfer use [modal damping](references/modal-damping.md).
- For NVH, select [operational load estimation](references/nvh-load-identification.md), [principal components of correlated references](references/nvh-principal-components.md), or [physical path contributions](references/nvh-transfer-paths.md) by requested output.
- For cyclic, DDAM, rotor gyroscopy, aeroelastic and acoustic checks use [specialized dynamics](references/advanced-dynamics.md).
