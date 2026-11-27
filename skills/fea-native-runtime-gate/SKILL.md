---
name: fea-native-runtime-gate
description: "Bind, dispatch and independently verify an authorized native operation, or reconcile an uncertain effect."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Native runtime gate

Use the host-owned profile, current schema and exact target. The [shared CLI](references/runtime-cli.md) and [controller](scripts/fea_controller.py) record dispatch and independent readback in one task-owned runtime root. Direct calls use the configured official tool. Use the [host adapters](references/official-mcp-adapter.md) when the host provides programmatic calling.

1. Prepare the normalized operation with fresh binding evidence and measurable witnesses. For an effect, include a distinct baseline and authorization bound to the operation digest.
2. Reserve using the same binding and digest, then dispatch the returned arguments through the existing tool. Send only fields allowed by its schema.
3. Record the raw response or transport failure. Verify the target and effect with a fresh independent observation. Uncertain effects remain fenced across restarts until reconciled.

Read [native admission and deck export](references/engineering-method.md) for per-operation requirements. Use [native persistence](references/native-persistence.md) to qualify save/reopen and [Solution Sequence](../fea-solver-investigation/references/solution-sequence.md) for solver submission and result checks.
