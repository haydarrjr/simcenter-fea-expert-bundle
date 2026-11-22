---
name: fea-multistep-nonlinear
description: "Plan, qualify or diagnose nonlinear structural load steps, state transfer, convergence and material response in SOL 106, 401 or 402."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Multistep Nonlinear

Select the nonlinear mechanism and intended step history. Bind the solution family, material law, contact behavior, load and restraint sequence, and quantities needed for acceptance. Use [connector/contact](../fea-connector-contact/SKILL.md) when contact transfer or bolt preload controls.

Use [diagnostics and controls](references/engineering-method.md) to bind the exact effective deck and F06. Use [load-path verification](references/open-solver-workflows.md) for a step-by-step engineering comparison and [solver deck round trip](../designcenter-open-journal-authoring/references/static-deck-roundtrip-2612.md) when importing a complete deck in the matching release. Consult exact-release Siemens Help before interpreting material fields, cutbacks and output requests.

Identify the attained load and last accepted increment of each required step. Check signed reactions, displacement, stress, and the state variables that govern the decision. Use [BatchPost](../batchpost-actions/SKILL.md) or scoped original solver text for the available fields. Verify history-sensitive quantities with a path-aware independent reference.
