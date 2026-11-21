# Material behavior, section properties and tensor meaning

## Contents

- [Elasticity and thermal compatibility](#isotropic-elasticity-and-thermal-compatibility)
- [Tangent and secant](#tangent-secant-and-path-dependence)
- [Tensor meaning](#tensor-conventions-are-part-of-the-material-contract)
- [Laminate reasoning](#orthotropy-and-laminate-reasoning)
- [Vendor declarations](#verified-solver-declarations-and-native-assignment)

Use material data to define the constitutive model actually required by the
load path. Preserve test temperature, heat treatment, orientation, strain/rate
range, units and source identity. A material name alone does not select a valid
curve or prove an allowable. Reconcile the effective solver property with the
intended physical state before interpreting stiffness or stress.

## Isotropic elasticity and thermal compatibility

For small-strain isotropic elasticity, enforce `E=2G(1+nu)` and positive bulk
and shear stiffness. In this package's compressible elastic calculations,
`E>0` and `-1<nu<0.5`. Do not make an incompressible problem artificially valid
by replacing nu=0.5 with an arbitrary nearby number; choose an appropriate
formulation and verify volumetric locking.

Use the [joint method](../../fea-connector-contact/references/engineering-method.md) for axial and tangential compliance. Establish the effective areas and lengths from the load path. Check whether head bearing, flange bending, member contact or gasket compliance controls.

Thermal strain depends on the stress-free temperature and the material coefficient over the actual interval. Integrate an instantaneous expansion coefficient with temperature before computing free extension. Apply the relevant bolt and member compliance and contact state to evaluate any preload change. Include permanent settlement or inelastic strain when supported by the load history.

## Tangent, secant and path dependence

For nonlinear uniaxial behavior, secant modulus is `sigma/epsilon`, whereas
tangent modulus is the local derivative `d(sigma)/d(epsilon)`. They answer
different questions. A secant approximation may match one total displacement
but give the wrong incremental stiffness, stability or modal linearization.
Use a consistent tangent for Newton updates and retain plastic strain/internal
variables across load steps. Unloading generally follows a different branch;
replacing a plastic curve with a low constant E does not reproduce permanent
strain or dissipation.

Compare the effective material at the current temperature and step, including
the reference state used for thermal strain. Obtain the active deck/property
readback rather than assuming the material selected in a library was assigned
to every element. Inspect region ownership, property IDs, thickness, section
orientation, density and units. A wrong density can leave static stiffness
credible while corrupting modal frequencies and inertia loads.

## Tensor conventions are part of the material contract

Separate tensor shear strain `epsilon_xy` from engineering shear
`gamma_xy=2*epsilon_xy`. Constitutive matrices using engineering Voigt strain
must not be multiplied by tensor-shear components without conversion. For
G=5 GPa and gamma_xy=0.002, shear stress is 10 MPa. Treating 0.002 as tensor
epsilon_xy instead doubles the predicted stress to 20 MPa: a clean-looking
contour can be wrong by two.

Keep stress/strain type, frame, recovery location and shell side/ply identity
with every tensor. The existing tensor kernel handles supported real tensor
semantics and engineering-shear conversion; it deliberately does not infer
ply failure from an averaged global stress. Use the
[tensor method](../../fea-results-interpretation/references/real-tensor-qoi.md)
before rotating or enveloping results.

## Orthotropy and laminate reasoning

For an orthotropic lamina, reciprocity gives
`nu21=nu12*E2/E1`. In plane stress, use positive E1/E2/G12 and a positive
`1-nu12*nu21`. Rotate the reduced stiffness into the element material axes,
then integrate through the actual ordered thickness coordinates:

```text
A = sum(Qbar_k*(z_k-z_(k-1)))
B = 1/2 sum(Qbar_k*(z_k^2-z_(k-1)^2))
D = 1/3 sum(Qbar_k*(z_k^3-z_(k-1)^3))
```

A, B and D have units N/m, N and N·m. A symmetric layup about the chosen
midplane has B=0; a balanced layup does not automatically remove every
bending/twisting coupling. Include thermal membrane forces and moments when
the expansion coefficients or temperature vary through thickness.

A two-ply `[0/90]` laminate, each ply 0.125 mm, with E1=135 GPa, E2=10 GPa,
nu12=0.3 and G12=5 GPa has A11=A22≈18.2466 MN/m. Yet B11≈-983.117 N and
B22≈+983.117 N for bottom0/top90 ordering. Reversing the stack leaves A
unchanged but reverses B. Thus equal thickness, ply counts and membrane
stiffness do not establish the same curvature or thermal response. This is
a hand-checkable laminate reference, not a claim that the package implements
a general laminate solver or ply-failure engine.

## Verified solver declarations and native assignment

Fetched Simcenter Nastran 2606 QRG pages, SKU `PL20251024315120185`, provide:

- `QRG.id508391` — MAT1: E/G/nu, mass density and expansion/reference
  temperature; SOL401 derives G from E/nu when all three are supplied.
- `QRG.id508516` — MAT8: orthotropic axes, reciprocity, shear properties and
  direction-specific allowables. Define shear data explicitly when it matters.
- `QRG.id508666` — PCOMP: ordered plies, thickness, angle, output and reference
  plane. A smeared representation cannot recover the same ply stresses as
  actual layered recovery; offsets affect result and contact interpretation.

Record material evidence hashes and statuses. Use exact-release Siemens Help and API discovery
for any actual assignment owner/factory and lifecycle. If no material-assignment
builder is verified and admitted, retain that exact capability gap; do not
invent a setter or silently mutate a shared material. Read back the effective
assignment and property, then falsify it with units, mass, stiffness, thermal
and orientation checks. Native assignment and engineering acceptance remain
separate from these source computations.
