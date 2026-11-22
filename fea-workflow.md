# Simcenter 3D FEA workflow

Use the globally configured official Siemens MCPs. Start a whole study with [FEA Chief Engineer](skills/fea-chief-engineer/SKILL.md). For a focused request, start with its outcome below and open supporting references as needed.

| Requested outcome | Start here |
|---|---|
| Read CAD features, dimensions, expressions or assembly structure | [Live CAD model data](skills/designcenter-open-model-data-read/SKILL.md) |
| Identify CAD, FEM, AFM or SIM ownership, or choose an idealization | [Model preparation](skills/fea-model-preparation/SKILL.md) |
| Read active CAE bodies or assigned materials | [Body and material inspection](skills/simcenter-3d-material-and-body-inspection/SKILL.md) |
| Inventory mesh collectors, types, counts and properties | [Mesh inspection](skills/simcenter-3d-mesh-inspection/SKILL.md) |
| Retrieve native mesh quality metrics | [Native mesh quality](skills/simcenter-3d-mesh-quality-review/SKILL.md) |
| Decide whether the mesh resolves an engineering quantity | [Mesh quality](skills/fea-mesh-quality/SKILL.md) |
| Show, hide or select active CAE entities | [Visibility and selection](skills/simcenter-3d-visibility-and-selection/SKILL.md) |
| Generate or edit a native mesh | [Mesh generation](skills/simcenter-3d-mesh-generation/SKILL.md) |
| Check mapped loads, flux or geometry-to-mesh conservation | [Boundary transfer](skills/fea-open-meshing/SKILL.md) |
| Inspect loads, constraints, effective solution or step scope | [Boundary condition inspection](skills/simcenter-3d-simulation-boundary-conditions/SKILL.md) |
| Read SIM/AFM links, solution setup or saved result references | [Qualified CAE operations](skills/designcenter-open-journal-authoring/references/cae-2612.md) for the matching build |
| Resolve an unfamiliar API, write a journal or retrieve vendor documentation | [API discovery](skills/designcenter-open-api-discovery/SKILL.md) for a member, [journal authoring](skills/designcenter-open-journal-authoring/SKILL.md) for code, [documentation search](skills/designcenter-open-documentation-search/SKILL.md) for a source |
| Run a solver job or explain a solver setup or termination | [Solver investigation](skills/fea-solver-investigation/SKILL.md), including its Solution Sequence for submission |
| Inspect exact deck syntax, effective selectors or deck closure | [Simcenter Nastran](skills/simcenter-nastran/SKILL.md) |
| Trace a deck, log or result file to its producing run | [Artifact forensics](skills/fea-artifact-forensics/SKILL.md) |
| Extract data, create plots or author a BatchPost configuration | [BatchPost](skills/batchpost-actions/SKILL.md) |
| Interpret an FEA quantity or report its physical meaning | [Results interpretation](skills/fea-results-interpretation/SKILL.md) |
| Evaluate a specific engineering acceptance claim | [Acceptance verifier](skills/fea-acceptance-verifier/SKILL.md) |
| Design or assess a verification, validation or uncertainty study | [VVUQ](skills/fea-vvuq-review/SKILL.md) |
| Assess static stiffness, load history, joints, or stability | [Static structural routing](skills/fea-sc3d-tool-routing/references/static-routing.md) |
| Choose a modal, frequency response, transient, shock, random or NVH method | [Dynamics by requested output](skills/fea-sc3d-tool-routing/references/dynamics-routing.md) |
| Build an integrated airframe verification | [Airframe verification](skills/simcenter-airframe-structural-verification/SKILL.md) |

Use [tool routing](skills/fea-sc3d-tool-routing/SKILL.md) when a task needs a Siemens profile or recovery. Use the [runtime gate](skills/fea-native-runtime-gate/SKILL.md) for qualified native operations requiring controlled dispatch and independent readback. The [persistence method](skills/fea-native-runtime-gate/references/native-persistence.md) defines save and reopen for an isolated 2612 batch chain and what an active interactive model requires.

Keep file lookups inside the task workspace and authorized roots. Continue independent stages when a profile or artifact is unavailable. Report what the available evidence establishes and the specific dependency for any unfinished stage.
