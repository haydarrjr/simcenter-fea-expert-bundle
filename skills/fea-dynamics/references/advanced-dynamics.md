# Specialized dynamics: decision equations and discriminating checks

Use these methods to select and verify specialized dynamics analyses. Check the solver formulation, output definitions and relevant tool profile for the installed release.

## Cyclic symmetry

For N sectors and harmonic index h, corresponding boundary displacements obey
`u_right = exp(i 2 pi h/N) T u_left`, where T rotates physical components.
Geometry alone is insufficient: material, mesh correspondence, preload,
contact state and support/load symmetry must also fit the reduction. A single
nonperiodic mount or open contact sector breaks the assumed cyclic operator.
For real structures, the h and N-h harmonics have conjugate relationships;
matching a frequency does not establish that the phase/mode reconstruction is
correct. Retain both real and imaginary parts where required.

For a periodic chain of equal masses `m` and scalar springs `k`, the cyclic
eigenvalues are `lambda_h = 4 k/m sin²(pi h/N)`. Check the rigid mode and
conjugate harmonic pairs. Compare reconstructed displacement and interface
work to verify phase and orientation.

## Random response and shock

For a one-sided cross-spectral matrix S_ff(f),
`S_xx = H S_ff H*`; variance is the integral of the diagonal over positive Hz.
Keep PSD units, frequency convention, bandwidth and damping explicit. A peak
harmonic amplitude is not an RMS random response, and a scalar PSD cannot
represent multiple correlated excitations.

For two contributions with variances `v1` and `v2` and covariance `c12`,
the combined RMS is `sqrt(v1 + v2 + 2 c12)`. Check that the covariance or
cross-spectrum is Hermitian positive semidefinite. Investigate negative
variances in the data or transform. When phase varies with frequency, integrate
the full cross-spectrum over the selected band.

DDAM and response-spectrum methods use their specified shock spectra, modal
participation and combination procedures. They are not interchangeable with a
PSD analysis. Obtain the actual spectrum definition and governing acceptance
standard; do not invent Navy coefficients or claim that a generic modal sum is
a qualified DDAM calculation. Rigid-body participation, missing mass and
truncation residuals need explicit treatment.

For base-motion SRS setup, verification and routing use [response spectra](response-spectrum.md).

## Rotating assemblies

The rotating linearized equation generally contains
`M qdd + (C + Omega G) qdot + (K + Kcentrifugal) q = f`, with a gyroscopic
matrix G that is skew-symmetric in an energy-consistent formulation. Gyroscopic
forces do no instantaneous work because `qdot^T G qdot = 0`, but they split
forward/backward whirl. Deleting G can preserve a zero-speed natural frequency
while giving the wrong critical-speed intersection.

Use operating-speed equilibrium, bearing cross-coupled stiffness/damping,
rotor/stator frames and spin direction. Track modes by shape/subspace and whirl
sense through a Campbell diagram, not by sorting frequencies at each speed.
Require a qualified gyroscopic eigensolution or documented rotor response for critical speeds and stability. A non-gyroscopic mounted-assembly model cannot establish those results.

## Aeroelasticity

Distinguish static divergence from dynamic flutter. A positive structural
stiffness and real zero-speed modes do not prove aeroelastic stability. The
coupled operator includes aerodynamic forces depending on dynamic pressure,
Mach number and reduced frequency, often with complex phase. A flutter claim
requires the relevant damping branch to cross zero under a documented solution
method, with basis, aerodynamic panel and speed-grid convergence.

Retain structural-to-aerodynamic interpolation and its work-conjugate load
transfer. An interface that preserves force but loses moment changes the work
input and may move a predicted instability. Check interface virtual work before interpreting the coupled result. Obtain the aerodynamic matrices and damping branches from a qualified flutter workflow.

## Vibroacoustics

At a fluid/structure interface, normal velocity continuity and balanced traction
must use consistent normals. With peak complex amplitudes, average acoustic
power is `0.5 Re(integral p v_n* dA)`; RMS amplitudes use a different factor.
Flipping the interface normal can change power sign while leaving pressure
magnitude unchanged. Compare power balance, phase, radiation boundary and mesh
resolution relative to acoustic wavelength `c/f`.

A structural eigenfrequency is not a sound-pressure prediction. Obtain fluid
density, sound speed, coupling areas, boundary impedance and acoustic result
units from actual source data and the documented solver family. Validate a
simple impedance/power reference before a whole-assembly acoustic interpretation.
