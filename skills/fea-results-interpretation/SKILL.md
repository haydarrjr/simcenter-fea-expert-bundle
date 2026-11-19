---
name: fea-results-interpretation
description: "Interpret identity-bound FEA results, recovery locations, tensors, modal subspaces and eigen-buckling references. Use for component decoding, principal/von-Mises/Tresca quantities, frame changes and coherent envelopes; unsupported complex or averaged fields stay explicit."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Results Interpretation

Read [artifact forensics](../fea-artifact-forensics/SKILL.md) and identify the exact solved state. For contours, values or trusted UI-independent images, open the exact result file via [BatchPost](../batchpost-actions/SKILL.md), list its state, and select actual types, components, positions and units. Use installed Nastran MCP tools or scoped original F06 text for scalar solver evidence. Record named cases, node/element/ply IDs, coordinate frame and averaging before interpretation.

- [Engineering method](references/engineering-method.md) for displacement, support reactions, wrench transfer, contact and stress extraction.
- [Real tensor quantities](references/real-tensor-qoi.md) for physical Voigt order, shear convention, rotation and invariant checks. Preserve integration-point, elemental, element-nodal and averaged results separately.
- [SOL103/SOL105 quantitative checks](references/sol103-sol105-quant.md) and [free-free SOL 103](../fea-dynamics/references/sol103-free-free.md) for eigenvalue diagnostics and appropriately normalized modes.
- [Engineering report](references/engineering-report.md) for figures, traceability and validation. Leave unreturned components, extrema or states unavailable. Keep the original field exports even when reporting a derived quantity.
