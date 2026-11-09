---
name: simcenter-3d-visibility-and-selection
description: >-
  Control what is shown and highlighted in the Simcenter 3D graphics window. Use
  when the user asks to show, hide, show only, select, or deselect meshes, mesh
  collectors, or solid bodies — optionally filtered by name or material. Backed by
  mesh-selection-visibility-tool and body-selection-visibility-tool.
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

# Visibility and Selection

Apply show, hide, showOnly, select (highlight), and deselect actions to meshes
or bodies. Call the tool fresh on every request so it acts on the current state.

## When to use

- "Hide everything except collector X." / "Show only the steel bodies."
- "Select the meshes made of aluminum." / "Deselect all bodies."

## Tools

- `mesh-selection-visibility-tool` — targets meshes and mesh collectors. Filters:
  `meshCollectorName`, `meshName`, `bodyName`, or `materialName`.
- `body-selection-visibility-tool` — targets solid bodies. Filters: `bodyName`
  or `materialName`.

Both require `action` (one of `show`, `hide`, `showOnly`, `select`, `deselect`).

## Workflow

1. Decide the target domain: meshes/collectors -> mesh tool; solid bodies ->
   body tool.
2. Choose the `action` from the user's intent.
3. Pass at most one filter. For the mesh tool, `meshName` may be combined with
   `meshCollectorName` only to scope a specific mesh inside a collector.
4. Omit all filters to apply the action to everything (all mesh collectors, or
   all bodies).
5. Confirm what changed back to the user.

## Rules

- `materialName` is fully supported. When the user filters by material, call the
  tool once with `action` + `materialName` — do not look up the collector first,
  and never say material filtering is unsupported.
- A call with no filter is always valid and targets everything; never ask the
  user to name a collector, body, or material just to satisfy the call.
- When a material is named, use the mesh tool in a FEM or SIM context and the
  body tool in a CAD context.

## Guardrails

- `showOnly` makes matching items visible and hides all others of the same type
  — confirm this is intended before broad use.
- If a filter name is not found, nothing changes; report it and offer to list
  valid names via the inspection skills.
- Prefer one clear action per call rather than chaining ambiguous requests.
