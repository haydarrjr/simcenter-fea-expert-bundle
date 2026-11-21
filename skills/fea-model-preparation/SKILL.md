---
name: fea-model-preparation
description: "Select idealization or dynamic component representations and verify CAD, FEM, AFM or SIM ownership."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Model Preparation

Use the [decision procedure](references/decision-procedure.md) when comparing representations and [beam mechanics](references/mechanics.md) for a supported analytical check. Use Designcenter Open and Model Inspection to verify geometry ownership, dimensional scale, FEM/SIM association, and effective mesh/connection/BC state. Map idealization to the QoI, load path, interfaces and required accuracy. Keep full element order, connectivity and provenance.

For assembly dynamics choose a [full FEM, mode set, FRF set or external superelement](references/component-representations.md) from the intended ports, band and recovery. Use the [external superelement procedure](references/external-superelements.md) for generation, matrix lineage and assembly.

Use [imported CAD](references/imported-cad-v4.md), [Siemens preparation](references/siemens-2606.md), [engineering method](references/engineering-method.md) where relevant. For each proposed work-copy operation, bind the exact supported API or MCP tool, units and source geometry. Record independent readback via [runtime gate](../fea-native-runtime-gate/SKILL.md). Preserve original files and distinguish a model preparation decision from a qualified native edit.
