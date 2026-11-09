# Siemens 2606 evidence and local Codex handoff

## Release-bound documentation

The bounded evidence ledger (source: fea_expert_agent_plugin/docs/evidence/siemens-2606-idealization-ledger.json)
records the canonical document IDs, release SKUs, raw source hashes, retrieval
time, content status and adopted claim. It contains summaries/metadata, not
copies of Siemens manuals. Read the relevant document through Siemens Help
Server when preparing a release-specific native implementation.

| Product/release | Document ID suffix | Adopted rule and its limit |
|---|---|---|
| Simcenter 3D 2606, PL20251024315444291 | `design.id625426` | Geometry idealization belongs to the idealized derivative and preserves original CAD. The source comparison performs no derivative operation. |
| Simcenter 3D 2606 | `advanced.id781576` | Beam section definition, assignment, orientation and offsets are distinct modeling steps. Scalar area alone cannot prove section adequacy. |
| Simcenter Nastran 2606, PL20251024315120185 | `element.id489151` | CBEAM provides beam mechanics including bending/shear and section variation; the analytic evaluator is not an implementation/qualification of that native element. |
| Simcenter Nastran 2606 | `element.id489051` | Element orientation determines section directions. Local y/depth and z/bending moment must be mapped explicitly. |
| Simcenter Nastran 2606 | `QRG.id508621` | PBEAM remark 12 distinguishes zero/nonzero shear fields for EB/Timoshenko, independently by plane. This does not establish that analytical kappa is numerically identical to a card field. |
| Simcenter 3D 2606 | `advanced.id625621`, `advanced.id629976` | Midsurface source association and effective shell thickness/normal/offset require separate checks. A vendor sampling switch is not an engineering error budget. No shell algorithm is implemented by this slice. |

Ledger status is DRAFT for these source documents. Twelve of thirteen retrieved
records reported COMPLETE and one PARTIAL. Equation images were unavailable in
some otherwise COMPLETE text; no taper/shear-relief equation is adopted from
missing images. Native availability, installed SDK signatures and numerical
parity are not inferred from documentation completeness.

## What Codex must qualify locally

The source callable entry points are `section_properties`, `analyze_beam`,
`assess_idealization`, and `assess_preparation_request`. They already execute
offline. None calls NXOpen or requires Windows to perform its calculation.
The following adapters/evidence are still required locally:

1. **Geometry and ownership extraction.** Read actual body/revision, idealized
   source association, section dimensions/common centroid, axes and protected
   feature identity. Map the part frame to the declared local frame. Validate
   the installed NXOpen SDK signatures before implementing readers/builders.
2. **Section/material/support assignment.** Construct appropriate native beam
   properties and orientation; inspect effective offsets, density, E/G/nu and
   root boundary behavior. Resolve the exact PBEAM/CBEAM shear convention from
   the installed release. The source package emits no new BDF or journal.
3. **Native model changes.** Use the shared Runtime for every model/file effect,
   preserving originals and native ownership. Reconcile semantic selections and
   protected regions after modification using `reconcile_selection_recipe`
   (`fea.selection-recipe-intent.v1` -> `fea.selection-reconciliation.v1`),
   `plan_associative_retrofit_or_rebind`, `evaluate_mesh_and_connection_replay`,
   and `plan_sim_rebind`, separating `SOURCE_TESTED` / `DOCUMENTED_2606_CANDIDATE`
   source verification from `NATIVE_READBACK_VERIFIED` `SelectionRecipe.GetEntities()`
   persistence. See parametric CAE qualification (source: fea_expert_agent_plugin/docs/qualification/parametric-cae-v1.md).
   This PR adds no Runtime handler or MCP contract and changes no NX/Runtime branch.
4. **Solver and discretization validation.** Run controlled SOL101 models on the
   licensed host for the original/proposed sections and both intended theories.
   Refine the beam mesh at load/section discontinuities and along uniform spans;
   preserve the exact QoIs. Inspect shear locking, end-release/offset effects,
   reactions, section forces, displacement, energy and sign conventions.
5. **Physical model validation.** Compare a suitably refined shell/solid/local
   model or experiment for beam hypotheses, attachment compliance and local
   feature stresses. Document location, averaging, singularity and material
   assumptions. The source difference budget cannot substitute for this step.
6. **Return defects with reproducible evidence.** Include source request/report,
   repository commit, product build and SDK, generated model/deck hashes,
   effective property/coordinate mapping, solver logs, result location/unit
   semantics, refinement history and expected-versus-observed quantities.

The historical fixture registry remains unchanged. Source tests supply bounded
algorithm evidence; SDK compilation, native execution, solver acceptance and
real engineering acceptance remain separate and unperformed here.
