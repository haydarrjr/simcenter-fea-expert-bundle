---
name: fea-mesh-quality
description: "Design and assess mesh approximation, element geometry, connectivity and QoI convergence. Use for TRI3/TET4 checks, coincident nodes, refinement studies and meshing API preparation; a valid element shape does not prove solution accuracy."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Mesh Quality

Separate element validity from approximation accuracy. Inspect actual node/element coordinates and incidence, physical regions and the solution regime. Interpret incomplete scans and unsupported elements explicitly; do not hide a singular stress peak with averaging.

## Engineering method and resources

- [Mesh decision method](references/engineering-method.md).
- [TRI3/TET4 implementation](references/tri3-tet4.md).
- Tetra API lifecycle (source: fea_expert_agent_plugin/docs/engineering/vendor-api-workflows.md).

## Executable starting point

```sh
python -m fea_agent assess-mesh examples/mesh_quality_tet4_v1.json
```

The cubic refinement oracle recovers p=3, but identical levels from the wrong physical model cannot pass. Dense-node search exhaustion also cannot establish PASS.

## Generate and inspect a real mesh

Compose with `fea-open-meshing` for `fea_generate_volume_mesh` and
`fea_analyze_meshed_part`, or `fea-artifact-forensics` to inspect a supplied
Gmsh/VTK/VTU/BDF mesh. Establish physical groups and source labels before
checking Jacobians. Confirm exterior-face coverage and normal direction before
pressure/heat transfer; then verify force, moment and work. Do not reinterpret
Gmsh's geometry volume difference as a notch-stress bound. Low-order solid
bending needs QoI refinement even when equilibrium is excellent. The
source meshing method (source: fea_expert_agent_plugin/docs/engineering/source-tools-v3.md) includes
actual affine/Fourier and submillimeter through-hole falsifiers.

## Completion boundary

Return the calculated or evidence-backed decision, its physical assumptions, the strongest falsifier exercised, and the specific unresolved dependency. Use qualified Engineering Desktop Runtime capabilities for native effects; this skill and source calculations do not create host authority. Preserve separate source, native, solver and engineering outcomes.
