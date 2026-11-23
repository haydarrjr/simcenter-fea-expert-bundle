# Read a physical result state, then calculate the engineering quantity

## Contents

1. Result identity and recovery semantics
2. Tensor invariants and representability
3. Modal and buckling interpretation
4. Numerical sensitivity and convergence
5. Readback and debugging

## Result identity and recovery semantics

Identify model/revision, solver family and release, solution/subcase, step or
iteration, physical state, coordinate frame, units and recovery location before
interpreting a number. An entity label is not necessarily a result-array index.
Element-nodal values require the parent element; two adjacent elements can
report different values at the same node. Shell TOP/BOTTOM, integration point,
centroid and corner are different locations. Never average across a material
interface, contact discontinuity or incompatible result state without a justified
physical operation.

The vendor result decoder preserves raw components, labels, parent elements and
units before feeding the tensor calculation. Its result access objects are
borrowed handles, not generic builders to destroy. Verify the current result
type, loadcase/iteration, component mapping and actual array size. Unsupported
beam/ply/complex recovery cannot be made into a solid real tensor by renaming
components.

## Tensor invariants and representability

For a symmetric real stress tensor, let `p=tr(sigma)/3` and `s=sigma-p I`.
Then `J2=s:s/2`, `von Mises=sqrt(3 J2)` and Tresca is the largest principal
stress difference. Units of J2 are stress squared. Use the actual tensor for
each physical state. Combining independently maximized components from different
loadcases creates a fictitious tensor and may over- or understate the true
statewise invariant envelope.

Engineering strain stores twice the tensor shear component. A 6-component
strain vector and a stress vector therefore require different decoding. Rotate
with `T'=R T R^T` using a proper orthonormal matrix and preserve transformation
provenance; rotating a component twice can leave scalar invariants apparently
reasonable while corrupting directional interpretation.

The source implementation centers the tensor before spectral/rotation work and
retains principal spans before adding a large hydrostatic shift. If absolute
principal values cannot be separated by floating-point resolution, report that
fact. If a rotated tensor's necessary small components cannot be reconstructed,
reject it rather than return a false precision result. See the complete
[real-tensor method](real-tensor-qoi.md).

## Modal and buckling interpretation

A real eigenpair needs both equilibrium and normalization checks. A small
matrix-norm residual can conceal an error in a soft coordinate beside a very
stiff one; use the action residual as well. Orthogonality is the raw mass inner
product, with normalized mass correlation reported separately. Repeated modes
need subspace comparison: minimum squared principal correlation and full rank,
not the average of individual-vector MAC values. An incomplete supplied basis
does not establish that an unseen repeated mode was excluded.

The translational SOL 103 reference checker is bounded to 1–12 pure translational DOFs.
The mounted-assembly workflow separately handles mixed translations/rotations
with explicit length scaling. Do not pass rotation coordinates to the
translational contract while labeling them metres.

A SOL105 eigenfactor scales a specified preload state. It is not a nonlinear
collapse load or a universal factor of safety. Preserve the sign convention,
static and buckling subcase identities, support ideal and preload artifact.
Contact-dependent stiffness requires review even if the Euler comparison passes;
a failing comparison remains FAIL. See the
[modal/buckling method](sol103-sol105-quant.md) for equations and exact scope.

## Numerical sensitivity and convergence

When hydrostatic stress dominates, compute invariants from the deviator before
rotation or subtraction of rounded absolute principal values. Verify that a
hydrostatic tensor remains hydrostatic under proper rotation. Report the
resolution limit when the stored components cannot resolve a small deviator.

For soft modes, scale the eigen-equation residual by the applied modal stiffness
and inertia terms. For repeated modes, check all principal correlations and the
rank of the mass-weighted subspace.

Bind nonlinear stresses to the achieved increment. Check equilibrium, contact
and retained preload at that increment before using recovered quantities.

## Readback and debugging

Use the linked tensor and elevated-mode or buckling checks on the actual data.
Use the exact-release Siemens Help API and a qualified read path for
element-nodal extraction. Preserve the actual result position and state.

On disagreement, test units, component/shear convention, frame, location,
parent ownership and step identity before adjusting tolerances. Compare a
known transformation or simple analytical invariant. For a hotspot, define the
QoI and its averaging/extrapolation rule, inspect convergence and distinguish
stress singularity from a finite physical concentration. Never smooth a failed
comparison merely to improve a contour plot or agreement statistic.
