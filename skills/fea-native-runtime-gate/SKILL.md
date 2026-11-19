---
name: fea-native-runtime-gate
description: "Prepare documented Siemens CAE operations through an existing official Designcenter or Simcenter 3D MCP. Bind profile, model, owner and revision to the exact tool schema. Record independent readback and reconcile uncertain effects before dependent work."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Native Runtime Gate

Use the host-owned Siemens profiles. Check the selected connection status and discover the exact tool and schema. For a live read use the appropriate read-only tool. Bind the returned owner, model and revision to the trusted native session before admitting an effectful operation. Use [tool routing](../fea-sc3d-tool-routing/SKILL.md) to choose the profile and the [journal workflow](../designcenter-open-journal-authoring/SKILL.md) for NXOpen sandbox semantics.

The packaged [controller](scripts/fea_controller.py) has a local CLI and an optional async adapter for an existing authenticated invocation and independent readback callback. It starts no process or connector. For a sequence in one native session use a single controller directory.

Use the [existing-session adapters](references/official-mcp-adapter.md) for a host with Python MCP ClientSession or a JavaScript tool dictionary. Build each dependent step after the previous step's independent observation is accepted.

1. Prepare the exact operation, profile, tool, current schema and target (session, release, owner, model and revision). Supply a binding evidence reference and measurable expected native witnesses. Effectful calls also require distinct baseline witnesses and authorization bound to the normalized operation digest. Callers remain responsible for authenticating the host and user approval.
2. Reserve immediately before dispatch using the same fresh binding and request digest. Send the controller's returned arguments through the existing tool. Keep payload SHA out of the Siemens argument envelope.
3. Record the raw response or transport failure. Obtain a fresh independent observation with target, UTC timestamp, evidence reference and witnesses. Only accepted observations permit dependent operations. Incomplete, timed-out or lost responses stay fenced across restarts until observed. Recover a license stop using the approved native license workflow and a fresh qualified run.
4. Preserve sandbox restrictions and verify builder results and cleanup. Track deck export, solver completion, SIM/FEM persistence and engineering acceptance with separate evidence.

Read [runtime and API admission](references/engineering-method.md). Distinguish API documentation from a qualified installed operation. For SOL 103, use the [qualified live setup path](../fea-dynamics/references/sol103-free-free.md) and the [Solution Sequence](../fea-solver-investigation/references/solution-sequence.md) for direct Nastran batch. The user saves the SIM/FEM.

## Completion boundary

Return the calculated or evidence-backed decision, its physical assumptions, the strongest falsifier exercised, and the specific unresolved dependency. Use the exact qualified Siemens MCP capability for effects in the live model. Preserve separate source, native, solver and engineering outcomes.
