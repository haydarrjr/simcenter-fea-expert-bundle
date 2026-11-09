# Model preparation as a mechanical reduction

## Contents

1. Obtain ownership and load-path evidence
2. Choose a reduction from the mechanics
3. Preserve hierarchy, frames and interface work
4. Worked mounted-assembly case
5. Native construction and failure recovery

## Obtain ownership and load-path evidence

Inspect the actual part/model hierarchy, material/property source, active SIM
overrides, mesh revision and selected load/constraint regions. A face number,
node label or nonempty selection is not a persistent physical region. Tie a
selection to its owning part, occurrence transform, revision, semantic purpose
and geometric invariants. Re-evaluate membership after topology change or remesh;
never retain a stale finite-element ID list merely because its integers exist.

The source package can audit model graphs, read source artifacts, calculate
section mechanics and aggregate hierarchical mass/inertia. Native geometry
editing belongs to the Runtime. Request an owned work copy and verify the
unchanged original independently of model undo. File export and saving have
separate effects and recovery; deleting a builder cannot undo a saved file.

## Choose a reduction from the mechanics

For an arm or bracket, identify dominant bending, transverse shear, axial and
torsional energies. Euler–Bernoulli assumes negligible transverse shear;
Timoshenko adds shear compliance. For a tip load, the independent terms are
`F L^3/(3 E I)` and `F L/(kappa G A)`. A length/thickness ratio alone is
insufficient when the load acts close to a support, the section changes or the
support compliance dominates. Evaluate the requested QoI against a declared
budget over the entire load-bearing span.

For shells, choose a reference surface and offsets that preserve membrane and
bending lever arms. For beams, retain section axes, shear center and eccentric
load introduction. A very stiff artificial beam is not a neutral replacement
for a rigid connection: it can produce ill-conditioning and impose an unintended
deformation constraint. RBE2-style kinematic constraints and RBE3-style averaging
have different purposes; neither choice is justified solely by solver stability.

Defeaturing is a model-form decision. Removing a fillet may leave displacement
almost unchanged while invalidating peak stress. Keep separate global and local
QoIs. A global energy match never certifies a notch-root fatigue stress. The
[section mechanics](mechanics.md), [decision procedure](decision-procedure.md)
and [support-arm case](worked-case.md) contain the existing quantitative arm
implementation and its boundaries.

## Preserve hierarchy, frames and interface work

For a component, rotate its center inertia with `I_global = R I_local R^T` and
use the parallel-axis term `m ((r.r) I - r r^T)`. Compose occurrence transforms
through the hierarchy; do not rotate a child twice or count assembly mass again
when it already includes its children. The v2 mounted-assembly contract explicitly
requires each component's mass to exclude children. Cycles, duplicate instances,
missing parents, nonproper rotations and physically unrealizable inertia are
rejected before solving.

At an interface point r, rigid motion is `u(r)=u0 + theta x r = B(r) q`.
The work-conjugate load is `Q = sum B(r)^T f(r)`, containing both resultant
force and moment. Therefore `sum f.u = Q.q`. A transfer that preserves force
but omits `r x f` changes the model's work and load path. Model revision and
frame must match before comparing these quantities.

## Worked mounted-assembly case

Run `python -m fea_agent assess-assembly examples/engineering_v2/mounted_assembly_model.json`.
The example is a manufactured housing, gearbox and nested accessory with
different occurrence orientations, off-center inertia and four tilted mounts.
Their exclusive masses are 90, 25 and 3 kg. Aggregation gives **118 kg** and
center approximately `(0.112392, 0.0130494, 0.0397458) m`. The reference-origin
mass matrix has nonzero translation/rotation coupling; deleting those terms
would change the modes even if total mass stayed correct.

Two interface loads at x = -0.5 and +0.5 m are respectively -1000 and
3000 N in Z. Their resultant is 2000 N in Z and **-2000 N m about Y**.
For the supplied virtual displacement, boundary and reduced work are both
3 J. The wrong-looking-right alternative `[0,0,2000,0,0,0]` passes a force-only
check but is rejected for a 2000 N m moment defect.

Independent tests translate the entire reference origin and rotate the whole
assembly. Frequencies and physical point displacement remain invariant after
the corresponding force/moment and inertia transformations. Changing the
arbitrary numerical characteristic length also leaves the physics unchanged.

## Native construction and failure recovery

Use the verified vendor workflows (source: fea_expert_agent_plugin/docs/engineering/vendor-api-workflows.md)
to bind geometry ownership and exact API declarations. The pressure compiler
audits per-face normal, area, centroid, owner and revision before emission.
Its 2 MPa example acts on 0.01 m² and produces -20 kN in the defined direction;
the opposite surface has the same area and centroid but the wrong normals and
is rejected. This is more discriminating than checking selection cardinality.

Use existing graph/region audits for CAD–idealized part–FEM–AFEM–SIM dependencies,
and the current Runtime client for qualified observations. For persistent CAE
Selection Recipes (`fea.selection-recipe-intent.v1` / `fea.selection-reconciliation.v1`),
prefer owner-qualified CAD group or attribute strategies qualified by FEM/AFEM
component and occurrence path, use documented Boolean/stacked strategies only
when operand recipes exist and remain homogeneous, and verify area, normal,
centroid, and load resultant/moment after topological splits or remeshing.
Use `classify_associativity`, `plan_associative_retrofit_or_rebind`,
`evaluate_mesh_and_connection_replay`, and `plan_sim_rebind` in
`fea_agent.parametric_cae` to evaluate associativity classes, inspect-before-create
duplicate guards, freeze states (`FEM_GEOMETRY_FROZEN`, `CAE_RECIPE_FROZEN`,
`AFEM_ASSEMBLY_FROZEN`), mesh update log completeness, and SIM BC/load/contact
propagation. Missing owner accessors, SDK signatures or installed handlers remain
named gaps (`BLOCKED_BY_OFFICIAL_MCP_CAPABILITY`).
After remesh, rerun region resolution and all dependent load/connection bindings,
then compare physical measures and effective model readback before accepting the
variant.

The mounted-assembly reduction does not establish flexible housing stresses or
connector capacity. If a load path reverses or flexible modes enter the band,
retain the computed reference and route to contact or flexible-structure analysis.
