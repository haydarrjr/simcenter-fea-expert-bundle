# Verification, validation and uncertainty tied to the decision

## Contents

1. Separate uncertainty sources
2. Numerical verification
3. Independent model-form checks
4. Evaluate preload sensitivity
5. Evidence and acceptance

## Separate uncertainty sources

Code verification asks whether the implemented equations are solved correctly.
Solution verification addresses discretization/iteration error for a specified
model. Validation addresses whether that model represents the intended physical
system. Input uncertainty, model-form discrepancy and numerical error are
different terms; a small mesh difference cannot absorb missing contact physics
or an uncertain friction coefficient.

Define the decision QoI first: maximum bolt force, contact opening sector,
pressure average, displacement at a physical point, modal subspace, frequency
band response or heat rate. Bind it to model, revision, units, frame, region and
step. An unchanged output name is not the same QoI after remeshing, changing
recovery location or altering the contact state.

## Numerical verification

Use independent analytical, high-precision or metamorphic checks that would fail
if the implementation were wrong. The joint workflow compares its active-set
Newton solution with 50-digit Decimal enumeration of all 256 contact states.
The assembly workflow independently checks a hand-summed six-mode system,
origin/frame invariance and virtual-work transfer. The tensor workflow uses
rotation and hydrostatic-offset invariance. Tests that merely reproduce the
same internal algorithm are weaker evidence.

For mesh refinement, the constant-ratio Richardson/GCI implementation estimates
order only in its supported trend and identity regime. Read
[constant-r refinement](constant-r-refinement.md) for its assumptions and
failure codes. A converged global force can coexist with an unconverged opening
boundary, bolt force or singular peak stress. Study the actual decision QoI
under both mesh and nonlinear increment refinement. Keep tolerances dimensional
where their quantities are dimensional.

## Independent model-form checks

Use equilibrium, energy and work-conjugate transfer as necessary checks, not
proof that the constitutive law or constraints are correct. Compare credible
alternative models: flexible versus rigid flange, unilateral versus bilateral
mount, Euler–Bernoulli versus Timoshenko, and actual thermal restraint versus
free expansion. Hold the physical inputs fixed when comparing model form.

For smooth linear problems, the first-order sensitivity is
`delta q = K^-1(delta f - delta K q)`. This explains why high stiffness contrast
or a near mechanism can amplify small uncertainty. It is not valid across a
contact active-set change. Near opening/slip, use resolved variants and inspect
the changed mechanism rather than propagate one tangent derivative everywhere.

Do not assign a probability of failure from arbitrary uniform parameter ranges.
Specify evidence for distributions, dependence and epistemic bounds. A bounded
scenario envelope is useful without pretending to be a calibrated reliability
model. Material strength statistics, preload scatter, friction and temperature
uncertainty must match the relevant population and operating condition.

## Evaluate preload sensitivity

Perturb the initial preload and each independent thermal or friction input within justified bounds. Record any change in contact state before interpreting derivatives. When important quantities depend on separation or slip, compare at least one native response on either side of the transition.

## Evidence and acceptance

Compare source artifacts and receipts on separate axes. Hash equality pins
bytes; it does not authenticate a native run or physical measurement. A source
model can pass internal arithmetic while lacking experimental or flexible-model
correlation. Preserve model-form limitations and the domain where the benchmark
applies. Historical acceptance evidence is scoped to its observed model and release.

Record the strongest falsifier exercised, the numerical/physical discrepancy
that remains, its effect on the decision and the next experiment that would
reduce it. Optimization is only credible if every candidate preserves constraints,
physical identity and an appropriate validation model; reducing a surrogate
objective must not exploit missing contact, an omitted loadcase or an invalid
transfer. Re-evaluate the engineering evidence for each candidate variant.
