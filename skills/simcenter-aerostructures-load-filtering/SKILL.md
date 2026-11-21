---
name: simcenter-aerostructures-load-filtering
description: "Extract station forces and moments or filter coherent Simcenter Aerostructures load cases."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Aerostructures load filtering

Bind the free-body definition, selected side, station origin, coordinate system, force and moment units, and exact input result states. Compare the recovered wrench with an independent cut or load balance at the same origin.

Choose 1D extremes for a single governing quantity or a 2D hull for coupled quantities. Retain original case identity and coincident components. Check tie handling, sign, scaling and tolerance in the active method schema. Verify the resulting case-set membership and underlying calculations before using the set downstream.

Read [custom method contracts](references/custom-lcf-templates.md) for NXOpen/ABB and module descriptors. Qualify the installed library and use the [native runtime gate](../fea-native-runtime-gate/SKILL.md) for effects.
