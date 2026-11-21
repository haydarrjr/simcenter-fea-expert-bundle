---
name: fea-native-runtime-gate
description: "Prepare and verify an authorized native Simcenter operation with independent readback."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Native Runtime Gate

Use the host-owned Siemens profiles. Apply the [routing recovery budget](../fea-sc3d-tool-routing/SKILL.md) and current exact tool schema. Bind the returned owner, model and revision before effects. See the [journal workflow](../designcenter-open-journal-authoring/SKILL.md) for NXOpen semantics.

The packaged [controller](scripts/fea_controller.py) has a local CLI and an optional async adapter for an existing authenticated invocation and independent readback callback. It starts no process or connector. For a sequence in one native session use a single controller directory.

Use the [existing-session adapters](references/official-mcp-adapter.md) for a host with Python MCP ClientSession or a JavaScript tool dictionary. Build each dependent step after the previous step's independent observation is accepted.

1. Prepare the exact operation, profile, tool, current schema and target (session, release, owner, model and revision). Supply a binding evidence reference and measurable expected native witnesses. Effectful calls also require distinct baseline witnesses and authorization bound to the normalized operation digest. Callers remain responsible for authenticating the host and user approval.
2. Reserve immediately before dispatch using the same fresh binding and request digest. Send the controller's returned arguments through the existing tool. Keep payload SHA out of the Siemens argument envelope.
3. Record the raw response or transport failure. Obtain a fresh independent observation with target, UTC timestamp, evidence reference and witnesses. Only accepted observations permit dependent operations. Incomplete, timed-out or lost responses stay fenced across restarts until observed. Recover a license stop using the approved native license workflow and a fresh qualified run.
4. Preserve sandbox restrictions and verify builder results and cleanup. Track deck export, solver completion, SIM/FEM persistence and engineering acceptance with separate evidence.

`DECK_EXPORT` accepts only `export_journal(target, fem, solution_tag)` from the controller, on the witnessed 2612.1700 modal route. Bind SIM path as `target.model`, and `fem` / `solution_tag` in the binding from the independent live snapshot. Preflight the native export settings and exact destination: a new file beside the owned SIM, no overwrite, no unresolved output overrides. Use the same `deck_path` and `original_solution_signature` in `expected` and `baseline`, and `deck_present: false` before and `true` after. Include `export_finished: true` and `deck_qualified: true` in `expected`. Archive the resulting hash. An absent file while the exporter may still run is not `NOT_APPLIED`. Prove the exporter is terminal before observing a negative outcome. Generic `CAE_MUTATION` still refuses `Solve`.

Read [runtime and API admission](references/engineering-method.md). Distinguish API documentation from a qualified installed operation. For SOL 103, use the [qualified live setup path](../fea-dynamics/references/sol103-free-free.md) and the [Solution Sequence](../fea-solver-investigation/references/solution-sequence.md) for direct Nastran batch. Verify persistence through an admitted save and independent reopen, or record operator save evidence when needed.

## Completion boundary

Return the calculated or evidence-backed decision, its physical assumptions, the strongest falsifier exercised, and the specific unresolved dependency. Use the exact qualified Siemens MCP capability for effects in the live model. Preserve separate source, native, solver and engineering outcomes.
