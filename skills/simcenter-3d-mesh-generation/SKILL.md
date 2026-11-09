---
name: simcenter-3d-mesh-generation
description: >-
  Generate or edit finite-element meshes on the active Simcenter 3D FEM part. Use
  when the user asks to create a 2D surface (shell) mesh or a 3D solid tetrahedral
  mesh, to mesh a named body / selected geometry / all bodies, or to edit an
  existing mesh's properties. Backed by surface-mesh-generation-tool and
  solid-mesh-generation-tool.
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

# Mesh Generation

Create surface or solid meshes, or edit an existing mesh in place, on the active
FEM part. This workflow modifies the model — call the tool fresh and confirm the
outcome.

## When to use

- "Mesh this face with 5 mm shell elements." / "Create a surface mesh."
- "Tet-mesh all solid bodies." / "Generate a 3D mesh on body X."
- "Change the element size of collector Y."

## Tools

- `surface-mesh-generation-tool` — 2D triangular/quadrilateral shell mesh, or
  edit an existing shell mesh.
- `solid-mesh-generation-tool` — 3D tetrahedral mesh, or edit an existing solid
  mesh.

All inputs are optional. Key parameters shared by both:
`bodyName`, `elementSize` (omit or 0 for automatic), `elementType`,
`useSelectedObjects`, `meshAllBodies`, `meshCollectorName`, `meshName`.

## Workflow

1. Pick the tool by dimensionality: shell/surface -> surface tool; solid/tet ->
   solid tool.
2. Decide the target:
   - a named body -> `bodyName`;
   - the current graphics selection -> `useSelectedObjects: true`;
   - explicitly all bodies (no selection implied) -> `meshAllBodies: true`;
   - editing an existing mesh -> `meshCollectorName` (or `meshName`), which take
     precedence over the generation targets.
3. Set `elementSize` / `elementType` only when the user specifies them;
   otherwise omit to use Simcenter's automatic values.
4. Report the created or edited mesh, then offer a quality check via the
   simcenter-3d-mesh-quality-review skill.

## Guardrails

- This workflow changes the model. If the target is ambiguous (named body vs.
  selection vs. all bodies), confirm with the user before generating.
- Use `useSelectedObjects` only for the current selection and `meshAllBodies`
  only when the user explicitly asks for all bodies without a selection.
- `meshCollectorName` / `meshName` edit existing meshes in place — do not combine
  them with generation targets expecting a new mesh.
