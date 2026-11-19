# Solid and thermal method

Use release-specific Siemens Help for the chosen element, material and thermal sequence.
The source API uses 3D isotropic small-strain elasticity with positive material
parameters, linear tetrahedra or fully integrated trilinear hexahedra; conduction
may use a symmetric positive-definite tensor. It rejects nearly incompressible
displacement-only applications rather than claiming a mixed formulation.

## Governing operators

`K = integral(B.T D B dV)`, `M = integral(rho N.T N dV)`,
`H = integral(gradN.T k gradN dV)` and
`C = integral(rho cp N.T N dV)`. The thermal equivalent load is
`fT = integral(B.T D alpha*(T-Tref)*[1,1,1,0,0,0] dV)`.
Strain uses engineering shear; tensor stress retains physical shear components.
Recover stress from mechanical strain after subtracting eigenstrain.

For prescribed displacement/MPCs, retain constraint work and reactions. In a
fully restrained isotropic body, heating creates hydrostatic stress; von Mises
can be zero while the normal stresses are large. A zero von Mises contour is
not evidence of zero thermal stress or acceptable brittle failure margin.

Transient conduction solves the declared theta-method system. `thermal_capacity`
chooses consistent or row-sum-lumped capacity. Lumping changes the discrete
method and must be reported. A converged consistent-capacity step can overshoot
outside source-free temperature bounds; there is no automatic physical pardon
for a small residual. Jointly examine time step, mesh, capacity and conductivity
before retrying. The implementation records a maximum-principle falsifier and
rejects negative Kelvin in both steady and transient solutions.

## Reproducible work

Use a two-material reference with distinct expansion coefficients to test thermal load transfer and restrained stress. Declare initial and prescribed temperatures and force balance.

Use analytical affine fields, independently assembled reference operators when
available, source-bound archived Nastran displacement and reaction data, time
decay and refinement as distinct verification paths. Agreement with archived
results checks the mathematical model and mapping under the shared assumptions.

## Discriminating checks

- Thin bending: low-order solids can lock. Compare successive QoI results;
  a small equilibrium residual alone says nothing about bending accuracy.
- Thermal history: inspect storage plus boundary heat per interval; merely
  reaching the requested final temperature can hide the wrong transient path.
- Interface: distinguish shared DOFs, explicit MPCs and disconnected bodies.
  Global force balance may pass while relative interface motion is wrong.
- Modal: require a physically justified mass model, support rank and eigenpair
  residual; unstressed modes cannot consume preload or temperature fields.
- Nonlinear intent: large strain, changing contact, yielding, rotations or
  stress stiffening require another model family. Report the gap explicitly.
