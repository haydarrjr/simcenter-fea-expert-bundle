# Thermal state, restraint and mechanical load-path change

## Contents

1. Separate a temperature field from a thermal load
2. Map temperature and mechanical work consistently
3. Solve sequential restraint
4. Worked assembly and bolt examples
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
A strong but wrong-looking-right shortcut is to apply an equivalent force to
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

## Worked assembly and bolt examples

Run `python -m fea_agent run-case examples/engineering_v2/assembly_case.json`.
The manufactured 118 kg assembly has four tilted anisotropic mounts. A 100 K
temperature change gives the four modeled local growth magnitudes
`110, 192, 81, 121 micrometres`, derived from length times coefficient times
temperature. Their directions and stiffnesses differ, so the body cannot
satisfy all free growth simultaneously.

Under the same gravity-equivalent inertial load, reference-origin Z translation
changes from about **-34.427 micrometres cold to +92.245 micrometres hot**.
Mount M1's local axial support reaction changes from **+206.174 N to -9.905 N**.
The bilateral reference remains in force/moment equilibrium, but the changed
sign requires a real tensile load path. If that interface is compression-only,
its assumed active state is wrong. The case runner detects the reversal and
routes the engineering question to contact analysis; it does not promote small
residuals to engineering acceptance.

The eight-bolt flange example offers an independent mechanism. Initial 20 kN
preload rises to about 36.957 kN after different bolt/member temperature changes.
Eccentric service then opens B2–B5; unloading with 4 micrometres settlement leaves
about 18.913 kN per bolt. A single thermal stress number cannot represent that
load history. Run `assess-joint examples/engineering_v2/joint_flange8_thermal_service.json`
and read the stepwise forces, contact states and energy.

## Verification and API effects

Test a free expansion reference, a restrained one-dimensional reference,
reaction/moment balance and a temperature sign reversal before interpreting
complex stress. For varying material properties use the appropriate integral
and tangent, then perform time/load-step convergence at the engineering QoI.
Track thermal field uncertainty separately from mesh error and joint model form.

The documented API workflow can attach a created load to an explicit solution
step and read back membership. The load descriptor and property names must come
from actual release-specific metadata; a contract fixture's strings are not
vendor-defined identifiers. Consult the
API workflow (source: fea_expert_agent_plugin/docs/engineering/vendor-api-workflows.md) and
Runtime compatibility (source: fea_expert_agent_plugin/docs/architecture/runtime-compatibility.md).
Thermal field creation, coupling, solve and persistent export need their own
qualified capabilities; no generic CAD mutation grant covers these operations.

Hot modes in the assembly source example use unchanged linear mount stiffness.
Geometric stress stiffness, temperature-dependent stiffness, contact switching
and flexible-body thermal modes are unresolved. Preserve that limitation when
deciding whether the reference is adequate for the operating-frequency band.
