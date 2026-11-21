# Dynamics routing by requested output

When “spectrum” is ambiguous, use the excitation and output units, frequency or time axis, and intended physical quantity to resolve it. Ask a focused question only if the answer would change the route. Reuse already bound session, part and state.

| User wants | First method | First evidence when an artifact or model already exists |
| --- | --- | --- |
| Natural frequencies, modes or effective mass | [Modal dynamics](../../fea-dynamics/SKILL.md) | Bind solution and basis; inspect the eigenvalues/output and exact state. |
| Correspondence of simulation or measured modes | [Modal correlation](../../fea-modal-correlation/SKILL.md) | Observation DOFs, mode vectors and comparable state. |
| Complex FRF or deterministic frequency response | [Forced response](../../fea-dynamics/references/forced-response.md) | Input/response DOFs, phase, transfer type and effective SOL 108/111 case. |
| Signed time series or reversal | [Transient field history](../../fea-dynamics/references/transient-field-history.md) | Actual time grid and frame with signed component coverage. |
| Peak response to a base spectrum | [Response spectra](../../fea-dynamics/references/response-spectrum.md) | Modal basis, excitation and event or alternative solver setup. |
| Stationary PSD/CSD, RMS or crossings | [Random response](../../fea-random-response/SKILL.md) | PSD convention and effective random controls, then the requested result state. |
| Equivalent or measured modal damping | [Modal damping](../../fea-dynamics/references/modal-damping.md) | Physical damping, mode data and transfer or fit source. |
| Choose between FEM, mode set, FRF set and reduced component | [Component representations](../../fea-model-preparation/references/component-representations.md) | Port DOFs, frame, operating band and needed recovery. |
| Estimate unmeasured operational loads | [Load identification](../../fea-dynamics/references/nvh-load-identification.md) | Calibrated complex transfer and operating responses on matched channels. |
| Decompose partially coherent references | [Principal components](../../fea-dynamics/references/nvh-principal-components.md) | Referenced CSD and rank estimates. |
| Rank contributions to a receiver | [Transfer paths](../../fea-dynamics/references/nvh-transfer-paths.md) | Compatible path loads and transfers plus independent target. |
| Resolve an empty result catalog or references | [Artifact forensics](../../fea-artifact-forensics/SKILL.md) | Exact file and reader coverage, then other original evidence for the requested quantity. |

For ordinary FEM/SIM inventory use Model Inspection. Use Designcenter Open for qualified native Response Dynamics and NXOpen reads. Use the solver diagnostic route for effective deck/F06 and a qualified result reader for data exports. Only use the [native runtime gate](../../fea-native-runtime-gate/SKILL.md) when performing a scoped native operation.
