---
name: fea-model-preparation
description: "Plan and verify Simcenter 3D idealization, FEM/SIM ownership, mesh, connections, units and associative changes from model evidence."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Model Preparation

Start from [decision procedure](references/decision-procedure.md) and [mechanics](references/mechanics.md). Use Designcenter Open and Model Inspection to verify geometry ownership, dimensional scale, FEM/SIM association, and effective mesh/connection/BC state. Map idealization to the QoI, load path, interfaces and required accuracy. Keep full element order, connectivity and provenance.

Use [imported CAD](references/imported-cad-v4.md), [Siemens preparation](references/siemens-2606.md), [engineering method](references/engineering-method.md) and the [support-arm example](references/worked-case.md) where relevant. For each proposed work-copy operation, bind the exact supported API or MCP tool, units and source geometry. Record independent readback via [runtime gate](../fea-native-runtime-gate/SKILL.md). Preserve original files and distinguish a model preparation decision from a qualified native edit.
