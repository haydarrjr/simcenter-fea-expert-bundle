# Model preparation as a mechanical reduction

## Contents

1. Obtain ownership and load-path evidence
2. Choose a reduction from the mechanics
3. Preserve hierarchy, frames and interface work
4. Check assembly scope and support mapping
5. Native construction and failure recovery

## Obtain ownership and load-path evidence

Inspect the actual part/model hierarchy, material/property source, active SIM
overrides, mesh revision and selected load/constraint regions. A face number,
node label or nonempty selection is not a persistent physical region. Tie a
selection to its owning part, occurrence transform, revision, semantic purpose
and geometric invariants. Re-evaluate membership after topology change or remesh;
never retain a stale finite-element ID list merely because its integers exist.

Audit model graphs and compare section or hierarchical mass properties where
the needed evidence is available. Use an owned work copy for an approved native
geometry edit and independently verify the original. Admit file export and
persistent save as separate effects with separate readback.

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
QoIs. A global energy match never certifies a notch-root fatigue stress. Use [beam mechanics](mechanics.md) and the [decision procedure](decision-procedure.md) to verify applicability across the entire load-bearing span.

## Preserve hierarchy, frames and interface work

For a component, rotate its center inertia with `I_global = R I_local R^T` and
use the parallel-axis term `m ((r.r) I - r r^T)`. Compose occurrence transforms
through the hierarchy; do not rotate a child twice or count assembly mass again
when it already includes its children. Use component mass without children when summing a hierarchy. Check for duplicate occurrences, missing parents, improper rotations and invalid inertia tensors.

At an interface point r, rigid motion is `u(r)=u0 + theta x r = B(r) q`.
The work-conjugate load is `Q = sum B(r)^T f(r)`, containing both resultant
force and moment. Therefore `sum f.u = Q.q`. A transfer that preserves force
but omits `r x f` changes the model's work and load path. Model revision and
frame must match before comparing these quantities.

## Check assembly scope and support mapping

Transform all loads, inertias and supports to a common origin and frame. Confirm occurrence identity, selected region and coupling DOFs. Check force and moment at interfaces and compare compliance or deflection independently across candidate representations.

## Native construction and failure recovery

Use exact-release Siemens Help and installed API discovery. Independently check face normal, area, centroid, ownership and revision before applying a pressure and verify the integrated force and moment afterward.

Use existing graph/region audits for CAD–idealized part–FEM–AFEM–SIM dependencies
and the current official Siemens reads. For persistent CAE Selection Recipes,
prefer owner-qualified CAD group or attribute strategies qualified by FEM/AFEM
component and occurrence path, use documented Boolean/stacked strategies only
when operand recipes exist and remain homogeneous, and verify area, normal,
centroid, and load resultant/moment after topological splits or remeshing.
Use the [parametric SOL101 workflow](../../simcenter-parametric-sol101/SKILL.md)
to evaluate associativity, inspect targets before creating duplicate objects,
and record freeze states (`FEM_GEOMETRY_FROZEN`, `CAE_RECIPE_FROZEN`,
`AFEM_ASSEMBLY_FROZEN`), mesh update log completeness, and SIM BC/load/contact
propagation. Missing owner accessors, SDK signatures or installed handlers remain
named gaps (`BLOCKED_BY_OFFICIAL_MCP_CAPABILITY`).
After remesh, rerun region resolution and all dependent load/connection bindings,
then compare physical measures and effective model readback before accepting the
variant.

The mounted-assembly reduction does not establish flexible housing stresses or
connector capacity. If a load path reverses or flexible modes enter the band,
retain the computed reference and route to contact or flexible-structure analysis.
