# Engineer the joint through compatibility and contact state

## Contents

- [Establish the load path](#establish-the-load-path)
- [Compute compatibility](#compute-a-compatibility-reference-before-trusting-a-contour)
- [Worked assembly](#worked-eight-bolt-decision)
- [Construct and falsify](#construct-debug-and-falsify)

Use the exact-release Siemens Help and installed API discovery for native setup. Use the mechanics below as a separate physical check.

## Establish the load path

Identify the two connected bodies, bolt axes, bearing patches, interface sides
and the reference frame. Obtain region membership and model/mesh/owner revision
from available inspection evidence. A cached face or element label after remesh
is not the same physical selection. Transform interface normals into the joint
frame and verify their sense: in the source model, compressive contact acts on
the upper flange along +Z. Reversed side selection must be corrected before
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

Use the implemented rigid-flange model for multiple eccentric stations. The
three relative DOFs give `d_i=w+theta_x*y_i-theta_y*x_i`. The unilateral laws
are `B_i=max(0,P_i+k_bi*(d_i-u_bi))` and
`C_i=max(0,P_i-k_mi*(d_i-u_mi))`. Solve force and both bending-moment balances
together; do not preserve the original closed-contact stiffness after lift-off.
The model reports contact gaps, bolt forces, average station pressures, tangent
and elastic energy. It rejects a balanced but unconstrained rigid-flange mode.

Lock pretension by retaining achieved interference/extension. Do not hold the
bolt force constant during service. Include thermal free expansions from both
members and bolt, measured from the pretension reference. At zero service load,
`deltaP=(u_m-u_b)/(1/k_b+1/k_m)` for an identical closed station. Permanent
settlement can reduce retained preload even after temperature and external
load return to their original values. Supply settlement cumulatively from the
locked reference and never reduce it in later service steps. The workflow
rejects a decrease instead of silently restoring clamp force. Re-tightening
requires a separately established new reference.

After substantial clamp loss, a slack-bolt/open-contact clearance can give a
zero tangent during numerical search even when the applied load has a valid
tension-supported endpoint. Distinguish that intermediate state from a true
geometric mechanism. The source solver searches through the gap using the
actual unilateral potential; the elastic reference used for a descent
direction is not an added physical spring. Check the final contact/bolt
branch, force/moment balance and reported tangent independently.

## Check preload redistribution

Compare bolt axial forces and interface contact reactions before and after preload locking, then after each service increment. Close force and moment balance in one frame. Check whether separation or sliding invalidates the linear compatibility estimate and identify the locations that require local assessment.

## Construct, debug and falsify

Bind each native construction step to a fetched owner/factory/member and an
actually admitted Runtime capability. Preserve the documented builder cleanup
and consume independent readback after commit. Before solving, inspect the
effective subcases and selected controls. SOL401 requires preload application
in its documented preload subcase; SOL402 has different preload and restoration
semantics. See the fetched 2606 evidence in the full method, not remembered
card names or an arbitrary step-type integer.

If contact remains uniformly closed where the reference opens, inspect glue,
region orientation, hidden stabilization and load introduction. If thermal
preload moves in the wrong direction, reconcile reference temperature, expansion
coefficients and grip lengths. If force balances but bolt load is excessive,
check compatibility and the lock state. If contact oscillates, separate an
increment-size experiment from a penalty-stiffness experiment and compare both
penetration and engineering QoIs.

The executable holdouts independently enumerate 256 active sets with 50-digit
Decimal arithmetic, verify energy/work and frame covariance, and reject the
force-balanced `preload+external load` counterexample. Match result identity,
station membership and force/moment balance before comparing native forces.
Source equilibrium does not establish real flange compliance, hotspot accuracy,
thread strength, installed API execution or engineering acceptance.
