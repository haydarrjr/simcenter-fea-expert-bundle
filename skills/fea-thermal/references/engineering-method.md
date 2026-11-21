# Thermal state, restraint and mechanical load-path change

## Contents

1. Separate a temperature field from a thermal load
2. Map temperature and mechanical work consistently
3. Solve sequential restraint
4. Verify restrained expansion
5. Verification and API effects

## Separate a temperature field from a thermal load

For heat conduction, the governing balance is
`rho c dT/dt = div(k grad T) + Q`. Surface convection, radiation, imposed flux
and prescribed temperature are different boundary conditions. Identify whether
the input is an absolute field, a temperature change from a stress-free state,
or an initial condition. Check net heat flow and stored thermal energy before
using a temperature field for stress.

Mechanical thermal strain is generally `epsilon_th = integral alpha(T) dT`
from the material's stress-free reference. A tabulated secant expansion
coefficient and instantaneous alpha(T) are not interchangeable. For constant
alpha, it reduces to `alpha DeltaT`. The source workflows explicitly use
constant moduli and coefficients with temperature changes in K; they do not
solve heat conduction or infer temperature-dependent material behavior.

Uniform free heating produces expansion without stress only when all relevant
motions are unrestrained. Differential expansion, rigid links, attachments or
contact can create force even if the entire analysis has one temperature value.
A strong but diagnostic shortcut is to apply an equivalent force to
every support without solving compatibility; it can satisfy a global resultant
while assigning incorrect local reactions.

## Map temperature and mechanical work consistently

Bind every transferred field to the source model/revision/step, target mesh,
coordinate system, material and stress-free temperature. Compare coverage and
physical locations, not only matching node labels. Temperature is a scalar;
heat flux is a vector and needs frame transformation. Conservative heat transfer
must preserve integrated heat rate where appropriate. Mechanical interface
transfer must separately preserve force, moment and virtual work.

Thermal coupling is also solution-dependent. The Nastran 2606 RBE3 declaration
documents thermal expansion requirements and explicitly different SOL402/414
behavior. Do not assume that a rigid element's ALPHA or a common card field has
the same effect in all solution sequences. The source evidence records this
release scope; a generic exporter cannot silently substitute one solver family.

## Solve sequential restraint

For a linear mount with free growth d and actual displacement u, restoring
force on the body is `-k(u-d)`, with elastic energy `k(u-d)^2/2`. In a rigid
assembly use each mount's directional stiffness and orientation, then solve
the coupled body translation/rotation from equilibrium. A simple sum of mount
forces misses compatibility and the moments from offset attachments.

For locked bolt/member paths the mismatch changes preload through the series
compliance, before service loading redistributes it. Retain the pretension lock
state, individual component temperature and settlement. Applying preload again
in the service step or dropping it during a restart produces a different
physical problem even when the service pressure is unchanged.

## Verify restrained expansion

Use free expansion and complete restraint as limiting cases for a uniform prismatic member. For a joint with different bolt and member temperatures, compute the differential expansion using each path length and temperature-dependent material data. Check preload change against a compatibility estimate at the same contact state.

## Verification and API effects

Test a free expansion reference, a restrained one-dimensional reference,
reaction/moment balance and a temperature sign reversal before interpreting
complex stress. For varying material properties use the appropriate integral
and tangent, then perform time/load-step convergence at the engineering QoI.
Track thermal field uncertainty separately from mesh error and joint model form.

The documented API workflow can attach a created load to an explicit solution
step and read back membership. The load descriptor and property names must come
from actual release-specific metadata; unverified descriptor strings are not
vendor-defined identifiers. Consult the
documentation for the current Siemens release and [runtime gate](../../fea-native-runtime-gate/SKILL.md).
Thermal field creation, coupling, solve and persistent export need their own
qualified capabilities; no generic CAD mutation grant covers these operations.

For hot modes, verify the equilibrated operating state and the tangent mount stiffness used by the perturbation.
Geometric stress stiffness, temperature-dependent stiffness, contact switching
and flexible-body thermal modes are unresolved. Preserve that limitation when
deciding whether the reference is adequate for the operating-frequency band.
