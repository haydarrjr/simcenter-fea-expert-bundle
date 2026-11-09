---
name: designcenter-open-documentation-search
description: >-
  Answer Designcenter workflow, how-to, best-practice, and troubleshooting
  questions from Siemens technical documentation, grounded with citations. Use
  when the user asks "how do I", "what is", or "which" about a product feature or
  workflow. Backed by the Designcenter Open documentation-search-tool.
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

# Technical Documentation Search

Answer product questions strictly from Siemens Designcenter technical
documentation, preserving citations. Never answer documentation questions from
memory.

## When to use

- "How do I …", "What is …", "Which … do I use" about a Designcenter feature,
  command, workflow, or best practice.
- Troubleshooting and concept questions that belong in the product docs.

## Tool

- `documentation-search-tool` — retrieves grounded documentation chunks and
  returns them with citations. Input:
  - `user_query` (required) — the question rewritten as one clear standalone
    sentence for retrieval.
  - `contextSensitiveSearch` (optional, default true) — scope to the currently
    active Designcenter application.

## Workflow

1. Rewrite the user's question as a single clear sentence: preserve intent, add
   no new requirements, resolve references like "it"/"this"/"that" from context,
   remove filler, and correct typos to American English.
2. Choose the scope:
   - Leave `contextSensitiveSearch` at its default (true) when the answer depends
     on the currently active application (its workflows, commands, behavior).
   - Set it to false for general, cross-application, or session-independent
     questions — concepts, terminology, product-wide release news, and
     licensing/installation/administration topics.
3. Call `documentation-search-tool` and answer ONLY from the returned chunks.
4. Present the grounded answer together with its citations so the user can
   verify it against the source documentation.

## Guardrails

- Grounding is mandatory: use only the returned chunks; never use prior model
  knowledge, assumptions, or external context, and do not infer missing details.
- If a successful search returns no relevant chunk, reply exactly: "I couldn't
  find the information to answer your question. Consider trying another question
  or topic." Do not use this reply to mask a connection problem: if the tool is
  not available at all (only `dc_connection_status` is present) or the call fails
  with a transport/timeout error, treat it as a connection issue and follow the
  designcenter-open-connection-status skill instead.
- The tool is deterministic — never repeat a call with identical inputs; retry a
  failed request up to 3 times before reporting failure.
