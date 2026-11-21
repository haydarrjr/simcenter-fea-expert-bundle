# Mesh decisions from geometry, approximation error and the target QoI

## Contents

1. Separate geometry validity from solution accuracy
2. Mesh design and constitutive regime
3. Computable verification
4. Worked falsifiers
5. Documented builder lifecycle

## Separate geometry validity from solution accuracy

A mesh can have positive Jacobians and still give the wrong engineering answer.
First establish the representation, material regime, load introduction and QoI.
Then test element geometry, connectivity and physical region membership. Finally
test convergence of the relevant response. These are distinct questions; passing
one cannot fill missing evidence for another.

For a linear tetrahedron with edge matrix J, signed volume is `det(J)/6`.
The sign detects inversion only relative to the expected node ordering; the
magnitude and normalized shape measures detect collapse. A triangle's area is
half the magnitude of the cross product of two edges. Evaluate characteristic
length from geometry, not a label such as fine/coarse. Duplicate nodes with
different labels are not automatically connected; a welded geometry can still
produce disconnected finite-element load paths.

For independent TRI3/TET4 geometry checks inspect duplicate IDs,
coincident positions, element/node incidence and orphan connectivity. It does
not infer higher-order Jacobians, warped shell behavior or solver-specific
integration quality from corner coordinates. See [TRI3/TET4 mechanics](tri3-tet4.md).

## Mesh design and constitutive regime

Use beams or shells only when their kinematics preserve the intended bending,
shear and connection behavior. For nearly incompressible material, a displacement
formulation can lock; mesh refinement alone is not evidence the formulation is
appropriate. For bending, distinguish interpolation order and through-thickness
resolution from an attractive surface mesh. Contact needs sufficient resolution
of pressure variation and the changing active region, with consistent master/
slave or symmetric treatment according to the documented solver formulation.

Refine where the QoI is sensitive. Resolve contact edges, load patches, material
interfaces, curvature and stress gradients. An idealized point load or re-entrant
corner can have a nonconvergent stress peak even when displacement and strain
energy converge. Report a defined path, area average, structural stress or
finite-radius model instead of declaring a divergent nodal maximum accurate.

## Computable verification

Use Model Inspection and measured QoI changes across independently recorded meshes.
The convergence evaluator compares the top-level physical identity with every
mesh level before numerical conversion. A model A request containing only model
B levels is rejected even if those levels agree with one another.

For constant refinement ratio r and an asymptotic scalar error `C h^p`,
estimate p from successive differences, extrapolate q to zero h, and apply a
declared safety factor to the extrapolation error. The implementation rejects
unsupported signs/trends, identity drift and unrepresentable quantities rather
than forcing a positive convergence order. Read the detailed method in the
[VVUQ refinement reference](../../fea-vvuq-review/references/constant-r-refinement.md).
Do not use the asymptotic estimate as a general error bound outside its regime.

Coincidence checking uses coordinate buckets at zero tolerance and bounded
spatial search at positive tolerance. For dense data the limits are 1,000,000
candidate comparisons and 20,000 returned pairs. Completeness is reported;
an exhausted search cannot establish PASS. Its boundary comparison uses the
actual Euclidean distance, including inclusive floating-point edge cases.

## Worked falsifiers

The three-level manufactured law `q(h)=5+2 h^3`, at h = 1, 1/2, 1/4,
has values 7, 5.25, 5.03125. The evaluator recovers p = 3 and q-infinity = 5.
Fine-level error is 1/32; a 1.25 factor yields an absolute estimate 5/128.
Changing every level to a different model identity must stop this otherwise
perfect numerical fit. The source tests exercise precisely that failure.

Use a reproducible mesh and report distance tolerance in model units, the candidate pair count and the reviewed connectivity effects.

For an eight-bolt flange, converged total reaction is a weak mesh acceptance
metric: equilibrium can hold while the opening sector and maximum bolt force
change materially. Compare contact extent, force distribution and relevant
pressure averages across meshes with the same geometry, contact law, load step
and physical selection. Keep nonconvergent edge peaks separate from those QoIs.

## Documented builder lifecycle

The .NET 2606 tetra recipe verifies the MeshManager factory and builder members
from canonical Siemens pages. Configuration is not the end of the workflow:
validate the supplied owner and properties, commit, inspect returned meshes,
destroy the builder and obtain independent model/update/quality readback. A
partial-mesh commit or automatic element-size adjustment cannot be labeled a
successful requested mesh without evaluating the changed result. Automatic
reset may remove manual edits, so preserve the explicit effect and recovery plan.

Verify the tetra builder lifecycle through installed API discovery and exact-release Siemens Help.
Compilation and a contract double exercise prove source behavior. Actual
geometry selection, licensed SDK execution and mesh readback still require
qualified Runtime capabilities.
