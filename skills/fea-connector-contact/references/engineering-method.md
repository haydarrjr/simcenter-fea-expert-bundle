# Engineer the joint through compatibility and contact state

## Contents

- [Establish the load path](#establish-the-load-path)
- [Compute compatibility](#compute-a-compatibility-reference-before-trusting-a-contour)
- [Construct and falsify](#construct-debug-and-falsify)

Use the exact-release Siemens Help and installed API discovery for native setup. Use the mechanics below as a separate physical check.

## Establish the load path

Identify the two connected bodies, bolt axes, bearing patches, interface sides
and the reference frame. Obtain region membership and model/mesh/owner revision
from available inspection evidence. A cached face or element label after remesh
is not the same physical selection. Transform interface normals into the joint
frame and verify the sign of compressive contact on each body. Reversed side selection must be corrected before
interpreting pressure or traction.

Choose tied/glued contact only when separation and relative sliding are excluded
by the physical connection. A bolted interface can open while the bolts remain
in tension; keeping it tied can suppress the mechanism that governs the bolt
load. Use a connector model only when its transferred DOFs, axial/shear/bending
compliance and load-introduction region represent the actual connection.
Rigid links can distribute load usefully but can also create a false flange
stiffness or overconstrain an interface.

Distinguish bolt axial force, interface compression, transverse friction,
shank bearing and thread capacity. They are separate load paths. A bolt-force
result is an input to a thread/fatigue assessment, not proof of either capacity.

## Compute a compatibility reference before trusting a contour

For a closed axial joint, derive `k_b=E_b*A_b/L_b` and an independently justified
member stiffness `k_m`. The load fraction is `C=k_b/(k_b+k_m)`. An external
separating force increment P produces `deltaB=C*P` in the bolt and reduces
member compression by `(1-C)*P`. The common shortcut `B=preload+P` overstates
the increment for a closed joint and misses the change of regime at separation.

For a rigid-flange reference with eccentric load stations, use joint translation and rotations. The
three relative DOFs give `d_i=w+theta_x*y_i-theta_y*x_i`. The unilateral laws
are `B_i=max(0,P_i+k_bi*(d_i-u_bi))` and
`C_i=max(0,P_i-k_mi*(d_i-u_mi))`. Solve force and both bending-moment balances
together; do not preserve the original closed-contact stiffness after lift-off.
Evaluate contact gaps, bolt forces, average station pressures, tangent and elastic energy. Check for an unconstrained rigid-flange mode even when forces balance.

Lock pretension by retaining achieved interference/extension. Do not hold the
bolt force constant during service. Include thermal free expansions from both
members and bolt, measured from the pretension reference. At zero service load,
`deltaP=(u_m-u_b)/(1/k_b+1/k_m)` for an identical closed station. Permanent
settlement can reduce retained preload even after temperature and external
load return to their original values. Track permanent settlement cumulatively from the locked reference. A decrease needs a physical explanation or a new reference. Re-tightening
requires a separately established new reference.

After substantial clamp loss, a slack-bolt/open-contact clearance can give a
zero tangent during numerical search even when the applied load has a valid
tension-supported endpoint. Distinguish that intermediate state from a true
geometric mechanism. A reference tangent used to find a descent direction must leave the unilateral physical law unchanged. Check the final contact/bolt
branch, force/moment balance and reported tangent independently.

## Check preload redistribution

Compare bolt axial forces and interface contact reactions before and after preload locking, then after each service increment. In a common frame, integrate the opposite interface tractions and their moments. Include only external forces in the whole-assembly balance.

For unilateral contact, check that separated regions carry negligible normal traction and that closed regions meet the declared gap or penetration tolerance. For Coulomb friction, compare tangential traction with the local friction bound and verify that sliding traction opposes relative slip. Check local normals and stick/slip state beside that comparison. Separation or sliding changes the compatibility estimate and can shift the relevant recovery location.

## Construct, debug and falsify

Bind each native construction step to a fetched owner/factory/member and an
actually admitted Runtime capability. Preserve the documented builder cleanup
and consume independent readback after commit. Before solving, inspect the
effective subcases and selected controls. SOL401 requires preload application
in its documented preload subcase; SOL402 has different preload and restoration
semantics. Verify the applicable controls in the [nonlinear method](../../fea-multistep-nonlinear/references/engineering-method.md) and exact-release Siemens documentation.

For a 3D bolt under large strains, compare bolt force and sign after preload and again as service loads are applied. Siemens reports a maintenance-level SOL 401 defect that can change force in the service step even when the preload step agrees. Verify the installed maintenance build and the article's conditions. Treat changing to tied behavior as a model-form change and check whether opening and slip remain relevant. [SOL 401 bolt preload](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.multi_step_nonlinear/html/xid924582?audience=external) · [Siemens Support advisory PL8869179](https://support.sw.siemens.com/en-US/knowledge-base/PL8869179)

If contact remains uniformly closed where the reference opens, inspect glue,
region orientation, hidden stabilization and load introduction. If thermal
preload moves in the wrong direction, reconcile reference temperature, expansion
coefficients and grip lengths. If force balances but bolt load is excessive,
check compatibility and the lock state. If contact oscillates, separate an
increment-size experiment from a penalty-stiffness experiment and compare both
penetration and engineering QoIs.

For a small joint reference, independently enumerate the plausible contact branches and compare equilibrium, energy/work and frame transformations. Match result identity and station membership before comparing native forces.
Source equilibrium does not establish real flange compliance, hotspot accuracy,
thread strength, installed API execution or engineering acceptance.
