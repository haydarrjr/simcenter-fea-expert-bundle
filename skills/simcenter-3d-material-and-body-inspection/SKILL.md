---
name: simcenter-3d-material-and-body-inspection
description: >-
  Inspect solid bodies and materials in the active Simcenter 3D part. Use when the
  user asks which bodies exist, a body's face count or owning part, which material
  is assigned to a body or mesh, or the physical properties of a named material.
  Combines body-info-tool and material-info-tool.
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

# Material and Body Inspection

Answer questions about the solid bodies in the model and the materials assigned
to bodies and meshes. Call tools fresh on every request.

## When to use

- "List the bodies." / "How many faces does body X have? Which part owns it?"
- "What material is assigned to body X / mesh Y?"
- "List all materials." / "Show the properties of material Z."

## Tools

- `body-info-tool` — body name, type, face count, owning part, and material
  assignment. Optional `bodyName` narrows to one body; omit for all bodies.
- `material-info-tool` — omit `materialName` to list every material with its
  `assignedToBodies` / `assignedToMeshes` usage; supply `materialName` for the
  detailed physical properties of one material.

## Workflow

1. For body questions, call `body-info-tool` (named or unfiltered).
2. For "which material" questions, read the material assignment from
   `body-info-tool`, then call `material-info-tool` with that name for property
   detail if the user wants it.
3. For material listings, call `material-info-tool` with no name and use the
   assignment fields to distinguish body materials from mesh materials.
4. Present bodies and materials as compact tables.

## Guardrails

- Read-only workflow — no model changes.
- Body results adapt to the active part (CAD, FEM, or SIM); if a body or
  material name is not found, offer an unfiltered listing to reveal valid names.
