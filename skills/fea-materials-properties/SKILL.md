---
name: fea-materials-properties
description: "Evaluate constitutive assumptions, effective material/property ownership, temperature dependence, orthotropy and laminate coupling. Use for stiffness and thermal load-path decisions; distinguish average stress from strength, fatigue and ply-failure claims."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Materials Properties

Verify material-to-body-to-element-property assignment with [Model Inspection](../simcenter-3d-material-and-body-inspection/SKILL.md) and the actual effective deck. Capture unit systems, density, isotropic/anisotropic axes, temperature range, reference temperature and source of allowables. Reconcile original source, solver representation and recovered fields. A generic material name cannot establish a strength allowable.

Read [material evidence method](references/engineering-method.md) and use [composite laminates](../fea-composite-laminates/SKILL.md), [continuum thermomechanics](../fea-continuum-thermomechanics/SKILL.md) and [thermal](../fea-thermal/SKILL.md) for family-specific evidence.
