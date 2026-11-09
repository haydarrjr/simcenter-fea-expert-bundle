---
name: fea-sc3d-tool-routing
description: Route FEA stages (inventory, mesh, BC/load, deck, solve, results, verification, docs) of the fea-* skills to the real Simcenter 3D host tools and subagents (Simcenter 3D model-inspection, Designcenter Open, Product Support, Simcenter Nastran MCP, Batch Post). Use when deciding which tool or subagent performs an FEA step, when a tool is missing or SC3D is not connected, or to report capability gaps such as BLOCKED_BY_OFFICIAL_MCP_CAPABILITY.
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Simcenter 3D tool routing for FEA skills

Rules:
1. **Never invent tool names.** List the current tool catalog at the start of each session and use only what is advertised. The names in [tool matrix](references/tool-matrix.md) were observed in installed host bundles and may change by release.
2. Host references: "Simcenter 3D" (model inspection), "Designcenter Open" (NXOpen discovery/journals/model reads), "Product Support" (documentation `search`), "Simcenter Nastran MCP" (read-only deck/F06), "Batch Post" (result post-processing).
3. Live mutation: mesh generation (`solid-mesh-generation-tool`, `surface-mesh-generation-tool`) and visibility tools are advertised live mutations; they are called only by the main agent after an explicit user request, on an owned copy, with `mesh-info-tool` readback. BC/load/solution/solve/save mutation is not advertised -> BLOCKED_BY_OFFICIAL_MCP_CAPABILITY. Live journal execution (`dcopen-execute-tool`) is main-agent only after explicit authorization. Read-only subagents have `available_tools` allowlists on their refs. Names marked dcopen-* must be discovered in the current catalog.
4. Report gaps explicitly; never emulate a missing capability by guesswork.

## Stage to route
| Stage | Primary route | Subagent | Fallback / gap |
|---|---|---|---|
| Connection | `dc_connection_status` (both Simcenter 3D and Designcenter Open expose it) | fea-model-inspector | Not connected: follow the recovery guidance of host skills `simcenter-3d-connection-status` / `designcenter-open-connection-status`; stages stay NOT_RUN |
| Inventory | `part-info-tool`, `body-info-tool`, `material-info-tool`; CAD: `explore-model-structure` then `read-model-data` | fea-model-inspector | - |
| Mesh | read `mesh-info-tool`, `mesh-quality-tool` (fea-model-inspector); create `solid-mesh-generation-tool`, `surface-mesh-generation-tool` = live MUTATION, main agent only, explicit user request, owned copy, `mesh-info-tool` readback | fea-model-inspector (read) / main agent (mutation) | Other mesh edits: journal draft by fea-journal-author, live run by main agent; else BLOCKED_BY_OFFICIAL_MCP_CAPABILITY |
| BC / load | read `boundary-condition-tool` | fea-model-inspector | **BC/load/solution/solve/save mutation not advertised** -> BLOCKED_BY_OFFICIAL_MCP_CAPABILITY unless a journal is drafted in sandbox (MCP_2612_DISCOVERED-level, "sandbox, not live") and the user explicitly asks the main agent to run it |
| Deck | Nastran MCP: `list_allowed_roots`, `request_file_access`, `discover_job`, `list_deck_cards`, `read_deck_cards`, `compare_decks`, `classify_simulation_intent` | fea-solver-diagnostics | Read-only; edits are manual instructions |
| Solve | none observed | - | BLOCKED_BY_OFFICIAL_MCP_CAPABILITY / NOT_RUN unless a solve tool is discovered |
| Results | F06/log tools (`parse_f06_file`, `parse_contact_log`, `diagnose_sol401_failure_context`, `search_file`, `read_file_excerpt`, `resolve_elements`) belong to fea-solver-diagnostics; export/contours via Batch Post by fea-results-post (no Nastran ref) | fea-solver-diagnostics, fea-results-post | OP2 beyond Batch Post: source-side [fea-artifact-forensics](../fea-artifact-forensics/SKILL.md) |
| Verification | independent analytical checks on data passed by the parent (no live reads) | fea-verifier | status PASS/FAIL/PARTIAL/NOT_RUN/UNVERIFIED |
| Docs | Product Support `search` (primary); `documentation-search-tool` only if advertised in the current Designcenter Open catalog | product-support-agent | cite; mark unverified if inconclusive |
| Journals | `dcopen-pattern-lookup-tool`, `dcopen-keyword-search-tool`, `dcopen-semantic-search-tool`, `dcopen-list-namespaces`, `dcopen-list-classes`, `dcopen-class-info`, `dcopen-member-info`, `dcopen-run-snippet-tool`, `dcopen-run-journal-tool` (sandbox only; discover in current catalog). Live `dcopen-execute-tool`: main agent only after explicit authorization | fea-journal-author (sandbox) / main agent (live) | - |

## Skill to stage
See the table in [tool matrix](references/tool-matrix.md) for all 20 fea-* skills. Pilot workflow: [simcenter-parametric-sol101](../simcenter-parametric-sol101/SKILL.md). Airframe & Aerostructures workflows: [simcenter-airframe-structural-verification](../simcenter-airframe-structural-verification/SKILL.md), [simcenter-aerostructures-load-filtering](../simcenter-aerostructures-load-filtering/SKILL.md), and [simcenter-aerostructures-margin-of-safety](../simcenter-aerostructures-margin-of-safety/SKILL.md).
