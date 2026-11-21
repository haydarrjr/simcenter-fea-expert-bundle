# Admit and verify an official Siemens operation

Identify the product release, the actual MCP namespace and tool schema, live backend identity, work/display parts, stable object labels, owner, revision, dirty state, and source path of the intended work copy. For a derived conclusion require independent evidence for the full specific quantity. For a bolted joint, object counts cannot identify step-specific member regions, coordinates or bolt/contact state.

Use the current global model readers for original evidence and independent readback. Reject a response whose part fingerprint, region scope or expected state conflicts with the request. When pagination is absent, keep a truncated read PARTIAL. A session health response proves connectivity only.

Treat capabilities separately for edit, persistent save, reopen, deck export, solve, job monitoring and result export. A documented NXOpen method, return code, sandbox proof and approved journal source are separate observations. Use the controller's existing operation, dispatch and native-observation records where it admits the operation. For authorized solver execution, verify the exported deck against the in-session setup and follow [Solution Sequence](../../fea-solver-investigation/references/solution-sequence.md) for batch submission. Verify persistence through an admitted save and independent reopen, or record operator save evidence when needed.

Capture baselines and independent observations. For a persisted setup, reopen or obtain an equally authoritative saved-state read and check ownership, targets, settings and dependencies. For a solver job, reconcile job identifier, effective deck, logs, result files and the actual submitted model state. On timeout preserve the operation receipt and reconcile state before retry. For readback that changes a result selection, use a task-owned context and verify restoration.

## Controller deck-export contract

The admitted `DECK_EXPORT` payload is `export_journal(target, fem, solution_tag)` for the witnessed 2612.1700 modal route. Bind the SIM path as `target.model` and supply `fem` and `solution_tag` from an independent live snapshot. Preflight native export settings and use a new destination beside the owned SIM with no unresolved output override.

Use the same `deck_path` and `original_solution_signature` in baseline and expected witnesses. Require `deck_present: false` in the baseline and `deck_present: true`, `export_finished: true` and `deck_qualified: true` in the expected readback. Archive the deck hash. An absent file can establish `NOT_APPLIED` only after the exporter is terminal. The generic `CAE_MUTATION` path refuses `Solve`. For a license stop use the approved native license recovery path and qualify a fresh run.
