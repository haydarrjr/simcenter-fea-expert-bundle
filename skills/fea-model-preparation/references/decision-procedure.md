# Evidence-driven preparation procedure

## Establish the engineering question

Identify what will be decided from the model: global deflection/stiffness,
load sharing, nominal section stress, local fatigue-driving stress, instability,
frequency or contact pressure. Record location, frame, component, section side
and sign convention. Identify the design/service load envelope and material
regime. A request for a local peak cannot be answered with a global stiffness
surrogate; a static beam calculation cannot resolve instability or dynamics.

Record original CAD identity/revision and its idealized derivative relationship.
Gather measured dimensions and their source, body membership, section axes,
load-introduction geometry and actual support stiffness evidence. Distinguish
an assigned material name from demonstrated constitutive parameters/temperature
range. A label such as "aluminium" is insufficient for a defensible E, density,
Poisson ratio or allowable. The worked case uses explicitly synthetic values.

## Competing representations

| Candidate | Evidence needed | Failure mechanisms to examine | Executable coverage here |
|---|---|---|---|
| Beam with EB kinematics | Section axes/properties, common centroid, loads/support, global QoIs; sufficiently small shear effect for the chosen budgets | Omitted shear, offsets, section distortion, local load introduction, wrong orientation | Quantitative supported arm comparison |
| Beam with Timoshenko kinematics | Same data plus justified shear-factor convention | Beam hypotheses still invalid near attachment/contact/section transitions; shear locking in a future FE discretization | Quantitative supported arm comparison |
| Shell/midsurface | Thickness field, normals, offsets, bending/membrane loads, joints, through-thickness QoIs | Thickness/offset errors, transverse stress/contact, loss of local detail | Evidence procedure only; no shell kernel |
| Solid/local solid model | Three-dimensional load transfer and local feature geometry, material regime, appropriate QoI and refinement | Singular restraints, singular point loads, distortion, inappropriate averaging | Local requirement identified; no solid solver |

Do not turn this table into universal geometric ratios. The first two choices
have a source algorithm for the stated class. Shell/solid choices require
additional evidence and later capability work. Preserve that distinction in
the result, including for models that are clearly outside the bounded beam case.

## Operational decision sequence

1. Confirm the hypotheses in [mechanics](mechanics.md). If a transverse load is
   eccentric to the common centroid, torsion/offset effects are unresolved.
   If support contact may open, an uncoupled linear spring is insufficient.
   If local stress controls, preserve the relevant geometry/local-model task.
2. Bind measurable original and proposed section descriptions to the same
   local axis, material, load case and support. Account for all point forces,
   point couples and distributed intervals. Equal total force/moment does not
   imply equal flexibility response. Preserve actual locations.
3. Obtain accuracy allocations for each decision-driving QoI and explicit
   small-kinematics/nominal-strain criteria. Explain who chose them and why.
   Do not infer allowable model error from meshing defaults or a generic 5% rule.
4. Supply the closed request to `plan-domain`. A schema/type/unit failure means
   the supplied calculation is invalid; a computed rejection means a supported
   proposed approximation fails its declared checks. Neither is native failure.
5. Examine section properties, reactions and energy before accepting the choice.
   Compare geometry and shear contributions individually. Explain which QoI
   controls and why a mass-conserving or same-area alternative can fail.
6. Independently verify the response with a controlled benchmark/hand integral,
   then design native convergence and local comparison work. Check displacement,
   rotation, nominal stress and energy with dimensionally appropriate tolerances;
   equilibrium alone cannot verify displacement or local stress.
7. Return a model-preparation decision record: source identities and assumptions,
   computed alternatives with their budgets, whole-span regime findings,
   protected features/local tasks, exclusions, source verification and the
   specific Codex tasks in [Siemens handoff](siemens-2606.md).

## Ambiguity and revision policy

Missing or incompatible physical inputs are not resolved by a plausible prose
assertion. Ask for the smallest missing decision-driving input after extracting
what is available. If material/support uncertainty controls the decision, evaluate
explicit bounded alternatives as separate requests and explain the sensitivity;
no probability distribution or automatic uncertainty bound is implemented.

Change one physical assumption at a time for diagnosis. Keep original geometry,
load case and requested QoI definitions available. Re-run the complete assessment
when any of them changes. A prior source pass is not transferable to a different
load path, support, orientation, revision or local stress requirement.

Legacy domain facts remain an inventory and routing interface. Do not use their
`input_shape_complete=true` as evidence that a physical idealization is correct.
The quantitative request carries the numerical information needed by this slice.
