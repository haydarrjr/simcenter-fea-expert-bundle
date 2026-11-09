# Real 3D transient fields and downstream durability

Use `fea_solve_transient` for bounded linear small-strain 3D Tet4/Hex8 models
with consistent mass, fixed homogeneous supports, explicit initial conditions
and time-dependent nodal/body forces. Use the nonlinear open-solver route when
contact, plasticity, finite rotations, follower loads or moving supports govern.
The source Newmark solver does not implement those mechanisms.

## Execute and assess

```sh
python -m fea_agent source-tool examples/advanced_dynamics_v4/axial_transient.json --operation solve_transient
python tools/qualify_dynamics_v4.py --require-engines --output dist/dynamics-v4.json
```

The example is an actual 3D field model with original labels and integration
points. Its zero Poisson ratio permits an independent longitudinal-bar reference;
it does not establish arbitrary 3D bending or shear accuracy. The qualifier also
executes OpenSees with independent model assembly and compares the complete
displacement and axial stress history. A separate matrix exponential isolates
the temporal error that two Newmark-based solvers could share.

The request schema is `fea.transient_solid.v1`. Supply `identity` with model ID
and revision, `units: SI`, continuum nodes/elements/materials,
`displacement_bcs`, optional nodal `initial_displacement`/`initial_velocity`, and
`load_history`. The latter is a list of increasing `time_s` starting at zero;
each row may carry `nodal_forces` or `body_acceleration` in the continuum load
format. Endpoint loads are absolute values, linearly interpolated in time.
`substeps` refines this same loading; it does not invent higher-frequency load
content. Supply `rayleigh_damping` with nonnegative `mass_per_s` and
`stiffness_s` only when justified by actual damping evidence.

Use `time_refinement: {factor: 2, relative_tolerance: 0.01}` as a starting
comparison. Examine displacement and integration-point stress waveform/peak
differences, then establish sufficient refinement for the required output.
`PAIRWISE_AGREEMENT` is a two-grid result, not a certified error bound.
Mesh refinement and element suitability remain independent requirements.

## Interpret physical evidence

Inspect force and moment balance including inertia, damping and reactions;
equilibrium residual; recovered elastic energy; and cumulative external,
kinetic, elastic and dissipated energy. Newmark average acceleration has a
discrete energy identity; energy conservation alone cannot resolve phase.
The coarse example has approximately `1e-14` energy defect and **80%** waveform
error. Reject its stress/life interpretation and refine the time grid.

`states` contains displacement, velocity, acceleration and reaction arrays in
the declared `node_ids` order. `tensor_history` preserves every original
element label/integration point, material, global signed stress components and
physical state. It is the input to [Durability](../../fea-durability/SKILL.md).
Keep `field_output_stride=1` for that bridge: subsampling can omit reversals and
is explicitly rejected by fatigue. A source history without time refinement
also requires refinement before that route.

When a long full field exceeds interactive transport budgets, retain
`field_output_stride=1` and use explicit spatial output, for example
`output: {nodal_fields: false, tensor_points: [{element_id: 5001, integration_point: 0}]}`.
All integration times remain present. Full-model energy, balance, extrema and
time-grid comparisons still use every point; only returned arrays are
projected. The result reports the exact selected points, omissions and history
digest. Select locations from a justified spatial assessment; one point is not
proof that another location cannot govern. Refine the mesh independently even
when the two time grids agree: dispersion of higher spatial modes can change
waveforms and fatigue damage while both grids pass the time criterion.

Do not relabel Gauss stresses as cell or nodal stresses. Hex8 has eight distinct
integration points, and material boundaries must not be averaged silently.
For visualization formats supporting only Node/Cell fields, preserve the
original tensor-history companion or implement an explicit recovery topology.
Read the method and independent evidence (source: fea_expert_agent_plugin/docs/research/advanced-physics-v4.md)
when interpreting a source result or proposing another integrator.
