---
name: simcenter-parametric-sol101
description: Build, update and accept a parametrically defined SOL101 cantilever beam pilot (CAD metadata, semantic selections, FEM/SIM, material, clamp and tip load, Euler-Bernoulli and mesh-convergence acceptance) using the real Designcenter Open, Simcenter 3D model-inspection, Product Support and Simcenter Nastran MCP tools. Use for this structural benchmark, reusable cantilever automation, or to judge PASS/FAIL/PARTIAL/NOT_RUN/UNVERIFIED status of such a workflow.
---

# Parametric SOL101 workflow (cantilever pilot)

This recipe is not proof that a host has passed the workflow. Report unsupported stages NOT_RUN and completed stages separately. Tool routing details: [fea-sc3d-tool-routing](../fea-sc3d-tool-routing/SKILL.md). Native-write gating: [fea-native-runtime-gate](../fea-native-runtime-gate/SKILL.md). Acceptance judgement: [fea-acceptance-verifier](../fea-acceptance-verifier/SKILL.md). Mesh convergence: [fea-mesh-quality](../fea-mesh-quality/SKILL.md).

## Ground rules
- **Never invent tool names.** Discover the current tool catalog each session; use only tools actually listed. Host names: "Simcenter 3D" (model-inspection tools), "Designcenter Open", "Product Support", "Simcenter Nastran MCP", "Batch Post".
- **Live execution needs an explicit user request.** Read-only inspection is the default. Solve and save capability must be *discovered*, not assumed; if no tool advertises it, the stage is `BLOCKED_BY_OFFICIAL_MCP_CAPABILITY` / NOT_RUN.
- Work on an **owned copy** (new operator-owned model); never overwrite the user's active model.
- **Environment gate:** before any FEM/SIM operation confirm that the Simcenter 3D environment is **Pre/Post** (not Motion). If it cannot be confirmed or switching cannot be verified, stop without FEM/SIM operations. Confirm connectivity first with `dc_connection_status` (recovery: see `simcenter-3d-connection-status` / `designcenter-open-connection-status` host skills).
- Resolve Simcenter 3D release and NX Open release independently. Do not authorise API calls from mismatched-release documentation; inspect the selected member first.

## Inputs
Length, rectangular width/height, isotropic E/nu/density, transverse force, mesh size, explicit consistent units. Check positive dimensions, stable Poisson ratio, slenderness, force direction.

## Steps: route, readback, evidence class
Evidence classes: SOURCE_TESTED, DOCUMENTED_2606_CANDIDATE, MCP_2612_DISCOVERED, HOST_QUALIFIED, NATIVE_EXECUTED, SOLVER_VERIFIED, ENGINEERING_ACCEPTED. A step's class is the highest *actually evidenced*; plans/documentation alone give at most DOCUMENTED_2606_CANDIDATE.

| # | Step | Tool route | Required readback | Max class without host proof |
|---|---|---|---|---|
| 0 | Connection + environment gate | `dc_connection_status`; `part-info-tool` | connected, Pre/Post confirmed, active part identity | MCP_2612_DISCOVERED |
| 1 | Discover API | `dcopen-pattern-lookup-tool`, `dcopen-keyword-search-tool`, `dcopen-semantic-search-tool`, `dcopen-list-namespaces`, `dcopen-list-classes`, `dcopen-class-info`, `dcopen-member-info`; docs via Product Support `search` (`documentation-search-tool` only if advertised in the current catalog); dcopen-* names: discover in current catalog | exact member signature, release | DOCUMENTED_2606_CANDIDATE |
| 2 | Parametric CAD create/update (owned copy) | test in `dcopen-run-snippet-tool` / `dcopen-run-journal-tool` sandbox first (sandbox, not live; MCP_2612_DISCOVERED-level); live change only by the main agent on explicit user request via `dcopen-execute-tool` (discover in current catalog) | `explore-model-structure` then `read-model-data`: expressions, features, bodies | NATIVE_EXECUTED (after live run + readback) |
| 3 | Semantic support/load attributes | same journal routes | attributes read back with `read-model-data` | NATIVE_EXECUTED |
| 4 | Selection recipes, entity counts | `read-model-data`; `body-info-tool`; `mesh-info-tool` (node/element sets) | expected counts, geometry region, resultant | HOST_QUALIFIED |
| 5 | Create FEM/SIM, material, mesh | discover capability: `solid-mesh-generation-tool`, `surface-mesh-generation-tool`, journal route; `material-info-tool` | mesh type, element count, material per body | NATIVE_EXECUTED |
| 6 | Clamp + tip force | discover capability; if no mutation tool, BLOCKED_BY_OFFICIAL_MCP_CAPABILITY; verify with `boundary-condition-tool` | type, applied objects, values, units, completeness | NATIVE_EXECUTED |
| 7 | Mesh quality | `mesh-quality-tool` | AR, skew, Jacobian, free edges | HOST_QUALIFIED |
| 8 | Validate exported SOL101 deck | Simcenter Nastran MCP read-only: `list_allowed_roots`/`request_file_access`, `discover_job`, `list_deck_cards`, `read_deck_cards`, `compare_decks` | SPC/FORCE/MAT1/PSOLID cards match inputs | HOST_QUALIFIED |
| 9 | Solve (only if a solve tool is discovered and user asked) | none known; do not assume | job id, termination evidence | SOLVER_VERIFIED |
| 10 | Solver evidence | `parse_f06_file`, `search_file`, `read_file_excerpt`, `diagnose_sol401_failure_context` (SOL 401 only) | no FATAL, termination, subcase | SOLVER_VERIFIED |
| 11 | Results: displacement, reaction, stress | `parse_f06_file`; Batch Post (`batchpost-actions`) for export/contours | tip displacement, reaction sum, stress away from clamp | SOLVER_VERIFIED |
| 12 | Contour/probe GUI acceptance | no tool; separate manual/GUI evidence | screenshot/receipt | NOT_RUN unless evidenced |
| 13 | Three parameter updates | repeat 2-6 with length, section, load | links and counts preserved; no duplicates | NATIVE_EXECUTED |
| 14 | Engineering acceptance | independent hand calc + [fea-acceptance-verifier](../fea-acceptance-verifier/SKILL.md) | criteria below | ENGINEERING_ACCEPTED |

Metadata identifies intent, not transient face/node tags. On update, re-resolve semantic selections and verify entity counts, region and resultant load. Re-execution must edit existing owned entities or fail explicitly, never duplicate. Store recipe, parameters and provenance with engineering artifacts.

## Acceptance criteria
- Reaction balance within **0.5 %**.
- Slender-beam tip deflection within **3 %** of Euler-Bernoulli (PL^3/3EI).
- Three mesh levels; final displacement change **< 2 %**.
- Stresses measured **away from the clamp singularity**.
- Three parameter updates preserve support/load links and entity counts.
- GUI acceptance separately needs parameter-dialog edit, navigator selection and contour/probe control.

## Status vocabulary
Use PASS, FAIL, PARTIAL, NOT_RUN, UNVERIFIED precisely. CAD-only, imported deck, analytical reference or offline unit tests are PARTIAL; they do not establish associative FEM/SIM updateability or licensed solver/GUI acceptance. Full PASS needs FEM/SIM, exported deck, licensed solve, reaction/displacement checks, associative updates and separate GUI acceptance. Unknown outcome after a timeout: UNVERIFIED; re-read state before retrying.

Read the [retrieval presentation contract](references/retrieval-presentation-contract.md). Historical qualification notes: [qualification history](references/qualification-history.md) (not current status).
