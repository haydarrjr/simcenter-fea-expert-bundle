---
name: fea-sc3d-tool-routing
description: Route FEA stages (inventory, mesh, BC/load, deck, solve, results, verification, docs) of the fea-* skills to the real Simcenter 3D host tools and subagents (Simcenter 3D model-inspection, Designcenter Open, Product Support, Simcenter Nastran MCP, Batch Post). Use when deciding which tool or subagent performs an FEA step, when a tool is missing or SC3D is not connected, or to report capability gaps such as BLOCKED_BY_OFFICIAL_MCP_CAPABILITY.
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Simcenter 3D tool routing for FEA skills

Use the installed global host definitions. Select the profile by operation. Use Designcenter Open directly for CAD model data and NXOpen in a plain Designcenter session. Use Simcenter 3D Model Inspection for FEM/SIM inventory, mesh quality and boundary conditions. For tasks that need both, bind each to the intended model using its own advertised tools. Use the global BatchPost connector and Siemens Help Server. Use Nastran MCP only when its deck/log tools are advertised. The [Solution Sequence](../fea-solver-investigation/references/solution-sequence.md) uses the installed Siemens batch solver and SCD5 converter for authorized jobs. Live model access and journal execution stay on official MCP. Do not install alternate readers or solvers.

Rules:
1. **Never invent tool names.** List the current tool catalog at the start of each session and use only what is advertised. The names in [tool matrix](references/tool-matrix.md) were observed in installed host bundles and may change by release.
2. Host references: "Simcenter 3D" (model inspection), "Designcenter Open" (NXOpen discovery/journals/model reads), "Product Support" (documentation `search`), "Simcenter Nastran MCP" (read-only deck/F06), "Batch Post" (result post-processing).
3. Use advertised mesh generation and visibility mutations only after an explicit request, on an owned copy, with readback. For solution setup and deck export, qualify the live Designcenter Open journal and its exact operation on the identified working copy. Run it through the current official MCP with the authorized scope and read back the effect. Read-only subagents use their tool allowlists. The user saves the SIM/FEM.
4. Check `dc_connection_status` on the selected profile. A missing host tool, a disconnected profile and a connected session without an active part are distinct observations. On `DCMCP-E002`, report the affected profile and remedy. Continue any requested stage supported by a connected profile or available result file.
5. Choose results from an explicit path or an exact saved result path returned by authorized MCP. Keep lookups inside the workspace and user-authorized roots. Request the path when the target is unresolved.

## Stage to route
| Stage | Primary route | Subagent | Fallback / gap |
|---|---|---|---|
| CAD connection and inventory | Designcenter Open `dc_connection_status`, `explore-model-structure`, then `read-model-data` | fea-model-inspector | Follow `designcenter-open-connection-status`; a connected empty session needs an active CAD part for model data |
| FEM/SIM connection and inventory | Simcenter 3D Model Inspection `dc_connection_status`, `part-info-tool`, `body-info-tool`, `material-info-tool` | fea-model-inspector | Follow `simcenter-3d-connection-status`; report only affected FEM/SIM stages as NOT_RUN |
| Mesh | read `mesh-info-tool`, `mesh-quality-tool` (fea-model-inspector); create `solid-mesh-generation-tool`, `surface-mesh-generation-tool` = live MUTATION, main agent only, explicit user request, owned copy, `mesh-info-tool` readback | fea-model-inspector (read) / main agent (mutation) | Other mesh edits: journal draft by fea-journal-author, live run by main agent; else BLOCKED_BY_OFFICIAL_MCP_CAPABILITY |
| BC / load | read `boundary-condition-tool`; qualify each requested change through the native runtime gate | fea-model-inspector (read) / main agent (mutation) | Mark unqualified live changes as BLOCKED_BY_OFFICIAL_MCP_CAPABILITY |
| Deck | qualified Designcenter Open journal exports with `WriteSolverInputFile`; Nastran MCP inspects the exact deck when exposed | main agent (export) / fea-solver-diagnostics (read) | Inspect the scoped original deck/F06 text when Nastran MCP is unavailable |
| Solve | [Solution Sequence](../fea-solver-investigation/references/solution-sequence.md) through installed Siemens Nastran batch executable | main agent | Require the exact deck and new solver log/F06 completion |
| Results | F06/log tools (`parse_f06_file`, `parse_contact_log`, `diagnose_sol401_failure_context`, `search_file`, `read_file_excerpt`, `resolve_elements`) belong to fea-solver-diagnostics; export/contours via Batch Post by fea-results-post (no Nastran ref) | fea-solver-diagnostics, fea-results-post | Unexposed fields remain unavailable; use [fea-artifact-forensics](../fea-artifact-forensics/SKILL.md) |
| Verification | independent analytical checks on data passed by the parent (no live reads) | fea-verifier | status PASS/FAIL/PARTIAL/NOT_RUN/UNVERIFIED |
| Docs | Product Support `search` (primary); `documentation-search-tool` only if advertised in the current Designcenter Open catalog | product-support-agent | cite; mark unverified if inconclusive |
| Journals | `dcopen-pattern-lookup-tool`, `dcopen-keyword-search-tool`, `dcopen-semantic-search-tool`, `dcopen-list-namespaces`, `dcopen-list-classes`, `dcopen-class-info`, `dcopen-member-info`, `dcopen-run-snippet-tool`, `dcopen-run-journal-tool` (sandbox only; discover in current catalog). Live `dcopen-execute-tool`: main agent only within qualified controls; discovery and sandbox evidence do not grant persistence, solve or submit | fea-journal-author (sandbox) / main agent (live) | - |

## Skill to stage
See the table in [tool matrix](references/tool-matrix.md) for all 20 fea-* skills. Pilot workflow: [simcenter-parametric-sol101](../simcenter-parametric-sol101/SKILL.md). Airframe & Aerostructures workflows: [simcenter-airframe-structural-verification](../simcenter-airframe-structural-verification/SKILL.md), [simcenter-aerostructures-load-filtering](../simcenter-aerostructures-load-filtering/SKILL.md), and [simcenter-aerostructures-margin-of-safety](../simcenter-aerostructures-margin-of-safety/SKILL.md).
