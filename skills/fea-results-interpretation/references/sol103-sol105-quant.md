# SOL103/SOL105 quantitative source procedure

Use these independent checks on supplied, state-bound K/M/eigenpair evidence
or a justified Euler-column comparison at a pinned static preload. Use the
[free-free modal workflow](../../fea-dynamics/references/sol103-free-free.md)
for near-zero modes or a semidefinite stiffness operator.

## SOL103 inputs and checks

For the restrained Cartesian reference below, require real positive
eigenvalues, symmetric positive-definite K (N/m) and M (kg), and explicit
mass-normalized vectors (`1/sqrt(kg)`). Keep damped, complex or mixed DOF
problems outside this reference. Preserve the as-reported matrices.
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

Apply the declared relative tolerance to both residuals. Unrelated stiff DOFs
can conceal an incorrect soft mode in a normwise check. Apply the orthogonality
tolerance to the raw M-inner product and report normalized correlation separately.

For each near-degenerate cluster, compare the mass-whitened subspaces.
Require full supplied/reference ranks and the minimum squared principal
correlation to meet `min_subspace_correlation`; an average cannot conceal a
missing direction. Report individual MAC values without treating them as
unique mode matches. A near-degenerate cluster still requires
**INDETERMINATE** review. A partial supplied basis also remains
**INDETERMINATE** because unseen repeated modes have not been excluded.
A numerical failure takes precedence over an indeterminate match. Mark
unsupported inputs and mismatched physical identities before comparison.

Use the optional uniform, linear-elastic, undamped, fixed-free
Euler–Bernoulli beam reference only for modes 1 and 2:
`f_n = beta_n^2/(2*pi*L^2)*sqrt(E*I/(rho*A))`,
with `beta_1 ≈ 1.87510407`, `beta_2 ≈ 4.69409113`. Require the declared
uniformity and boundary basis; agreement does not establish 3D mesh adequacy.

For an independent scalar mode check, verify `lambda = K/M`,
`f = sqrt(lambda)/(2*pi)` and `M phi² = 1` under mass normalization.
Check mapping, symmetry and basis completeness before evaluating modal claims.

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
is `en-US.PL20251024315120185.basic_dynamics.id472236`. Verify the release's applicability before using the caution band.

Return computed metrics, declared tolerances, retained identities and
assumptions, and all rejection/review findings. Keep native, solver, client
and engineering outcomes tied to independently recorded evidence.
