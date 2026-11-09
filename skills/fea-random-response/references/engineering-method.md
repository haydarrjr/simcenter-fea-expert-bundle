# Stationary flexible-structure random response

## Contents

1. Select the physical and stochastic model
2. Input and response spectral matrices
3. Numerical integration and coverage
4. Recover stress and interpret RMS
5. Worked case and falsifiers
6. Solver/API operations and unsupported families

## Select the physical and stochastic model

Start with the requested quantity and operating state. The implemented
calculation assumes linear isotropic elastic frame members, fixed bilateral
constraints, small displacement, time-invariant mass/stiffness and stationary
force-pattern multipliers. It solves the full flexible model read from the
effective deck; it is not a six-DOF rigid assembly approximation.

A static equilibrium alone does not supply a valid dynamic tangent for a
pretensioned contact assembly. Establish preload inheritance, temperature,
contact opening/sliding, material state and tangent symmetry. If stochastic
motion changes the contact active set, a single stationary linear transfer
function is insufficient. For rotating equipment, identify gyroscopic and
speed-dependent terms before using symmetric real modes. For deterministic
shock, use the time history or an appropriately defined response spectrum;
a stationary PSD/RMS calculation does not answer the peak transient question.

The source computation derives rotation-vector RMS and relative member chord
RMS across the **whole model**, including locations absent from the requested
output list. It requests model-form review above the stated small-motion
screen. An RMS screen can disqualify a linear model; passing it cannot prove
peak-motion bounds, constant contact state or elastic material capacity.
There is no yield stress inferred from E or from a generic steel label.

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

The integrator inserts neighborhoods around every in-band natural frequency,
using damping-dependent widths, then compares 8- and 16-point Gauss–Legendre
quadratures and adaptively refines the largest normalized covariance error.
The error scale is based on uncoupled output variances so cancellation does
not produce a misleading relative error. Input PSD knots also partition the
integration intervals. An evaluation/iteration budget failure remains an
unresolved integral; it is not returned as a converged RMS.

The reported error is an embedded numerical estimate, not a rigorous interval
bound or a model-form error bound. Independently verify a high-Q mode, narrow
band, varying PSD slope and coherent cancellation. For a force-driven SDOF
under constant one-sided white force PSD `S0`, the all-frequency variance is

\[
\sigma_x^2={S_0\over8\zeta m^2\omega_n^3}.
\]

A finite band omits positive tails; compare the actual integration limits.
For independent verification of the gantry, OpenSees supplies separately
assembled M/K, direct complex solves use a reconstructed modal damping matrix,
and SciPy QUADPACK integrates the sensor variance. This uses neither the
production element matrices nor its modal transfer/quadrature implementation.

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
impact, sliding or changing contact requires additional modeling. The current
implementation returns normal-stress RMS and covariance, and expressly does
not return a full torsional/shear equivalent-stress peak or life.

## Worked case and falsifiers

The flexible gantry's eccentric body excites sway, torsion and arm bending.
Two deck load patterns apply X forces at different nodes. Over 5–120 Hz their
constant cross spectrum is `[[4,1.2],[1.2,9]] /Hz`, with ζ=0.015. The sensor-X
RMS is about **0.302 mm**. This agreement is with a separately executed
OpenSees elastic reference, not a licensed Simcenter random run or test data.

Use these competing hypotheses and falsifiers:

| Apparent conclusion | Discriminating check | Result that changes the decision |
| --- | --- | --- |
| A coarse frequency grid establishes the RMS | Seed poles using ζ, refine quadrature and compare an independent integral | A missed narrow mode materially increases variance |
| Inputs can be treated as independent | Retain measured complex cross spectra and compute the auto-only counterfactual | Correlated addition/cancellation changes governing output |
| All pairwise coherences ≤1 make a valid input | Check eigenvalues of the full cross-spectral matrix | A negative eigenvalue makes the proposed joint excitation impossible |
| Small static displacement validates random response | Compute all-node rotations and all-member relative RMS motion | A held-out 0.4 m member develops about 84.8 mm chord RMS and requires another model |
| The local maximum is sqrt(sum of component RMS²) | Recover the full joint stress process/covariance with physical states | The constructed envelope combines incompatible phases/components |
| Real symmetric modes represent a spinning rotor | Inspect speed, gyroscopic matrix and forward/backward branches | Nonzero gyroscopic coupling requires a different eigenproblem |

## Solver/API operations and unsupported families

Use the solver-investigation skill to join actual effective-deck bytes and
state-specific results. The verified Siemens helpers can prepare an explicitly
selected linear solution/step, attach borrowed BCs, export the effective deck
with observed typed options and read borrowed nodal displacement results.
These source helpers do not configure a native random solution by guessing
descriptor strings. Actual installation metadata, qualified result-owner
acquisition and registered Runtime FEA operations remain external dependencies.

The portable `fea-random-response` entrypoint is now a real separate SKILL.md.
Legacy rotor, cyclic, aeroelastic, DDAM and acoustic aliases still route to
advanced dynamics guidance; they are not separate installed skills or
implemented specialist solvers. When one of those families is physically
required, explain its equations, sources and concrete next verification rather
than presenting this elastic random solver as a universal substitute.
