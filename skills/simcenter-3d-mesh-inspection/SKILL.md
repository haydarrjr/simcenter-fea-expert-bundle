---
name: simcenter-3d-mesh-inspection
description: >-
  Inspect the mesh structure of the active Simcenter 3D FEM/SIM model. Use for
  "list mesh info" and any question about which mesh collectors and meshes
  exist, or the mesh type, element type, element count, node count, or assigned
  material of a mesh. This is the live mesh/FE inventory path — NOT Designcenter Open CAD
  geometry reads and NOT Batch Post .op2 result post-processing. Combines
  part-info-tool and mesh-info-tool for a top-down model overview.
metadata:
  copyright: Unpublished work. Copyright 2026 Siemens
---

<!-- FEA integration safety v1 -->
## FEA integration safety contract (overrides conflicting legacy guidance)

- Discover the current tool catalog and exact input schemas before calling tools.
  A connected server need not expose every tool from older documentation.
  If a call fails, check dc_connection_status first. Retry bounded read-only
  discovery after recovery; never replay an uncertain mutation blindly.
- Documentation: use documentation-search-tool only when currently advertised.
  If absent after connectivity recovery, route to the advertised Product Support
  search tool using its current schema and version-specific Siemens sources.
  If neither route is available, report BLOCKED_BY_OFFICIAL_MCP_CAPABILITY /
  NOT_RUN; do not invent syntax, citations, or answers from memory.
- Pagination: send PAGE or CURSOR only if that exact parameter exists in the
  current tool input schema. A response mentioning hasMoreSchema/hasMoreData
  does not authorize unsupported arguments. If continuation is unavailable,
  report the read as PARTIAL with the unresolved scope; do not claim completeness.
- Journal sandbox: import only NXOpen modules. Never import sys or another
  standard-library module. Use sys.argv only when the current journal tool
  explicitly supplies sys; otherwise stop and verify the supported entry point.
  Keep main(args), session acquisition and builder cleanup requirements.
- A sandbox SUCCESS, exit code zero, or no captured stdout is not observable
  proof that statements, assertions, or error paths executed. Report execution
  transport status separately from observable test evidence. Without inspectable
  output/readback, the claimed behavior remains UNVERIFIED, not tested-correct.
- Action verbs alone do not authorize an ambiguous target, save, solve, or
  overwrite. Live changes require explicit user intent, an identified owned
  working copy, current advertised capability and applicable host approval.
  After a change, obtain independent native readback tied to model identity.
- Mesh metrics: null, zero, placeholder, unavailable or uncomputed values are
  UNVERIFIED unless the metric definition, element applicability and computation
  status establish their meaning. Never convert missing evidence into PASS.
  Free edges may be intentional shell boundaries; interpret topology explicitly.
  Use project/solver/element-specific documented thresholds, not universal limits.
  Shape quality alone does not establish QoI mesh convergence or solve acceptance.
<!-- End FEA integration safety v1 -->

# Mesh Inspection

Guide the user from a whole-session overview down to the details of a specific
mesh. Always call the tools fresh; never reuse a previous result.

## When to use

- "List mesh info." / "How many elements / nodes?" / "What element types are used?"
- "What parts are open?" / "Summarize the model."
- "List the mesh collectors." / "What meshes are in collector X?"
- "What element type / element count / material does mesh Y use?"

This skill is for the live FEM/SIM mesh model. Do not route these to Designcenter Open
(CAD geometry) or Batch Post (.op2 result files) — mesh collectors, element and
node counts, and mesh quality live on the Model Inspection server.

## Tools

- `part-info-tool` — loaded parts, their type (CAD, FEM, ideal, SIM),
  modification/session state, and a count summary by type. Takes no input.
- `mesh-info-tool` — mesh collectors and the meshes within them, including mesh
  type, element type, element count, node count, and assigned material. Optional
  `meshCollectorName` or `meshName` narrows the scope.

## Workflow

1. If the user asks about the overall model, call `part-info-tool` first to
   establish what is loaded and which part is active.
2. Call `mesh-info-tool` with no filter for a full mesh inventory, or with
   `meshCollectorName` / `meshName` when the user names a specific target.
3. Report results as a compact table (mesh, collector, type, element type,
   element count, material). Note when a scope returns nothing.

## Guardrails

- This is a read-only workflow — it does not modify the model.
- If a named collector or mesh is not found, say so and offer to list all
  available names via an unfiltered call.
