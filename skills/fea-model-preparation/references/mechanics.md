# Mechanics of the bounded idealization assessment

## Coordinate and hypothesis contract

Use a straight common centroidal x-axis from the supported root (x=0) to the
free tip (x=L). Positive displacement/force is y; positive moment/section
rotation is about z. Rectangle depth h is along y, width b along z. Swapping
width and depth preserves area while changing bending stiffness: orientation
is physical input, not a display preference.

Each segment is prismatic. All segments share one isotropic material, one
shear-factor convention and one uncoupled root support. Original and proposed
models must share span, material, load case and support. The implementation
compares section changes, not simultaneous material, load or attachment changes.
Geometry is declared data until separately authenticated against CAD.

Supported hypotheses: linear elasticity, small displacement/rotation, rigid
plane cross sections, one transverse bending plane, static point forces,
point couples and uniform distributed loads on explicit intervals. The
Timoshenko variant permits shear deformation; the Euler–Bernoulli (EB) variant
sets its contribution to zero. This kinematic distinction is described by
[INL's MOOSE beam formulation](https://mooseframework.inl.gov/moose/modules/solid_mechanics/C0TimoshenkoBeam.html).
No implementation is copied from that source.

Excluded: axial/prestress effects, torsion, biaxial coupling, centroid or shear
center offsets, thin-wall distortion, contact/opening, plasticity, buckling,
thermal strain, dynamics, curved members and true three-dimensional stress
concentrations. A stepped beam represents global flexibility; it does not
resolve a shoulder's stress concentration. No universal slenderness cutoff or
Saint-Venant exclusion distance is asserted.

## Section and load-path equations

The implemented rectangle properties are

\[
A=bh,\quad I_z=bh^3/12,\quad I_y=hb^3/12,\quad
Z_z=I_z/(h/2),\quad G=E/[2(1+\nu)].
\]

The material requires E>0, density>0 and -1<nu<0.5. The latter is the stable
isotropic elastic range, not evidence of the real material's linear regime.
Volume and mass are integrated over the piecewise section lengths.

At a cut x, construct the right-side resultants from every distal load:

\[
V(x)=\sum_{a>x}F_a+\int_x^Lq(t)\,dt,
\qquad
M(x)=\sum_{a>x}F_a(a-x)+\sum_{c>x}C_c+
\int_x^Lq(t)(t-x)\,dt.
\]

One-sided values include/exclude a load at the cut according to `Side.LEFT`
or `Side.RIGHT`. At x=0 only RIGHT is valid; at x=L only LEFT is valid.
At a section transition both sides share displacement and rotation, while
section-dependent stress and shear slope can differ. Point force/couple
jumps are retained. Within an unloaded discontinuity-free interval,
M'=-V and V'=-q under this right-side convention. Root reactions are the
negatives of total applied force and total moment about the root. A force or
couple applied directly at the root loads its spring but not the beam field.

## Displacement, rotation and energy

For root stiffnesses k_t and k_r, use u0=F_total/k_t and theta0=M_root/k_r.
An explicit null stiffness means fixed in that degree of freedom; zero is a
mechanism and is rejected. Coupled, unilateral or frequency-dependent support
behavior is outside this model. A flexible support must not be silently
replaced with a perfect clamp.

At station s, virtual work gives

\[
\theta(s)=\theta_0+\int_0^s\frac{M(x)}{E I_z(x)}\,dx,
\]

\[
u(s)=u_0+s\theta_0+
\int_0^s\frac{(s-x)M(x)}{E I_z(x)}\,dx+
\int_0^s\frac{V(x)}{\kappa G A(x)}\,dx.
\]

The last integral is omitted for EB. Section rotation and centerline slope
are different quantities for Timoshenko: u'=theta+V/(kappa G A). Nominal
fiber stress is sigma_x=-M*y/I_z; top and bottom fibers retain their signs.
It is not a fillet, hole, contact or attachment peak stress.

\[
U=\int_0^L\left(\frac{M^2}{2EI_z}+\frac{V^2}{2\kappa GA}\right)dx
+\frac{F_{total}^2}{2k_t}+\frac{M_{root}^2}{2k_r}.
\]

A fixed degree of freedom contributes no spring energy. For the worked case,
kappa=5/6 is obtained by matching the energy of the parabolic shear distribution
in a solid rectangle: integral_A(tau^2/G)dA=V^2/(kappa G A). This is an explicit
approximation, not a universal exact elasticity coefficient or a qualified
PBEAM field mapping. Different shear-factor evidence must be supplied explicitly.

## Deterministic numerical method

records.py (source: fea_expert_agent_plugin/fea_agent/idealization/records.py) holds immutable SI
records; sections.py (source: fea_expert_agent_plugin/fea_agent/idealization/sections.py) calculates
properties; beam.py (source: fea_expert_agent_plugin/fea_agent/idealization/beam.py) integrates the
piecewise response. The algorithm splits at section, force, couple and
load-interval boundaries, represents polynomials in a normalized local
coordinate, integrates response coefficients and evaluates energy with a
three-point Gaussian rule exact for the supported polynomial integrands.
It does not assemble finite
elements, solve a stiffness system or parse a general Nastran deck.

Whole-span extrema are assessed from interval endpoints and interior stationary
points, not just requested output stations. Derivatives supply candidate roots
for displacement, section rotation, slope and nominal strain. One-sided
boundary values are retained. Finite-range guards reject unrepresentable
intermediate/results instead of manufacturing a zero or infinity. Sum and
product policies are exercised by numerical tests; this does not promise
accurate arbitrary ill-conditioned binary64 arithmetic.

The JSON adapter converts dimensions once. Shared coordinates differing only
within four binary64 epsilons relatively are reconciled to their first canonical
occurrence (span has priority). No absolute geometric tolerance is used; zero
cannot absorb nonzero locations. Ambiguous matches, collapsed intervals and
real gaps/overlaps are rejected. The pure SI core requires exact adjacency.

## Model choice and error accounting

For each computable QoI Q, assessment.py (source: fea_expert_agent_plugin/fea_agent/idealization/assessment.py)
calculates original Timoshenko Q_r, proposed Timoshenko Q_t and proposed EB Q_e.
The declared allowance is a+r*abs(Q_r), with dimensional absolute tolerance a
and dimensionless relative tolerance r. The geometry difference is
D_g=abs(Q_t-Q_r); omitted shear is D_s=abs(Q_e-Q_t).

Timoshenko requires D_g within the allowance. EB requires D_g+D_s within it,
so opposite errors cannot cancel to make the model appear better. Every
requested computable QoI must pass; mass alone cannot justify a mechanical
idealization. At least one informative mechanical response is required.
Each comparison exposes `numerical_resolution` and
`reference_is_resolved_nonzero`. The resolution scale comes from a separate
original-model Timoshenko response to the absolute magnitude of every
constituent force, couple and distributed load at its original location.
Its full-span response scale survives cancellation of signed loads; energy
uses the envelope's total elastic energy. The margin is
64 times (1 + segment count + force count + couple count + twice the UDL count)
times the ULP of that scale. This is a conservative floating-point resolution
screen, not a certified forward-error bound or a physical accuracy allocation.
It scales with load, including quadratically for energy, rather than using a
fixed dimensional cutoff. An unresolved or cancellation-dominated response
cannot by itself justify a global model choice. Signed numerical outputs and
user budgets remain visible and unchanged; the algorithm does not manufacture
an exact zero. Unrepresentable envelope calculations fail explicitly.

If both theories qualify, EB is selected as the simpler permitted global
approximation; if only Timoshenko qualifies it is retained; otherwise the
proposal is rejected. This preference is conditional on the supplied hypotheses.

These are **differences between three declared reduced models**, not bounds on
error against 3D elasticity, experiment or the actual part. They omit uncertainty
in geometry, material, loading, support behavior and the beam hypotheses.
A mass match is insufficient, and a near-zero response needs a meaningful
absolute budget. Caller-owned whole-span deflection/span, rotation, slope and
nominal-strain limits are checked separately; they are screening criteria,
not automatic proof that small-strain theory represents reality. Maximum
section depth/span and width/span are also screened against explicit
caller-owned limits; no universal aspect-ratio threshold is embedded.

Protected feature IDs become retained-geometry/local-model requirements.
LOCAL_PEAK_STRESS always returns unavailable. A globally eligible beam choice
can coexist with unresolved local requirements; it is never full engineering
acceptance. Do not remove the feature merely because global differences pass.
