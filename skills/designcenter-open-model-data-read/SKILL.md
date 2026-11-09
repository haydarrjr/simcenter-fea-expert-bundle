---
name: designcenter-open-model-data-read
description: >-
  Read live CAD modeling data from the currently open Designcenter part —
  features, bodies, faces, sketches, expressions, attributes, relationships,
  failures, errors, layers, and the assembly tree. Use when the user asks about
  the current CAD model's actual geometry, state, or values. This covers CAD
  modeling entities ONLY — it does NOT cover mesh/FE data (mesh collectors,
  element or node counts, mesh quality); route "mesh info" and FE mesh questions
  to the Model Inspection mesh-info-tool instead. Combines the Designcenter Open
  explore-model-structure and read-model-data tools in their required order.
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

# Live Model Data Read

Answer questions about the open part's real state by discovering its schema,
then extracting only the data the question needs. Use for live reads, not for
API discovery or journal authoring.

## When to use

- "What features / expressions / attributes does this part have?"
- "List the bodies / layers / relationships in the current model."
- "Which features failed?" / "Show the assembly tree."

## Tools

- `explore-model-structure` — reports the queryable schema (entities, their
  scalar and relational properties, entity notes, filter syntax, pagination) for
  the active Designcenter application domain. Input: `application` (array; e.g.
  `["modeling"]`), optional `userQuery`, optional `PAGE` only if advertised by the current input schema. MUST be called before
  the first read in a conversation.
- `read-model-data` — retrieves live values and relationships from the open part
  using a JSON extraction schema. Input: `schemaForExtraction` (JSON string),
  optional `CURSOR` only if advertised by the current input schema.

## Workflow

1. Call `explore-model-structure` with the relevant `application` domain(s).
   If `hasMoreSchema` is true, if the current input schema supports PAGE, call again with `PAGE` set to `nextPageToCall`
   (keep `application` unchanged) and merge every schema page before proceeding.
2. Build a MINIMAL `schemaForExtraction` using ONLY names from the discovery
   response — never invent names. Include all entity types relevant to the
   question; include a scalar property only if the user asked for it, it is
   needed for a filter, or it is needed for traversal.
3. Apply an entity-level `filter` (operator `and`/`or` + `conditions`) whenever
   the question narrows by name, value, type, or category.
4. Call `read-model-data`. If `hasMoreData` is true, if the current input schema supports CURSOR, call again with `CURSOR`
   set to the returned value and the SAME `schemaForExtraction`; retrieve every
   page before answering.
5. Re-run `explore-model-structure` if the active part, application domain, or
   schema context changes.

## Extraction schema shape

```json
{
  "domain": [
    {
      "name": "<domain>",
      "entities": [
        {
          "name": "<EntityType>",
          "scalar_properties": ["<prop1>"],
          "relational_properties": ["<relation>"],
          "filter": {"operator": "and", "conditions": [
            {"prop": "<prop1>", "comparator": "<COMPARATOR>", "value": "<val>"}
          ]}
        }
      ]
    }
  ]
}
```

## Guardrails

- This is a read-only workflow — it does not modify the part.
- Always discover before reading; never build an extraction schema from assumed
  names.
- Keep properties minimal: when in doubt, leave a scalar out.
