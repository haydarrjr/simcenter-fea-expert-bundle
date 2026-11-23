---
name: simcenter-parametric-sol101
description: "Create or update an associative parametric Simcenter SOL 101 study."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Parametric SOL 101

Bind the load path, units, material and section assumptions, and quantities of interest. Use [associative geometry and mesh updates](references/associative-update.md) when a CAD parameter changes the analysis geometry. Resolve the support and loading regions in their owner and occurrence before and after the update.

Use [model preparation](../fea-model-preparation/SKILL.md) for the modeling chain and [native runtime gate](../fea-native-runtime-gate/SKILL.md) for changes. Qualify the exported SOL 101 deck and follow the [solution sequence](../fea-solver-investigation/references/solution-sequence.md). Check independent force/moment balance, displacement, stress recovery location and numerical convergence. See [engineering evidence](references/retrieval-presentation-contract.md) for the acceptance workflow and applicable analytical checks.
