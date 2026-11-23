---
name: simcenter-3d-mesh-generation
description: "Create a shell or solid mesh, apply a selection recipe or local mesh control, and verify the realized mesh."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Mesh generation

On an identified FEM working copy, use the [native runtime gate](../fea-native-runtime-gate/SKILL.md) for the authorized edit. Match `surface-mesh-generation-tool` to shell meshes and `solid-mesh-generation-tool` to solid meshes.

Choose exactly one scope: named body, current graphics selection, explicitly requested all bodies, or identified existing mesh/collector. A mesh or collector filter can edit existing entities in place. Set element type and size from the engineering intent, or leave them unspecified when automatic values are intended. Verify exact scope, mesh identity, element type and count with an independent `mesh-info-tool` readback. Check mesh quality when the engineering task requires it.

For Selection Recipe, local Mesh Control and scoped quality, use the [2612 NXOpen operations](../designcenter-open-journal-authoring/references/cae-2612.md#regional-mesh-operations). Read resolved membership and the control binding separately. Regenerate the FEM, then measure the achieved size on the same physical region and run [regional quality review](../simcenter-3d-mesh-quality-review/SKILL.md).
