# Tool matrix (observed host catalog; re-discover every session)

Sources of the names: installed bundle skills/recipes/mcps.json of simcenter-3d (skills simcenter-3d-*, designcenter-open-*, batchpost-actions; recipes simcenter-3d-model-inspection-agent, -designcenter-open-agent, -doc-agent, -batchpost-agent), simcenter-nastran (mcps.json, recipe nastran-sol401-debugger, skills nastran-sol401-*), product-support (skill product-support), plus the live tool listing.

## Tools by host
| Host | Tools |
|---|---|
| Simcenter 3D (model inspection) | `dc_connection_status`, `part-info-tool`, `body-info-tool`, `material-info-tool`, `mesh-info-tool`, `mesh-quality-tool`, `boundary-condition-tool`, `surface-mesh-generation-tool`, `solid-mesh-generation-tool`, `mesh-selection-visibility-tool`, `body-selection-visibility-tool` |
| Designcenter Open | `dc_connection_status`, `dcopen-pattern-lookup-tool`, `dcopen-keyword-search-tool`, `dcopen-semantic-search-tool`, `dcopen-list-namespaces`, `dcopen-list-classes`, `dcopen-class-info`, `dcopen-member-info`, `dcopen-run-snippet-tool`, `dcopen-run-journal-tool`, `dcopen-execute-tool`, `explore-model-structure`, `read-model-data`; `documentation-search-tool` only if advertised in the current catalog (unverified) |
| Product Support | `search` (product=STS_SIMCENTER3D for Nastran; HyperMesh for OptiStruct) |
| Simcenter Nastran MCP | `parse_f06_file`, `parse_contact_log`, `diagnose_sol401_failure_context`, `classify_simulation_intent`, `compare_decks`, `search_file`, `read_file_excerpt`, `resolve_elements`, `list_deck_cards`, `read_deck_cards`, `discover_job`, `list_allowed_roots`, `request_file_access` |
| Batch Post | see host skill `batchpost-actions` (exports, contours, CSV, templates) |

## Subagents
fea-model-inspector (read Simcenter 3D / CAD state), fea-journal-author (NXOpen discovery and sandbox journals only; no live execution), fea-solver-diagnostics (Nastran MCP F06/deck tools, read-only), fea-results-post (Batch Post exports; no Nastran ref), fea-verifier (analytical/independent checks on data passed by parent; no live reads), product-support-agent (documentation).

## 20 fea-* skills to stage
| Skill | Stages | Subagents |
|---|---|---|
| [fea-acceptance-verifier](../../fea-acceptance-verifier/SKILL.md) | verification | fea-verifier |
| [fea-artifact-forensics](../../fea-artifact-forensics/SKILL.md) | deck, results | fea-solver-diagnostics, fea-results-post |
| [fea-chief-engineer](../../fea-chief-engineer/SKILL.md) | all (orchestration) | all |
| [fea-composite-laminates](../../fea-composite-laminates/SKILL.md) | BC/load, deck, results | fea-solver-diagnostics, fea-results-post |
| [fea-connector-contact](../../fea-connector-contact/SKILL.md) | BC/load, deck, solve diagnostics | fea-model-inspector, fea-solver-diagnostics |
| [fea-continuum-thermomechanics](../../fea-continuum-thermomechanics/SKILL.md) | deck, results | fea-solver-diagnostics |
| [fea-durability](../../fea-durability/SKILL.md) | results | fea-results-post |
| [fea-dynamics](../../fea-dynamics/SKILL.md) | deck, results | fea-solver-diagnostics, fea-results-post |
| [fea-materials-properties](../../fea-materials-properties/SKILL.md) | inventory | fea-model-inspector |
| [fea-mesh-quality](../../fea-mesh-quality/SKILL.md) | mesh | fea-model-inspector |
| [fea-modal-correlation](../../fea-modal-correlation/SKILL.md) | results | fea-results-post |
| [fea-model-preparation](../../fea-model-preparation/SKILL.md) | inventory, mesh, BC/load | fea-model-inspector, fea-journal-author |
| [fea-multistep-nonlinear](../../fea-multistep-nonlinear/SKILL.md) | deck, solve diagnostics | fea-solver-diagnostics |
| [fea-native-runtime-gate](../../fea-native-runtime-gate/SKILL.md) | journals, capability discovery | fea-journal-author |
| [fea-open-meshing](../../fea-open-meshing/SKILL.md) | mesh (non-Siemens Gmsh; no host tool) | none (source side) |
| [fea-random-response](../../fea-random-response/SKILL.md) | results | fea-results-post |
| [fea-results-interpretation](../../fea-results-interpretation/SKILL.md) | results | fea-results-post (Batch Post); F06 via fea-solver-diagnostics |
| [fea-solver-investigation](../../fea-solver-investigation/SKILL.md) | deck, results, inventory | fea-solver-diagnostics, fea-model-inspector |
| [fea-thermal](../../fea-thermal/SKILL.md) | BC/load, results | fea-model-inspector, fea-results-post |
| [fea-vvuq-review](../../fea-vvuq-review/SKILL.md) | mesh, verification | fea-verifier |

## Capability gaps
| Gap | Status |
|---|---|
| Mesh generation/visibility are advertised live mutations (main agent only, explicit request, owned copy, `mesh-info-tool` readback); BC/load/solution/solve/save mutation not advertised | BLOCKED_BY_OFFICIAL_MCP_CAPABILITY |
| No solve/submit tool advertised | BLOCKED_BY_OFFICIAL_MCP_CAPABILITY / NOT_RUN |
| No save tool advertised | discover; otherwise journal route only on explicit request |
| Simcenter 3D not connected / tools missing | run `dc_connection_status`, follow recovery; stages NOT_RUN |
| Nastran deck/F06 outside allowed roots | `list_allowed_roots`, `request_file_access` (approval per job bundle) |
| Nastran MCP tools are SOL 401 oriented | state limits when applied to SOL 101; parse_f06_file/list_deck_cards remain usable read-only |
