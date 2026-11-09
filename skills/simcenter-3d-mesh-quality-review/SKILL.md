---
name: simcenter-3d-mesh-quality-review
description: >-
  Evaluate finite-element mesh quality in the active Simcenter 3D part. Use when
  the user asks about aspect ratio, skewness, Jacobian ratio, free edges, element
  order (linear vs quadratic), or whether a mesh is "good enough" to solve. Backed
  by mesh-quality-tool, with mesh-info-tool for locating the mesh to evaluate.
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

# Mesh Quality Review

Report element quality metrics and help the user judge whether a mesh is fit to
solve. Call tools fresh on every request.

## When to use

- "Check the mesh quality." / "Are there any bad elements?"
- "What is the aspect ratio / skewness / Jacobian ratio of collector X?"
- "Is mesh Y linear or quadratic? Any free edges?"

## Tools

- `mesh-quality-tool` — aspect ratio, skewness, Jacobian ratio, free edge count,
  and element order. Scope with `meshCollectorName` (all meshes in a collector),
  `meshName` (one mesh), or omit both (all collectors in the active part).
- `mesh-info-tool` — use first when the user's target name is ambiguous, to
  resolve the correct collector or mesh name.

## Workflow

1. Determine the scope: a named collector, a named mesh, or the whole part.
2. If the name is uncertain, call `mesh-info-tool` to confirm valid names.
3. Call `mesh-quality-tool` with the resolved scope.
4. Summarize per-metric results, and highlight elements that fall outside common
   quality thresholds so the user can decide whether to remesh.

## Guardrails

- Read-only workflow — it evaluates, it does not modify the mesh.
- Do not invent thresholds as hard limits; present metrics and note which values
  are typically considered marginal, deferring the final judgment to the user.
- If remeshing is requested, hand off to the mesh-generation skill.
