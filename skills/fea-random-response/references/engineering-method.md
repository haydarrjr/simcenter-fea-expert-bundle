# Stationary flexible-structure random response

## Contents

1. Select the physical and stochastic model
2. Input and response spectral matrices
3. Numerical integration and coverage
4. Recover stress and interpret RMS
5. Test correlated inputs
6. Solver/API operations and unsupported families

## Select the physical and stochastic model

Start with the requested quantity and operating state. The flexible linear reference here assumes elastic behavior, fixed bilateral constraints, small motion, time-invariant mass/stiffness and stationary force-pattern multipliers.

A static equilibrium alone does not supply a valid dynamic tangent for a
pretensioned contact assembly. Establish preload inheritance, temperature,
contact opening/sliding, material state and tangent symmetry. If stochastic
motion changes the contact active set, a single stationary linear transfer
function is insufficient. For rotating equipment, identify gyroscopic and
speed-dependent terms before using symmetric real modes. For deterministic
shock, use the time history or an appropriately defined response spectrum;
a stationary PSD/RMS calculation does not answer the peak transient question.

Check rotation and relative member chord RMS where relevant to the small-motion assumption, including regions outside the requested output. Peak motion, contact state and material limits need their own evidence.

## Input and response spectral matrices

With the frequency convention `exp(+iωt)`, the dynamic stiffness is

\[
D(\omega)=K-\omega^2M+i\omega C,\qquad H(\omega)=L D(\omega)^{-1} B.
\]

`B` contains actual spatial load vectors resolved from selected deck load-set
IDs. `L` recovers a nodal DOF, element-end action or PBAR normal stress. The
source API uses a **one-sided spectral matrix per Hz** for the load multipliers.
If a load pattern is 1 N, a multiplier PSD of 4/Hz corresponds to 4 N²/Hz.
If the pattern is 100 N, the same multiplier PSD gives 40,000 N²/Hz. Do not
silently normalize load patterns or confuse per-Hz and per-rad/s densities.

The complex input spectral matrix must be Hermitian positive semidefinite
at each frequency. Its diagonal entries are nonnegative auto spectra, and

\[
S_{ij}=\gamma_{ij}\sqrt{S_{ii}S_{jj}}\,e^{i\theta_{ij}},\quad
S_{ji}=S_{ij}^{*},\quad |\gamma_{ij}|\le1.
\]

Pairwise coherence bounds are necessary but not sufficient for three or more
inputs: check the full matrix eigenvalues. A negative eigenvalue is not
repaired by changing a diagonal or silently clipping it. Re-estimate the
joint cross spectra from consistent synchronized measurements or choose an
explicit physically justified coherent-field model. Piecewise-linear
interpolation between valid Hermitian PSD matrices preserves admissibility.

The output spectral matrix and zero-lag covariance are

\[
S_y(f)=H(2\pi f)S_x(f)H(2\pi f)^{H},\qquad
\Sigma_y=\int_{f_a}^{f_b}\operatorname{Re} S_y(f)\,df.
\]

Use the conjugate transpose. Dropping phase, substituting `H Hᵀ`, or summing
individual RMS amplitudes changes the problem. A pair of identical coherent
loads can quadruple variance; an equal anti-phase pair can cancel it. The
source report computes the auto-spectra-only counterfactual and the cross-term
contribution so the consequence of ignoring coherence is quantitative.

## Numerical integration and coverage

Solve `Kφ=λMφ`, with `ΦᵀMΦ=I`. With constant modal damping ratio ζ,

\[
H(f)=L\Phi\,\mathrm{diag}
\left[(\lambda_j-\omega^2+i2\zeta\sqrt{\lambda_j}\omega)^{-1}\right]
\Phi^TB.
\]

The current source calculation uses the **complete** bounded frame basis;
there is no arbitrary first-six-mode truncation. A production large FEM needs
mode-selection, residual flexibility, effective-mass/output convergence and
the correct operating tangent. Effective mass alone does not guarantee local
stress convergence, and missing high-frequency modes can affect response
below the highest extracted natural frequency.

Partition frequency integration at PSD knots and resolve in-band resonances with a damping-sensitive grid or adaptive quadrature. Check that the covariance and RMS converge even under cancellation.

The reported error is an embedded numerical estimate, not a rigorous interval
bound or a model-form error bound. Independently verify a high-Q mode, narrow
band, varying PSD slope and coherent cancellation. For a force-driven SDOF
under constant one-sided white force PSD `S0`, the all-frequency variance is

\[
\sigma_x^2={S_0\over8\zeta m^2\omega_n^3}.
\]

A finite band omits positive tails; compare the actual integration limits.
For independent verification, use a reference with separately assembled M/K
and a declared damping matrix. Check the sensor variance with an independent
direct complex response and quadrature when appropriate matrices and
reference calculations are already available.

## Recover stress and interpret RMS

Linear recovery can produce covariance of end forces and normal stresses at
specific PBAR recovery points. Keep element, end, physical point, frame and
state attached. The opposite signs at two member ends follow the defined
internal-action convention; they do not justify taking independent absolute
maxima before recovering stress.

`RMS = sqrt(variance)` describes a second moment. It is not a deterministic
maximum, a finite-duration exceedance guarantee or a fatigue life. A 3σ
threshold has a single-instant Gaussian interpretation only when Gaussian
assumptions hold; the chance of exceeding it during a long test is different.
Componentwise RMS values do not define a simultaneous tensor. Von Mises is
nonlinear in tensor components; evaluating it on an invented vector of
component RMS values is generally not a physical stress state.

Peak estimation needs duration, bandwidth/spectral moments and a stated
stochastic model. Fatigue needs appropriate stress process recovery, cycle
statistics/validated time-history reconstruction, material S–N data, mean
stress treatment and cumulative-damage assumptions. Non-Gaussian excitation,
impact, sliding or changing contact requires additional modeling. Report
normal-stress RMS and covariance only for the recovered components. Full
torsional/shear equivalent-stress peaks and life need additional evidence.

## Test correlated inputs

Compare independent, fully correlated and phase-shifted inputs using the same auto-spectra. Evaluate the actual complex cross terms in the response. Check Hermitian symmetry, positive semidefiniteness and frequency integration. Separate sensitivity to the correlation model from errors introduced by modal truncation.

## Solver/API operations and unsupported families

Use [Nastran random response](nastran-random-response.md) for effective random controls and [solver investigation](../../fea-solver-investigation/SKILL.md) to bind the deck and results to one job. Use [BatchPost random displacement](../../batchpost-actions/references/random-displacement-csv.md) when its scope matches the requested export. Use [specialized dynamics](../../fea-dynamics/references/advanced-dynamics.md) for rotor, cyclic, aeroelastic, DDAM or acoustic decisions.
