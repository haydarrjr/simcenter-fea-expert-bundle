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
artifacts. In `run-case`, the manifest lists source paths and SHA-256 hashes;
the runner reads bounded regular files, checks bytes, joins physical identities
and executes the relevant engineering processors. Those hashes establish which
bytes were assessed. They do not authenticate the author or prove a native run.
Reject a model/mesh/case join conflict before comparing numerical values.

For nonlinear evidence, the implemented `fea.nonlinear-diagnosis.v2` request
binds the effective deck and log hashes plus exact Nastran2606 release SKU
`PL20251024315120185`. Optional iteration CSV has its own hash, complete case
identity and declared origin. The CSV is FEA-owned interchange, not invented
native F06 syntax. Preserve MANUFACTURED_TEST_TRACE versus ADAPTER_EXPORT.

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

## Worked false-convergence case

Run the bundled eight-bolt flange case:

```sh
python -m fea_agent run-case examples/engineering_v2/joint_case.json
python -m fea_agent diagnose-nonlinear examples/engineering_v2/nonlinear_false_convergence.json
```

The nonlinear example is explicitly manufactured. Its deck fragment selects
SOL401, a preload subcase and dependent service loading. Its F06 fragment uses
documented `ACCUM / ITER / EQU / CON / BLT` column semantics. The numerical
history is a separately hash-bound FEA interchange CSV. Do not describe these
files as a native solver execution or a complete solvable deck.

The last CSV record claims convergence, and the final summary has EQU=y and
BLT=y. That looks reassuring, but CON=n. Independent checks expose the failure:

| Evidence | Calculation | Engineering implication |
|---|---|---|
| Applied force 160,000 N, reaction −142,000 N | Unbalanced force = 18,000 N; 11.25% of applied load | Exceeds the declared 1% budget. |
| Artificial energy 120 J, strain energy 1,000 J | Ratio = 12% | Exceeds the declared 5% numerical-energy budget. |
| Force convergence error 0.04; selected EPSP 0.001 | Error is 40 times the selected criterion | A converged Boolean cannot replace the selected numerical test. |
| Final load factor 0.8 | Only 80% of requested target | Terminal status cannot establish the full service load. |
| Contact summary CON=n | Contact criterion remains unsatisfied | Investigate changing/open contact and residual-bearing interfaces. |

Reject the claimed converged engineering state. Rank checks that discriminate
causes: inspect effective contact selection and reaction completeness; compare
pretension/lock inheritance and zero-service bolt force; correlate contact
change with residual growth; inspect stabilization contribution; then vary load
increments or the constitutive/contact model under a controlled revision.
Merely increasing iteration count or changing a flag cannot remove the measured
18 kN equilibrium defect. Preserve each alternative as a hypothesis with the
specific observation that would falsify it.

## Separate artifact integrity, authenticated observation and acceptance

The actual Runtime client validates descriptive inventory, exact target state,
bounded payloads and BEFORE/AFTER receipt chains. `ExpectedPart` binds identity,
open generation, revision and fingerprint. `HostReceiptVerifier` is an
embedding-owned independent trust port; caller JSON and a self-consistent
hash chain cannot install it. Live reads require an explicit durable client
ledger with pinned trust context; a source-fixture restart cannot clear a host
operation's unresolved hold. A SOURCE_FIXTURE response stays native NOT_RUN.

Even a valid `VerifiedHostReceipt` establishes only the bounded observation it
binds. It does not prove that the correct contact law, mesh or nonlinear material
was chosen, that the solver completed the intended load sequence, or that the
design satisfies its intended-use margin. Conversely, absence of a desktop
does not invalidate a mathematically proved source counterexample. Report the
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

Execute `python -m unittest tests.test_runtime_client_v2 -v` for forged-origin,
wrong-owner, part-ABA, partial-inventory and uncertain-response counterexamples.
Use the [Runtime method](../../fea-native-runtime-gate/references/engineering-method.md)
for callable DTOs and reconciliation, and the
compatibility contract (source: fea_expert_agent_plugin/docs/architecture/runtime-compatibility.md)
for exact source pins and unsupported native operations. Deliver the decisive
numbers, provenance and falsifiers; keep engineering acceptance distinct from
source CI and package validity.
