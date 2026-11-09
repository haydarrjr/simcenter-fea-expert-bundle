# SOL103/SOL105 quantitative source procedure

Use this path for explicit K/M/eigenpair data or a justified Euler-column
comparison with a pinned static load state. Run `assess-sol103` or
`assess-sol105` on closed v1 JSON; retain unknown physical facts as unresolved.
Do not infer native results, capacity or authenticated provenance from source
arithmetic. Keep SOL106 nonlinear history **NEXT WAVE / NOT IMPLEMENTED**.

## SOL103 inputs and checks

Require 1–12 Cartesian translational DOFs, real positive eigenvalues,
exactly symmetric positive-definite K (N/m) and M (kg), and explicit
mass-normalized vectors (`1/sqrt(kg)`). Reject asymmetric, singular, massless,
rigid, damped, complex or mixed translation/rotation cases; never repair K/M.
Pin model/revision, owner, material, BC/load state, frame, solution step and
ordered DOF identities across the supplied and reference data. Preserve
separate reference artifact and per-mode provenance; declarations remain
unauthenticated.

Evaluate the following against the supplied policy:

| Check | Computed quantity |
| --- | --- |
| Frequency | `f = sqrt(lambda)/(2*pi)` and relative supplied-frequency discrepancy |
| Normwise residual | `norm(K*phi-lambda*M*phi) / ((norm(K,F)+lambda*norm(M,F))*norm(phi))` |
| Mode-action residual | `norm(K*phi-lambda*M*phi) / (norm(K*phi)+lambda*norm(M*phi))` |
| Mass normalization | `phi.T*M*phi`, compared with 1 |
| Raw M-orthogonality | `abs(phi_i.T*M*phi_j)` |
| Separate normalized correlation | Raw M-inner product divided by both mass norms' square roots |
| Matching MAC | `(phi.T*M*ref)^2 / ((phi.T*M*phi)*(ref.T*M*ref))` |

Apply `max_relative_residual` to **both** residuals: unrelated stiff DOFs
must not conceal an incorrect soft mode. Apply `max_mass_orthogonality` to
the **raw** M-inner product; do not substitute normalized correlation.

For each near-degenerate cluster, compare the mass-whitened subspaces.
Require full supplied/reference ranks and the minimum squared principal
correlation to meet `min_subspace_correlation`; an average cannot conceal a
missing direction. Report individual MAC values without treating them as
unique mode matches. A near-degenerate cluster still requires
**INDETERMINATE** review. A partial supplied basis also remains
**INDETERMINATE** because unseen repeated modes have not been excluded.
Any computed failure takes precedence as **SOURCE_CHECKS_FAIL**. Malformed
or unsupported contracts, including mismatched reference physical identities,
reject with CLI exit 2; do not relabel those requests as executed comparisons.

Use the optional uniform, linear-elastic, undamped, fixed-free
Euler–Bernoulli beam reference only for modes 1 and 2:
`f_n = beta_n^2/(2*pi*L^2)*sqrt(E*I/(rho*A))`,
with `beta_1 ≈ 1.87510407`, `beta_2 ≈ 4.69409113`. Require the declared
uniformity and boundary basis; agreement does not establish 3D mesh adequacy.

As a simple independent check, K=4 N/m, M=1 kg, lambda=4 s^-2 and phi=1
give f=1/pi Hz, mass norm 1, both residuals zero and MAC 1. Test adverse
claims with a nonsymmetric soft block beside stiff DOFs, scaled but
unnormalized modes, swapped reference DOFs, frequency disagreement, and an
incomplete repeated eigenspace.

## SOL105 inputs and checks

Require positive E, I and length, linear elasticity, small deflection and
explicit uniform-column/boundary justification. Use
`Pcr = pi^2*E*I/(K_eff*L)^2` with pinned/pinned `K_eff=1`, fixed/free
`K_eff=2`, or fixed/fixed `K_eff=0.5`.

Pin the static preload's model/revision, owner, subcase and source artifact
to the buckling request. Require a distinct buckling subcase and negative
preload for compression. Keep preload magnitude, positive eigenfactor and
`P_eigen = lambda*abs(preload)` separate. Compare the latter with Euler Pcr
using the declared absolute-plus-relative load budget.

Return **SOURCE_CHECKS_FAIL** when the arithmetic comparison fails, including
contact cases. Otherwise contact remains **INDETERMINATE**, even inside the
documented lambda caution band. Reject tension-as-compression, unsupported
boundary factors, stale preload, absent justification and plastic/nonlinear
collapse interpretations. No linear eigenfactor establishes collapse capacity.

## Documentary scope and output

Attribute the contact caution `0.9 <= lambda <= 1.1` specifically to
Simcenter Nastran **2606**, SKU `PL20251024315120185`, document
`en-US.PL20251024315120185.User.id1369897`. The SOL103 documentary reference
is `en-US.PL20251024315120185.basic_dynamics.id472236`. Their fetched
source/content status is **DRAFT/COMPLETE**; these are documentary constraints,
not solver execution. Preserve `applicability_to_declared_solver=UNVERIFIED`;
do not generalize the band to another declared solver or release.

Return computed metrics, declared tolerances, retained identities and
assumptions, and all rejection/review findings. Keep native, solver, client
and engineering statuses **NOT_RUN**, `authenticated=false`,
`native_executable=false` and `engineering_accepted=false`. Read
P10 worked cases and source limits (source: fea_expert_agent_plugin/docs/qualification/structural-quant-source-slice.md)
for further examples and numerical range limits.
