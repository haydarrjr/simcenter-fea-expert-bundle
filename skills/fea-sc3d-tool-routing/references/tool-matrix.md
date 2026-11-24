# Siemens profile catalog and recovery

Resolve these operations against the current official tool catalog, including its namespaces and schemas.

On 2026-11-25, Designcenter Open 2612.1700 exposed 12 application tools, including `explore-model-structure` and `read-model-data`. The local VS Code profile with `DC_CONNECTION_STATUS_RESOURCE=1` lists those 12 tools and exposes `dc_connection_status` at the MCP resource `designcenter://connection-status`.

| Profile | Observed capabilities |
|---|---|
| Simcenter 3D Model Inspection | `dc_connection_status`, `part-info-tool`, `body-info-tool`, `material-info-tool`, `mesh-info-tool`, `mesh-quality-tool`, `boundary-condition-tool`, `surface-mesh-generation-tool`, `solid-mesh-generation-tool`, `mesh-selection-visibility-tool`, `body-selection-visibility-tool` |
| Designcenter Open | `dc_connection_status`, `explore-model-structure`, `read-model-data`, `dcopen-pattern-lookup-tool`, `dcopen-keyword-search-tool`, `dcopen-semantic-search-tool`, `dcopen-list-namespaces`, `dcopen-list-classes`, `dcopen-class-info`, `dcopen-member-info`, `dcopen-run-snippet-tool`, `dcopen-run-journal-tool`, `dcopen-execute-tool`. Use `documentation-search-tool` only if advertised |
| Siemens Help Server / Product Support | `search` in `STS_SIMCENTER3D` for Nastran and CAE or `STS_DESIGNCENTER` for NXOpen |
| Simcenter Nastran MCP | `discover_job`, `classify_simulation_intent`, `list_deck_cards`, `read_deck_cards`, `compare_decks`, `parse_f06_file`, `parse_contact_log`, `diagnose_sol401_failure_context`, `resolve_elements`, `search_file`, `read_file_excerpt`, `list_allowed_roots`, `request_file_access` |
| BatchPost | Open and list the exact result before requesting exports through [BatchPost](../../batchpost-actions/SKILL.md) |

A CAD model read provides CAD data. Use the [qualified CAE catalog](../../designcenter-open-journal-authoring/references/cae-2612.md) for matching SIM/AFM links and step membership. The boundary-condition inventory and effective deck answer different questions. For SOL 101/103, use the applicable deck/F06 readers and keep SOL 401-specific tools scoped to their supported diagnostic context.

Active interactive persistence and isolated batch save with independent reopen use the [native persistence method](../../fea-native-runtime-gate/references/native-persistence.md). [Solution Sequence](../../fea-solver-investigation/references/solution-sequence.md) owns qualified deck export, installed batch submission and solver evidence. Use the [runtime gate](../../fea-native-runtime-gate/SKILL.md) for admitted live effects.

## Recover the affected operation

With 2612 project clients, the generated profile enables `--legacy-discovery` where the native connector needs standard MCP `initialize` and `tools/list` in place of `server/discover`. Refresh the catalog before assessing attachment. BatchPost starts a separate worker before its connector is ready. If worker initialization fails, inspect its diagnostics and verify that the host inherited the Siemens licensing environment.

| Observation | Response |
|---|---|
| Required profile missing from the client catalog | Check the host's profile registration and refresh its catalog through the host |
| Model Inspection returns `DCMCP-E002` | Follow [Model Inspection connection](../../simcenter-3d-connection-status/SKILL.md) for that profile. Continue independent CAD or file work if its own binding is available |
| Connected Designcenter session has no active part | Follow [Designcenter connection](../../designcenter-open-connection-status/SKILL.md) to establish the model target |
| Invalid argument, unsupported member, inner error or empty data | Inspect the response and exact schema. Apply a supported correction or narrower read. Use the qualified release path where it covers the operation and targeted API discovery for gaps |
| Read times out | Recheck the binding if stale. Retry after demonstrated recovery or a materially smaller request. Use qualified CAE readback or exact solver evidence where it covers the required field |
| Native effect times out or returns ambiguous evidence | Record `UNKNOWN` and reconcile fresh native/file state before any dependent call or replay |
| Requested deck lies outside diagnostic roots | Resolve the exact path through the profile's allowed-root/access workflow or read the authorized original text |

AgentsAI may delegate bounded inspection, discovery/sandbox, diagnostics, result export, verification and documentation to their corresponding recipe roles. Use the same skill and profile directly when no delegation is needed. The coordinating agent owns live effects and solver submission.
