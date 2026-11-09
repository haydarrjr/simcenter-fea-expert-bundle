# Signed histories, nonlinear notch response and life interpretation

## Choose the supported method

Use `stress_life` for a linear-elastic uniaxial stress history below a supplied
elastic limit, with an appropriate material amplitude-versus-cycles S-N curve.
Use `fkm_nonlinear` when elastic FE stresses are to drive the documented pyLife
FKM nonlinear notch/hysteresis method and its material, geometry, surface and
probability inputs are justified. Both routes require an explicit fixed unit
direction and verify that the entire tensor is uniaxial in that direction.

Do not apply the FKM elastic-notch route to an already-plastic FE result.
General multiaxial, rotating-principal, nonproportional, weld, creep and
temperature-dependent fatigue need separate qualified methods. A declared
method gap is the engineering conclusion when these mechanisms govern.

## Bind and execute a real result

`fea_solve_transient` returns `tensor_history` and `tensor_history_sha256`.
Construct this request without changing the history:

```python
request = {
    "schema_version": "fea.fatigue_assessment.v1",
    "history": transient_result["tensor_history"],
    "expected_history_sha256": transient_result["tensor_history_sha256"],
    "expected_model_sha256": transient_result["model"]["model_sha256"],
    "method": "stress_life",
    "point_selections": [
        {"element_id": 5001, "integration_point": 0, "direction": [1, 0, 0]}
    ],
    "parameters": {
        "material_id": "verification-alloy",
        "reference_amplitude_Pa": 100e6,
        "reference_cycles": 1e6,
        "slope": 5,
        "mean_stress": "goodman_tensile_only",
        "ultimate_strength_Pa": 400e6,
        "elastic_limit_Pa": 250e6,
        "curve_source": "Synthetic verification curve; not material allowables",
    },
}
```

These curve values are executable verification data. Replace them with actual
material evidence for an engineering assessment. Select each point by original
element label and quadrature index; a row number is not an element label.

The history schema is `fea.tensor_history.v1`. It carries model ID/revision/hash,
source kind/request hash, `SI`, `GLOBAL_CARTESIAN`, tensor components
`[xx,yy,zz,xy,yz,xz]`, `SMALL_STRAIN_CAUCHY`, `LINEAR_ELASTIC`, sampling evidence,
and ordered states. Each state has a unique state ID, step, increment, physical
seconds and constant point membership. Each point has an element label,
integration point, material ID, six stresses in Pa and zero equivalent plastic
strain. Do not normalize away or repair inconsistent evidence silently.

Source histories require `PAIRWISE_AGREEMENT` and all integration steps.
External input is `EXTERNAL_UNAUTHENTICATED` with
`EXTERNAL_EVIDENCE_REQUIRED`; a content hash cannot authenticate an external
solver or validate acquisition bandwidth. State the unresolved external evidence
in the conclusion even when a numerical screening result can be calculated.

## Read the output correctly

The stress-life route returns actual rainflow cycles with source state/time
endpoints. Closed cycles count one; remaining finite-record branches count one
half. Do not close the signal periodically unless that physical repetition is
established and modeled separately. The example curve obeys
`N=Nref*(Sref/Sa_corrected)^slope`; it uses amplitude and cycles. Tensile-only
Goodman uses `Sa/(1-max(Smean,0)/Su)` and gives no beneficial compression credit.
`1/D` is a nominal repetition-to-unity calculation, not a sequence-sensitive
prediction or a failure probability.

FKM inputs are SI: tensile strength and load standard deviation in Pa, stressed
and reference surfaces in m2, gradient in 1/m, dimensionless roughness and shape
factors. `failure_probability` is a fraction; `load_occurrence_percent` is 2.5
or 50 percent. The adapter performs the MPa/mm conversion once and returns both
the SI inputs and engine parameters. The current normal-load-distribution route
requires explicit standard deviation. `K_p>1` is required because both `P_RAM`
and `P_RAJ` are requested.

The full engine produces separate P_RAM, P_RAJ and P_RAJ_miner capacities.
Preserve them; they are different assessments. Inspect the returned stress and
strain loops, damage increments and derived cyclic constants. Internal HCM run
indices refer to the engine's repeated-sequence processing and are not original
physical timestamps. Each point is assessed separately to avoid assuming every
FE location has a proportionally scaled history.

## Discriminate a false engineering pass

The qualifier solves a 3D bar with eight samples per first period. Its energy
defect is approximately `1e-14`, yet the refined displacement and stress
waveforms differ by 80%. `assess_fatigue_history` rejects that source history.
Refine the same physical forcing and compare the signed stress again. A stress
range with the right maximum can still have the wrong reversal sequence.

The FKM reference reproduces the upstream example (about 239646 P_RAM and
781480 P_RAJ cycles), while a separately evaluated Masing equation checks loop
strain ranges. Report these as software/method verification. They are not
independent fatigue experiments, component reliability or guideline certification.
