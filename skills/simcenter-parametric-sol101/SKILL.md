---
name: simcenter-parametric-sol101
description: "Create or update an associative parametric Simcenter SOL 101 study."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Parametric SOL 101

Bind the load path, units, material/section assumptions, quantities of interest and engineering acceptance criteria before changing the study. In Pre/Post, bind the owned CAD/FEM/SIM chain. Record parameter identity and semantic support/load regions. Re-resolve them after a geometry or mesh update, and verify region, orientation, count and load resultant. Reapply an existing operation idempotently or surface the conflict.

Use [model preparation](../fea-model-preparation/SKILL.md) for the modeling chain and [native runtime gate](../fea-native-runtime-gate/SKILL.md) for changes. Qualify the exported SOL 101 deck and follow the [solution sequence](../fea-solver-investigation/references/solution-sequence.md). Check independent force/moment balance, displacement, stress recovery location and numerical convergence. See [engineering evidence](references/retrieval-presentation-contract.md) for a model-independent acceptance workflow and optional synthetic benchmark.
