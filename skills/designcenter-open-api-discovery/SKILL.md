---
name: designcenter-open-api-discovery
description: >-
  Discover the NXOpen API before writing journal code against a Designcenter
  session. Use when the user needs to find the right class, method, enum,
  or namespace, or wants documented API patterns and pitfalls. Combines the
  Designcenter Open discovery tools: pattern lookup, keyword and semantic search,
  namespace and class listing, and class/member inspection.
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

# NXOpen API Discovery

Find the exact, verified NXOpen API names you need before generating journal
code. NEVER guess class, method, enum, or parameter names — every name must come
from a tool result.

## When to use

- "What class/method do I use to chamfer an edge / mirror a body / extrude a
  sketch?"
- "Which namespace / classes cover CAM (or Features, Drafting, Assemblies)?"
- "What is the signature of `ExtrudeBuilder.Section`? Is this property settable?"
- Before writing any journal — to catch documented API pitfalls early.

## Tools

- `dcopen-pattern-lookup-tool` — curated patterns, documented gotchas, correct
  method names, and Designcenter color indices. Input: `keywords` (array),
  optional `limit` (default 3, max 5).
- `dcopen-keyword-search-tool` — ranked class/method search. Input: `keywords`
  (array), optional `search_type` (`classes` | `methods`), `page`, `page_size`,
  `category`, and `full_class_name` (required when `search_type` = `methods`).
- `dcopen-semantic-search-tool` — natural-language intent search. Input: `query`
  (string), optional `limit`. First call builds an embedding index (one-time
  ~30-60s).
- `dcopen-list-namespaces` — all namespaces with class counts. Optional `filter`.
- `dcopen-list-classes` — classes in a namespace. Input: `namespace`, optional
  `include_submodules`.
- `dcopen-class-info` — member-name overview of a class. Input: `class_name`
  (fully qualified).
- `dcopen-member-info` — full signature, parameter/return types, settability of
  one member. Input: `class_name`, `member_name`.

## Workflow

1. Extract specific technical keywords from the request (nouns, domain verbs,
   object types). Exclude generic verbs (create, new, make, add, set, get).
2. Call `dcopen-pattern-lookup-tool` FIRST to surface gotchas and correct
   methods before anything else.
3. Find the class: `dcopen-keyword-search-tool` for known terms,
   `dcopen-semantic-search-tool` for intent, or `dcopen-list-namespaces` →
   `dcopen-list-classes` to explore a domain.
4. Drill down: `dcopen-class-info` to see member names, then `dcopen-member-info`
   once per member you actually need (signature, types, settability).
5. Carry the verified names forward into snippet/journal authoring.

## Guardrails

- Discovery is read-only; it does not change the API or the model.
- Always use fully-qualified names (`NXOpen.Features.ExtrudeBuilder`) and
  full enum paths.
- Never assign a member that `dcopen-member-info` reports as read-only.
