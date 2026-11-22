---
name: fea-open-meshing
description: "Verify geometry-to-mesh and load or heat-flux transfer by conservation checks."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Open meshing and boundary transfer

Use for boundary-group and mesh-transfer verification on newly imported or idealized solid geometry. Identify the actual Designcenter body and faces; establish unit scale, expected volume, interfaces and mesh family. Use [Model Inspection](../simcenter-3d-mesh-inspection/SKILL.md) and [mesh quality](../fea-mesh-quality/SKILL.md) against the owned model. Qualified native mesh generation follows [mesh generation](../simcenter-3d-mesh-generation/SKILL.md), with independent element/collector readback.

For a repeatable selection, state its physical role, body or occurrence, coordinate frame, geometry type, orientation and expected coverage. Resolve and inspect the recipe before committing a mesh control or using it to transfer a boundary condition. After CAD updates, compare membership and total area or length against the intended region across child faces and edges. Check excluded geometry for overlap. Measure the realized local edge size and its transition to the neighboring mesh after regeneration. See [regional mesh verification](references/regional-mesh-verification.md).

On a known physical region, integrate pressure or traction into a force and moment about an explicit datum, or integrate heat flux into a total power. Check surface normals, orientation, selected area, units and conservation after mapping. Do not replace midside-node connectivity, smooth duplicate entities or assume a single face is an entire boundary. Read [engineering method](references/engineering-method.md) for representative balance checks and [continuum thermomechanics](../fea-continuum-thermomechanics/SKILL.md) for solid-field verification.
