# Shared FEA CLI v1

Use the scripts directory from the verified checkout or attested project. Run `python -B -X utf8 <scripts>/fea_cli.py` with Python 3.12. Create one task-owned runtime root, typically `.work/fea-runtime`, and give all cooperating runs for the same host that root.

| Command | Behavior |
|---|---|
| `capabilities search --query TEXT [--domain DOMAIN]` | List known semantic capabilities from the local registry. |
| `capabilities describe ID` | Show ownership, execution surface, inputs, outputs and qualification scope. |
| `operation validate --request FILE` | Validate strict UTF-8 JSON and return the exact request, binding and effect digests for caller review. |
| `sc3d prepare`, `nastran prepare`, `batchpost prepare` | Admit an operation into the common ledger using `--root`, `--request` and the applicable `--authority`. |
| `operation reserve`, `operation record`, `operation observe`, `operation reconcile` | Reserve the checked payload, preserve the response or failure, and apply fresh independent observations. |
| `sc3d batch`, `nastran submit` | Explicit Windows isolated execution with `--product`, a fresh owned output scope and a caller grant for effects. |
| `nastran inspect`, `nastran verify` | Read an exact deck closure or run a supported independent engineering check over bound local bytes. Pure local reads write one terminal receipt. |
| `operation reconcile-job` | Recheck the retained original job, its staged input hashes and terminal files after a client interruption. |
| `run status`, `run next`, `artifact inspect --id ID` | Return compact operation projections and verify artifact bytes before returning metadata or a bounded contour CSV row slice. |

The transport emits JSON with contract version, command status, execution status, engineering disposition and available identities. Exit 0 indicates the requested command completed, including a successful prepare. Other exit codes are 2 for invalid input, 3 for authority rejection, 4 for unavailable or uncertain execution, 5 for runtime or read failure and 6 for completed engineering rejection. `ACCEPTED` execution confirms the declared operation predicates. Physical acceptance requires engineering evidence and its own disposition.

## Isolated native mutations

Run the following capabilities with the existing sc3d batch command. Bind the exact writable file in the file target with its SHA-256. Place the related files in the declared owned scope and supply the read-only dependency digest. Use an unregistered disposable copy for a writable target. Previously retained artifacts keep their original bytes.

| Capability | Explicit scoped input | Native evidence |
|---|---|---|
| sc3d.bc.scale_nodal_force | SIM and FEM paths, FEM SHA-256, and load object with exact solution, step, name, sorted grid_labels, scale_before and scale_after | Exact NodeIDTableForce membership and basic-frame FORCE rows, target magnitude change, other BC fingerprint, unchanged FEM and fresh clean SIM reopen. The scale values are the native ScalingForce property values on this profile. |
| sc3d.mesh.refine_region | FEM and CAD paths, CAD SHA-256, and region object with cad_body, cad_face, guard_body, sorted unique face_vertices_mm and size_mm | Native CAD-to-polygon binding, persisted face control, reduced median edge length, increased local edge count, unchanged guard connectivity and coordinates, unchanged CAD and fresh reopen. Current scope is standalone millimeter CAD and a meshed linear tetrahedral region. |

Both operations carry the installed run_journal executable hash, a deadline, the caller grant and native_state predicates UNLAUNCHED and VERIFIED. Acceptances include the before and after scoped measurements. Mesh-control inspection may mark a reopened FEM dirty in memory. The receipt records dirtiness before and after inspection and requires saved bytes and the CAD dependency to remain unchanged during readback.

## Request and authority

Validate and prepare take a document with `operation` and `binding`. The operation contains `version`, `run_id`, `operation_id`, `capability`, `target`, `args`, `dependencies`, `expected` and `output_scope`. The optional `input_artifacts` list connects exact accepted artifacts. Same-run artifact inputs carry accepted producer IDs in `dependencies`. Effect operations also carry `baseline`, `deadline` and `authorization_ref`.

The binding carries the observed target, `evidence_ref` and `observed_at`. Live host bindings include the actual profile, advertised catalog, catalog digest, exact tool and descriptor digest. Effectful host bindings also require the applicable qualification and ownership evidence. SC3D targets identify the native process and exact model, roles, owner and occurrence. Use an observed revision where exposed or a scoped precondition digest. Nastran targets identify the release, executable hash, job directory and effective deck closure. BatchPost targets identify the particular worker, result hash and exact catalog for selection. File targets identify workspace-relative bytes and schema.

An approved caller transmits a separate grant to `--authority` with `ref`, `effect`, `request_digest` and `binding_digest`. The host owns authorization and transport. Reserve rechecks that exact authority, dependencies, binding and a fresh observation of the effect baseline. An exact predicate binds JSON types and values. A numerical predicate binds the value, absolute and relative tolerance, units, dimension and frame.

## Host dispatch and recovery

For direct Codex, Copilot and Agent Workspace use the installed official tool after reserve returns its exact function and arguments. Record its raw reply with the run and operation IDs. Observe independently using the same target, a fresh timestamp, an independent evidence reference, scoped witnesses, explicit coverage and settlement evidence. Optional programmatic calling uses the host-provided session in the [adapters](official-mcp-adapter.md). See [native persistence](native-persistence.md) for isolated files and [job controls](../../fea-solver-investigation/references/solution-sequence.md) for the deck authority.

A resource fence survives restart. Reconciliation requires fresh read-only evidence and settlement before accepting a match to the baseline as `NOT_APPLIED`. A timeout retains the original reservation and can require clarification from the native job or session. Cooperating clients serialize effects with the same root and observed resource identity. External GUI and unrelated clients can still change the resource.

An old controller ledger remains readable through its legacy entry points, including reconciliation of legacy receipts. Use a single canonical current root and retain the existing root for legacy history. Admission of v1 operations in a legacy root switches new dispatch to v1. Back up the ledger and original evidence before migrating or changing versions. For rollback use the matching backed-up controller and its original root and reconcile pending operations before resuming effects.

Schema validation uses the [host dependency pins](../scripts/fea_runtime/requirements-host.txt). Independent numerical dependencies and method applicability are described in [engineering provenance](engineering-provenance.md). Install dependencies explicitly in the selected environment using approved wheels, for example with `pip install --no-index --find-links <wheelhouse> -r <requirements>`. Help, registry lookup and base deck inventory use the standard library.
