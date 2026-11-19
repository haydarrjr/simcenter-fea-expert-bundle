---
name: fea-native-runtime-gate
description: "Prepare documented Siemens CAE operations through an existing official Designcenter or Simcenter 3D MCP. Bind profile, model, owner and revision to the exact tool schema. Record independent readback and reconcile uncertain effects before dependent work."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Native Runtime Gate

Use the host-owned Siemens profiles. Check the selected connection status and discover the exact tool and schema. For a live read use the appropriate read-only tool. Bind the returned owner, model and revision to the trusted native session before admitting an effectful operation. Use [tool routing](../fea-sc3d-tool-routing/SKILL.md) to choose the profile and the [journal workflow](../designcenter-open-journal-authoring/SKILL.md) for NXOpen sandbox semantics.

The packaged [controller](scripts/fea_controller.py) has a local CLI and an optional async adapter for an existing authenticated invocation and independent readback callback. It starts no process or connector. For a sequence in one native session use a single controller directory.

1. Prepare the exact operation, profile, tool, current schema and target (session, release, owner, model and revision). Supply a binding evidence reference and measurable expected native witnesses. Effectful calls also require distinct baseline witnesses and authorization bound to the normalized operation digest. Callers remain responsible for authenticating the host and user approval.
2. Reserve immediately before dispatch using the same fresh binding and request digest. Send the controller's returned arguments through the existing tool. Keep payload SHA out of the Siemens argument envelope.
3. Record the raw response or transport failure. Obtain a fresh independent observation with target, UTC timestamp, evidence reference and witnesses. Only accepted observations permit dependent operations. Incomplete, timed-out or lost responses stay fenced across restarts until observed. Recover a license stop using the approved native license workflow and a fresh qualified run.
4. Preserve sandbox restrictions and verify builder results and cleanup. Saving, solving, reopening, GUI state and engineering acceptance require their own authority and evidence.

For engineering-method references, read [runtime and API admission](references/engineering-method.md). Separate Engineering Desktop Runtime and source compiler capabilities below apply only when their respective runtime and tools have been supplied and qualified explicitly.

A plausible discovery response may ignore a requested part filter or return only a prefix. A self-declared authenticated host origin cannot replace independent receipt verification; missing CAE_MUTATION is an exact upstream gap.

## Source MCP and exact-release preparation

`fea-source-engineering` is a separate host-independent STDIO MCP server. Its
`fea_compile_siemens_extension` emits documented NX Open .NET 2606 result
inventory or solve-chain C#. Discovery and source-double compilation do not
establish an installed Runtime operation. `fea_assess_runtime_evidence`
checks contradictory deck/include/state/unit/frame/mesh/job histories. A later
COMPLETED string cannot clear a lost-response hold or authenticate outputs.
The vendor extension (source: fea_expert_agent_plugin/docs/engineering/vendor-runtime-v3.md) records
exact owners, borrowed objects and native gaps; the
source transport (source: fea_expert_agent_plugin/docs/engineering/source-tools-v3.md) has no native
writer or public endpoint.

For batch result-state preparation, use `fea_compile_result_readback` and the
2606 readback method (source: fea_expert_agent_plugin/docs/engineering/vendor-readback-v4.md). Preserve
loadcase, super-iteration and iteration; temporary selection changes require
exclusive borrowed access and verified restoration. Raw buffers cannot acquire
physical tensor/time/label meaning without owner evidence. This source
compiler does not call the host or create a Runtime handler.

The distinct `fea_run_calculix` capability executes an explicitly configured
open solver under hash-bound authorization and durable job custody. It is
effectful, not native Runtime authority. Read
open execution and custody (source: fea_expert_agent_plugin/docs/engineering/source-tools-v4.md) when
these source jobs are relevant; absence of a Siemens installation does not
prevent independently qualified open engineering.

## Completion boundary

Return the calculated or evidence-backed decision, its physical assumptions, the strongest falsifier exercised, and the specific unresolved dependency. Use qualified Engineering Desktop Runtime capabilities for native effects; this skill and source calculations do not create host authority. Preserve separate source, native, solver and engineering outcomes.
