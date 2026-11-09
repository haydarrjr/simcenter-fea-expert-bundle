# Specialized dynamics: decision equations and discriminating checks

These are engineering methods for the legacy cyclic, random, rotor,
aeroelastic, DDAM and vibroacoustic routes. They do not advertise native handlers
or a new numerical solver. Use the checked API catalog for actual operations;
an absent result type, solver descriptor or Runtime capability is an explicit
implementation/qualification gap.

## Cyclic symmetry

For N sectors and harmonic index h, corresponding boundary displacements obey
`u_right = exp(i 2 pi h/N) T u_left`, where T rotates physical components.
Geometry alone is insufficient: material, mesh correspondence, preload,
contact state and support/load symmetry must also fit the reduction. A single
nonperiodic mount or open contact sector breaks the assumed cyclic operator.
For real structures, the h and N-h harmonics have conjugate relationships;
matching a frequency does not establish that the phase/mode reconstruction is
correct. Retain both real and imaginary parts where required.

A simple independent reference is a periodic ring of N equal masses m joined
by identical scalar springs k. Its eigenvalues are
`lambda_h=4 k/m sin²(pi h/N)`. For N=8, m=2 kg and k=200000 N/m, h=0 is a
rigid mode and h=1 and h=7 have the same frequency, about 38.52 Hz. Swapping a
phase boundary while preserving that frequency can still give the wrong
forced-response shape. Compare reconstructed displacement and interface work,
not only the eigenvalue. This scalar ring is an analytical check, not a bladed
disk stress model.

## Random response and shock

For a one-sided cross-spectral matrix S_ff(f),
`S_xx = H S_ff H*`; variance is the integral of the diagonal over positive Hz.
Keep PSD units, frequency convention, bandwidth and damping explicit. A peak
harmonic amplitude is not an RMS random response, and a scalar PSD cannot
represent multiple correlated excitations.

Two equal unit-variance contributions with coherence/correlation 0.9 have
combined RMS `sqrt(1+1+2*0.9)=1.94936`, whereas an independent-input assumption
gives `sqrt(2)=1.41421`. The covariance/cross-spectrum must be Hermitian positive
semidefinite; negative variance is a data/transform error, not a quantity to
clip without explanation. Use this comparison to falsify an unjustified SRSS
combination. When phase varies with frequency, integrate the full complex cross
spectrum rather than a single broadband correlation coefficient.

DDAM and response-spectrum methods use their specified shock spectra, modal
participation and combination procedures. They are not interchangeable with a
PSD analysis. Obtain the actual spectrum definition and governing acceptance
standard; do not invent Navy coefficients or claim that a generic modal sum is
a qualified DDAM calculation. Rigid-body participation, missing mass and
truncation residuals need explicit treatment.

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
The mounted-assembly source kernel has no gyroscopy and must not be used to
claim rotor stability or a speed-dependent critical-speed margin.

## Aeroelasticity

Distinguish static divergence from dynamic flutter. A positive structural
stiffness and real zero-speed modes do not prove aeroelastic stability. The
coupled operator includes aerodynamic forces depending on dynamic pressure,
Mach number and reduced frequency, often with complex phase. A flutter claim
requires the relevant damping branch to cross zero under a documented solution
method, with basis, aerodynamic panel and speed-grid convergence.

Retain structural-to-aerodynamic interpolation and its work-conjugate load
transfer. An interface that preserves force but loses moment changes the work
input and may move a predicted instability. Use the implemented conservative
transfer falsifier before interpreting the coupled result. No aerodynamic matrix
or flutter solver is implemented in the six-DOF source example.

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
