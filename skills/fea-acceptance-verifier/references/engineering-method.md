# Decide whether a result supports the engineering claim

Contents: [claim and identity](#match-the-claim-to-a-falsifiable-quantity-and-physical-state),
[independent mechanics](#use-independent-mechanics-not-a-solver-success-label),
[false-convergence case](#worked-false-convergence-case),
[authentication and acceptance](#separate-artifact-integrity-authenticated-observation-and-acceptance).

## Match the claim to a falsifiable quantity and physical state

Start with the intended decision: for example, whether a pretensioned flange
retains its load path under temperature, pressure and eccentric service loading.
Separate bolt-force increase, interface opening/slip, local stress, fatigue and
thread capacity. A reduced joint equilibrium calculation can falsify an incorrect
load split; it cannot establish continuum hotspot stress or thread stripping
capacity. State which quantity each independent reference actually predicts.

Bind model/revision/owner, mesh, case, frame, units and step to the actual
artifacts. Record source paths and SHA-256 hashes, then reconcile physical
identities before comparing numerical values. Use independent tool and job
evidence for origin and native execution.

For nonlinear evidence, bind the effective deck, native log, release, achieved step and result history. Record the source of any extracted iteration table and distinguish a synthetic reference trace from an export of the run.

## Use independent mechanics, not a solver success label

For a complete static free body in one frame, check force and moment resultants:

\[
\mathbf r_F=\sum\mathbf F_{external}+\sum\mathbf R,
\qquad
\mathbf r_M=\sum(\mathbf r\times\mathbf F)+\sum\mathbf M.
\]

Include inertial terms for dynamics and use the correct origin for moments.
Apply an absolute floor together with a declared relative budget so a small
reference load does not conceal an arbitrarily large relative defect. Extract
all relevant constraint/contact reactions; a missing interface cannot be
repaired by loosening the equilibrium tolerance.

Evaluate energy in the actual loading sequence. External, thermal, elastic,
plastic, kinetic, frictional and numerical stabilization contributions have
different meanings. A final strain-energy value alone is not work balance.
Use artificial-energy ratio as a diagnostic of numerical support, with a
project-specific limit; it does not replace force balance, contact status or
path-dependent constitutive checks.

For the coupled joint reference, bolt stiffness and member compliance determine
the pre-separation load split. Under an eccentric load, opening changes the
active contact set and redistributes reactions. Compare the solved normal-force
and moment balance, station gaps and bolt loads; separately test tangential
friction demand. Do not treat an elastic stick trial beyond friction capacity as
a computed post-slip solution. Locked pretension is a retained state, not a
constant force blindly re-applied at every service step.

## Test an apparently converged solution

Select an independent check sensitive to the proposed failure. Compare the predicted and observed reaction, residual, energy change and active contact state at the same accepted increment. A change to load step or contact enforcement can expose an apparent terminal solution that is unstable or violates equilibrium.

## Separate artifact integrity, authenticated observation and acceptance

Artifact hashes establish file integrity. Native identity and execution require evidence from the bound host or exact solver job, with independent readback where applicable. An authenticated observation is evidence for the operation and target it covers. Engineering acceptance also requires a defensible physical model, numerical verification and the applicable decision criteria. An independent source calculation can establish a contradiction under its stated assumptions. Report the
source result and the absent native evidence separately.

Use these outcome distinctions:

- A demonstrated wrong identity, equilibrium defect, impossible result or
  contradicted control is a failure of the corresponding claim.
- Missing native/solver evidence is NOT_RUN or UNVERIFIED; do not invent a
  failed solver run or grant engineering acceptance.
- A valid reduced-model calculation is source evidence within its assumptions.
  It remains insufficient for unsupported continuum, post-slip or fatigue claims.
- Contact/mesh/time-step/model-form uncertainty requires a discriminating study,
  not an average PASS that hides one failed physical direction or load stage.

Test for contradictory state, unknown origin or missing independent readback. Consult the [runtime gate](../../fea-native-runtime-gate/SKILL.md) for case-specific evidence.
