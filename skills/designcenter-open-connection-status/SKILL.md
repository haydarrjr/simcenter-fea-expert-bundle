---
name: designcenter-open-connection-status
description: >-
  Check and recover the connection between the Designcenter Open MCP server and a running
  Siemens Designcenter session. Use when the Designcenter Open tools are missing or
  not listed, when a journal, snippet, discovery, model-data, or documentation
  tool call fails or times out, or when the user asks "is Designcenter connected",
  "why are no NXOpen tools available", or "the Designcenter Open server won't start". Backed
  by the always-available dc_connection_status tool.
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

# Designcenter Open Connection Status

Confirm that the Designcenter Open MCP server is attached to a live Designcenter
session, and guide the user to recover the connection when it is not. The NXOpen
discovery, snippet, journal, execute, model-data, and documentation tools are
published by the backend only while a session is active; when the session is not
attached, `dc_connection_status` is the one tool that is always present.

## When to use

- The expected Designcenter Open tools are not listed, or only `dc_connection_status` is
  available.
- A discovery, snippet, journal, execute, model-data, or documentation tool call
  just failed, returned an error, or timed out.
- The user asks "is Designcenter connected?", "why do the NXOpen tools not
  work?", "there are no tools", or "the Designcenter Open server won't start".
- Before reporting that the server is broken or unavailable — check first instead
  of guessing from a failed call.

## Tools

- `dc_connection_status` — reports whether this MCP server is currently connected
  to a running Designcenter session. Always available, even before Designcenter
  connects or after it disconnects. Takes no input. Returns the connection state
  plus guidance for resolving a disconnected state.

## Workflow

1. Call `dc_connection_status` to read the current connection state. Never assume
   the server is down without this check.
2. If it reports connected: retry the user's original tool call once, then
   continue the normal workflow from that fresh result.
3. If it reports not connected: relay its guidance to the user — start (or
   re-attach) the MCP server session from the Designcenter UI, wait until it
   reports ready, then retry the original request.
4. Expect a brief startup gap: the backend session attaches a second or two
   after the server process starts, so the first call often shows only
   `dc_connection_status` or reports not-connected. Re-check and retry up to 3
   times, pausing about two seconds between tries, before concluding the session
   is unavailable.
5. Report the actual state in plain language (connected / not connected) and the
   concrete next step, not a generic failure.

## Guardrails

- Read-only workflow — it inspects the connection, it does not modify the part or
  run any journal.
- Do not fabricate a connection state; report only what `dc_connection_status`
  returns.
- Do not tell the user the tools do not exist. When only `dc_connection_status`
  is present, the correct conclusion is that the Designcenter session is not yet
  attached, not that the capability is missing.
- Once the session is connected, hand back to the matching Designcenter Open skill (API
  discovery, journal authoring, model-data read, or documentation search).
