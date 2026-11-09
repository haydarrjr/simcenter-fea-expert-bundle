# Build, execute and question an actual nonlinear history

## Contents

- [Choose a physically discriminating model](#choose-a-physically-discriminating-model)
- [Prepare the typed model](#prepare-the-typed-model)
- [Execute with explicit custody](#execute-with-explicit-custody)
- [Read fields and challenge their physics](#read-fields-and-challenge-their-physics)
- [Independent comparisons](#independent-comparisons)
- [Report an engineering decision](#report-an-engineering-decision)

Use the source `prepare_calculix` and explicit effectful `run_calculix`
operations for a separately installed, configured CalculiX 2.23 engine.
Read research, theory and actual evidence (source: fea_expert_agent_plugin/docs/research/open-solvers-v4.md)
for the supporting primary sources and qualification. Read the
complete executable examples (source: fea_expert_agent_plugin/examples/open_solver_v4/README.md)
for exact JSON and reproduction commands. Native Siemens operations retain
their own Runtime capability and admission requirements.

## Choose a physically discriminating model

State the requested quantity and the strongest plausible wrong answer before
building the model. For a locked bolt, a continuing force controller may
converge while removing the intended stiffness increase. For contact, a wrong
surface may converge while transferring no force. For thermoplasticity, a
plausible total strain can conceal lost permanent strain. Select load paths
that make those alternatives observable.

Identify which bodies deform and which constraints idealize fixtures. Distinct
contact bodies need distinct nodes; shared nodes cannot open or slip. Preserve
the hole, bearing surfaces, cut section, axes and body/material ownership when
working from CAD. A homogeneous coupon verifies its constitutive response;
it does not establish the bearing stress or contact stiffness of an assembly.

Choose reference equations only within their assumptions. A small-strain
uniaxial return consistency is useful for a homogeneous solid coupon. It is
not a general finite-strain validation. A frictional flat block is not the
frictionless small-contact-radius problem assumed by Hertz.

## Prepare the typed model

Use `fea.open-solver.v1` with m, N, s and K; use Pa for stress/modulus,
kg/m³ for density and Pa/m for the normal and tangential contact slopes.
Convert engineering material data to the solver's required true stress and
plastic-strain conventions where applicable. Keep provenance and calibration
uncertainty outside the strict mechanical payload in the study record.

Use `tet4`, `tet10`, `hex8` or `hex20` connectivity in CalculiX order.
Imported CAD mesh records retain parent element/face sides and body material
assignments. For high-order elements, distinguish the corner geometry check
from a full curved Jacobian assessment. Do not advertise a positive corner
volume as proof against a midside inversion.

Represent every step's constraints and loads explicitly. Base constraints
persist; changing constraints belong to the step. CLOAD, DLOAD and step
boundaries are replaced at each step. Temperature fields persist unless
explicitly updated. NLGEOM is consistent through the complete history.

For a solid pretension section, select an internal face section and a dedicated
reference node. Apply the preload through scalar DOF 1; in the following step,
set `hold:true` on that adjustment and remove the force load when lock is the
physical intent. Request section integration rather than assuming a control
node's reaction equals bolt force. Review the section orientation and what
physical region is cut.

The delivered `bolted_plate_joint.json` combines a flexible shaft/caps, bored
plates, three contact pairs and the same internal cut in one history. Its
final opening phase adds a lower axial grip at the preceding deformed state.
That fixture change is part of the physical experiment: retain its reaction
in equilibrium. For a different real assembly, derive its own supports and
actuator history instead of inheriting this verification fixture silently.

Prepare first. Check units, positive geometry, model ownership, complete load
history and `input_sha256`. No solver process is started by preparation.
Do not pass raw INP, include directives, paths, commands or user subroutines;
the current contract intentionally has no such fields.

## Execute with explicit custody

Discover the source MCP capability. The host configures the executable,
library directory, job root and resource policy. When execution is authorized,
send the model and `authorization:{execute:true,prepared_input_sha256:...}`.
Bind the digest to the preparation just reviewed. Changing a model requires a
new preparation digest, not reuse of an old authorization.

A disabled or missing engine is `NOT_RUN`. A fresh effectful execution retains
input, original outputs, process exit, version and hashes in a new job directory.
Require every declared final step and the matching model geometry, in addition
to the engine's completion marker. A partially populated directory is not a
successful result. A stale RUNNING receipt means outcome reconciliation is
needed; do not infer liveness or retry an uncertain job blindly.

Use the configured job readback/series bridge to inspect retained artifacts.
Keep full arrays and raw files in custody when a transport response summarizes
them. A compact MCP result is not permission to discard provenance.

## Read fields and challenge their physics

Use DAT integration-point stresses/plastic strain for a constitutive oracle.
FRD stress/strain recovery is nodal extrapolation and averaging. Keep element,
integration point, step, increment and time distinct; never rename a Gauss
value as a nodal observation. Preserve Cauchy stress, total strain, thermal
and plastic contributions and tensor shear conventions.

Inspect full global force and moment resultants in a consistent frame and
configuration. Include solver-generated pretension cut nodes, not only input
node labels. `FORC` can contain applied and reaction contributions. In a
transient problem, the static resultant test needs an inertia term; report
that omission instead of assigning a false equilibrium conclusion.

For each contact pair, inspect integrated normal/tangential force, pressure
sign, Coulomb admissibility, activity and deformed physical gap. An open
interface cannot carry tensile contact traction. A completely inactive contact
history cannot establish the intended clamped load path. FRD positive COPEN is
clipped to zero: use the independent geometric gap diagnostic, preserve its
projection coverage, and distinguish linear corner-facet approximation from
the engine's high-order quadrature.

For unloaded contact, inspect each body's remaining restraint. A floating
member can satisfy global force balance while moving along an unconstrained
mode. The implemented six-mode kinematic screen flags unrestrained static
bodies only when they have no active contact or shared nodes. An unassessed
body is not certified stable; active-contact and coupled tangent-stiffness
stability require further analysis. In the retained combined-joint near miss,
zero plate pressure coexists with zero plate gap and a floating lower plate.

Keep undefined open-area derived normals/shear statistics as undefined. They
are not measured zeros. A missing plastic-strain field likewise remains
`NOT_REPORTED_BY_ENGINE`, not a measured zero. Preserve raw warnings and all failed attempts; a
successful later cutback does not erase a conditioning concern.

## Independent comparisons

Run the actual qualification tool for reproducible references. It executes
the engine rather than filling outputs from analytical expectations.

- For thermal plasticity, compare the published HSNV100 states and the authored
  load/hot-hold/unload/cool coupon. At 90 s, HSNV100 expects −75 MPa axial
  stress, 0.000525 equivalent plastic strain and 0.001275 lateral strain.
  Recheck tangent-modulus to plastic-hardening conversion if these disagree.
- For locking, compare integrated solid-section force after service motion
  against independent EA/L compatibility and the continued-force near miss.
  For the combined flexible joint, compare all three interface resultants,
  the fixed adjustment, differential thermal growth and a reduced bolt/member
  compliance estimate. Its 7.4% thermal-force discrepancy is retained because
  cap bending and contact compliance are absent from the reduced estimate.
  Check omitted shaft/bore contact against actual deformed clearance, including
  generated cut nodes. Do not call axial refinement contact-face convergence.
- For contact, refine mesh at fixed control settings, then reduce increment at
  fixed mesh/penalty, then vary penalty alone. Inspect force, gap, slip and
  global moment, not only maximum stress. The delivered contact study has an
  unresolved 3.36% final compression-force mesh change; report it.
- For transient waves, compare the entire history to the continuum solution
  and refine space and time. Increasing spatial resolution at fixed time step
  can worsen a waveform. Algorithmic damping is not calibrated material
  damping.

Keep all numerical tolerances explicit. Report the reference's assumptions,
quantity, scale, output precision and missing error bound. Do not loosen a
threshold to change a physics finding into a passing label.

## Report an engineering decision

Lead with the supported physical conclusion and the most discriminating
counterexample. Separate actual external execution, numerical agreement,
unresolved discretization, constitutive calibration and engineering acceptance.
Include original model/input/result hashes, solver version, actual states,
body/field identity, reference provenance and quantified discrepancies.

For a converged model with wrong load transfer, reject its intended physical
interpretation and repair the region/constraint path before tuning iteration
limits. For nonconvergence, inspect mechanism, scaling, material law, contact
pairing and increment changes using the retained artifacts. For consistent
checks with unresolved mesh error, report a useful result interval or a
pending mesh decision rather than a final strength conclusion.

Keep native transfer release-specific. CalculiX time, load inheritance and
pretension adjustments are not mechanically equivalent to SOL401 BOLTLD,
BOLTSEQ and constant-time preload subcases. Prepare a native handoff with its
own documented semantics; never claim that this external run executed Siemens.
