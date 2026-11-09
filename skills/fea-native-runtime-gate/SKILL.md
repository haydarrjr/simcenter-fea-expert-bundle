---
name: fea-native-runtime-gate
description: "Prepare documented Siemens API operations and use the current Engineering Desktop Runtime client for capability discovery, session evidence and qualified readback. Use for owner/build/revision/effect admission and uncertain-outcome reconciliation; never create a competing native writer."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Native Runtime Gate

Use the supplied MCP session through the implemented client. Verify actual tool metadata, pinned contract profile and owner/revision/incarnation. Treat discovery as descriptive and caller-shaped receipts as untrusted. Preserve the uncertainty fence across restart and reconcile before replay.

## Engineering method and resources

- [Runtime and API admission method](references/engineering-method.md).
- Current upstream compatibility (source: fea_expert_agent_plugin/docs/architecture/runtime-compatibility.md).
- Documented API workflows (source: fea_expert_agent_plugin/docs/engineering/vendor-api-workflows.md).
- Injected MCP client example (source: fea_expert_agent_plugin/examples/engineering_v2/runtime_client_example.py).

## Executable starting point

```sh
python -m fea_agent assess-runtime-contract examples/engineering_v2/runtime_contract_case.json
```

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
