# Simcenter 3D FEA workflow

Use the globally configured official Siemens MCPs. Avoid duplicate workspace registrations. Use the installed Siemens batch solver and SCD5 converter for authorized jobs. Scope local file work to the job inputs, outputs and reports. Mark unexecuted operations as NOT_RUN.

Load [FEA Chief Engineer](skills/fea-chief-engineer/SKILL.md) and [SC3D Tool Routing](skills/fea-sc3d-tool-routing/SKILL.md) first. Load specialist skill instructions and their references as needed.

| Request | Starting skill |
|---|---|
| Inspect the open CAD part | [Designcenter model data](skills/designcenter-open-model-data-read/SKILL.md) |
| Inspect FEM/SIM, mesh or BC | [Mesh inspection](skills/simcenter-3d-mesh-inspection/SKILL.md), [Boundary conditions](skills/simcenter-3d-simulation-boundary-conditions/SKILL.md) |
| Discover API or prepare and test a journal | [API discovery](skills/designcenter-open-api-discovery/SKILL.md), [Journal authoring](skills/designcenter-open-journal-authoring/SKILL.md) |
| Investigate deck, F06 or contact logs | [Solver investigation](skills/fea-solver-investigation/SKILL.md), [Artifact forensics](skills/fea-artifact-forensics/SKILL.md) |
| Configure, submit and post-process a Nastran batch job | [Solution Sequence](skills/fea-solver-investigation/references/solution-sequence.md) |
| Export or interpret results | [BatchPost](skills/batchpost-actions/SKILL.md), [Results interpretation](skills/fea-results-interpretation/SKILL.md) |
| Evaluate engineering acceptance | [Acceptance verifier](skills/fea-acceptance-verifier/SKILL.md), [VVUQ](skills/fea-vvuq-review/SKILL.md) |
| Create or verify SOL 103 free-free normal modes | [SOL 103](skills/fea-dynamics/references/sol103-free-free.md) |
| Produce technical HTML with genuine results | [Report method](skills/fea-results-interpretation/references/engineering-report.md) |
| Retrieve Siemens documentation | [Documentation search](skills/designcenter-open-documentation-search/SKILL.md) |
| Associative SOL101 or airframe workflows | [SOL101](skills/simcenter-parametric-sol101/SKILL.md), [Airframe](skills/simcenter-airframe-structural-verification/SKILL.md) |

For CAD or NXOpen in plain Designcenter, use the global Designcenter Open profile directly. For FEM/SIM inventory, mesh quality and boundary conditions, use Simcenter 3D Model Inspection. If the task needs both profiles, bind each to the intended model through its own advertised status and tools. Keep the connection status distinct from the active part identity. Preserve file and session lineage across calls. Use read-only calls for read-only tasks. Qualify live edits, deck export and batch submission individually. After a transport failure, keep effectful operations pending until an independent readback resolves the effect. BatchPost has its own result file and worker state. The user saves the SIM/FEM.

For a prepared authorized operation, use the [runtime gate](skills/fea-native-runtime-gate/SKILL.md) and its controller alongside the existing host connection. Treat local attestation, host discovery, native effects and FEA acceptance as separate observations.

## When access or input is missing

- If a needed global profile is missing from the client's tool list, check the host's profile registration and refresh its catalog through the host. Keep that profile distinct from a declared MCP connection failure.
- For Model Inspection `DCMCP-E002`, record the profile, exact error and affected FEM/SIM stages. For an affected FEM/SIM task, ask the operator to enable Model Inspection and reconnect. Requested CAD reads can still proceed via Designcenter Open.
- If Designcenter Open connects but reports no active part, report the missing model target. Run CAD model reads once an active part is available.
- For BatchPost, use an explicitly supplied result file or an exact saved result path returned by an authorized MCP read. Validate that path and call `open` before `list`. A file name, model part path, or previous chat is insufficient to select a result. Ask for the absolute result path if it is missing. Continue an independent results stage if its file is known even when Model Inspection is unavailable.
- Use only the task workspace and explicitly authorized input roots for file lookups. Avoid recursive drive searches and unrelated session history. If the requested report can be written, include completed observations and concrete missing inputs or connection evidence for the remaining stages.
