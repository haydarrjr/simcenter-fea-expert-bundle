---
name: fea-sc3d-tool-routing
description: "Choose or recover the official Siemens tool profile for a CAD, CAE, solver, documentation or result operation."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Siemens tool routing

Choose by operation and needed evidence. Use the selected host's current catalog and schema. Reuse a valid binding and check the intended part, owner and release when a model is involved.

| Operation | Profile and entry point |
|---|---|
| Read CAD part, features or occurrences | Designcenter Open via [live CAD data](../designcenter-open-model-data-read/SKILL.md) |
| Inspect FEM/AFM mesh, bodies, materials or SIM boundary object inventory | Simcenter 3D Model Inspection via the relevant inspection skill |
| Read native SIM ownership, solution, step membership or result references | Designcenter Open via the [qualified CAE read](../designcenter-open-journal-authoring/references/cae-2612.md) on a matching release |
| Discover an NXOpen member or draft a journal | Designcenter Open via [API discovery](../designcenter-open-api-discovery/SKILL.md) or [journal authoring](../designcenter-open-journal-authoring/SKILL.md) |
| Create a mesh or execute another qualified native change | Advertised tool for the operation with [runtime gate](../fea-native-runtime-gate/SKILL.md) controls and independent readback |
| Define a repeatable physical region or drive local mesh size | [Geometry-to-mesh method](../fea-open-meshing/SKILL.md) for scope and [mesh generation](../simcenter-3d-mesh-generation/SKILL.md) for qualified Selection Recipe and Mesh Control operations |
| Locate failed elements or check mesh convergence | [Native quality review](../simcenter-3d-mesh-quality-review/SKILL.md) for the population and [mesh quality](../fea-mesh-quality/SKILL.md) for element validity and response sensitivity |
| Diagnose contact convergence or check a change in contact state | [Contact mechanics](../fea-connector-contact/SKILL.md) for physical acceptance, [Nastran](../simcenter-nastran/references/nonlinear-static-io.md) for effective controls, and [BatchPost](../batchpost-actions/SKILL.md) for numerical witnesses |
| Inspect a deck or solver logs, or submit a job | Nastran diagnostics or scoped original text for inspection. Use [Solution Sequence](../fea-solver-investigation/references/solution-sequence.md) for qualified export and installed Siemens batch submission |
| Export field or graph data from a result file | [BatchPost](../batchpost-actions/SKILL.md) after binding the exact result |
| Retrieve vendor documentation | Product Support via [documentation search](../designcenter-open-documentation-search/SKILL.md) |

Use [static structural routing](references/static-routing.md) when the request concerns static response, load history, contact or buckling. Use [dynamics routing](references/dynamics-routing.md) for dynamic quantities. See the [tool matrix](references/tool-matrix.md) for observed tool names and host recovery. If an effect is uncertain, reconcile the target state before issuing a dependent call.
