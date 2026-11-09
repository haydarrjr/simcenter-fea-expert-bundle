---
name: simcenter-3d-simulation-boundary-conditions
description: >-
  Review the boundary conditions of the active Simcenter 3D simulation (SIM) part.
  Use when the user asks about loads, constraints, or other boundary conditions —
  their type, solver card, applied objects, solver properties with values and
  units, or whether any are incomplete. Backed by boundary-condition-tool.
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

# Simulation Boundary Conditions

Report the loads, constraints, and other boundary conditions of the active SIM
part, independent of any solution. Call the tool fresh on every request.

## When to use

- "List the loads and constraints." / "What boundary conditions are defined?"
- "What objects is constraint X applied to? What are its solver properties?"
- "Are any boundary conditions incomplete?"

## Tools

- `boundary-condition-tool` — returns each boundary condition's name, type,
  solver card name, applied objects, solver properties (formatted values and
  units), description, and an incomplete flag. Optional `boundaryConditionName`
  narrows to entries with that name; omit for all.

## Workflow

1. Confirm the active part is a SIM part (loads/constraints live there). If the
   user is unsure, the part-info context from the simcenter-3d-mesh-inspection skill can
   clarify the active part.
2. Call `boundary-condition-tool` with no name for a full inventory, or with
   `boundaryConditionName` for a specific entry.
3. Present entries grouped as loads, constraints, and other; include applied
   objects, solver properties with units, and flag any marked incomplete.

## Guardrails

- Read-only workflow — it reports boundary conditions, it does not create or
  edit them.
- Results are solution-independent; do not imply a specific solution unless the
  tool output ties an entry to one.
- Call out incomplete boundary conditions explicitly so the user can fix them.
