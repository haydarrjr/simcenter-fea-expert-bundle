# Solver-linked engineering investigation

## Contents

1. Evidence graph and physical state
2. Effective deck and flexible mechanics
3. Job/result interpretation and independent checks
4. Discriminating repair
5. Reconcile solver artifacts
6. Siemens and Runtime operation boundary

## Evidence graph and physical state

A solver result belongs to a particular **submitted model**, boundary/load
selection and physical state. A CAD name, SIM filename or last-modified date
does not identify that state. Bind the effective deck, FEM/SIM ownership, job log and result files. Record model revision, mesh revision, frame, units, solution, subcase and actual state.

The hierarchy links SIM → FEM → idealized part → CAD part, with a component
parent graph and exclusive structural/mass-element ownership. Shared GRID
nodes are legitimate interfaces; double-counting an element as owned by both
an assembly and its child is not. Check missing owners, cycles, duplicate IDs and deck membership. Physical support and load regions carry
their own mesh revisions. A remesh may reuse numeric tags, so matching old
GRID numbers does not clear a stale region.

Record exact artifact paths and hashes. Use scoped files and keep provenance from the originating job. Hashes establish byte identity. Independently check run lineage and mechanics.

Use the official Nastran and BatchPost readers or the relevant original solver tables to establish these links.

## Effective deck and flexible mechanics

Resolve global and local Case Control selection and referenced sets from the effective deck. Use [deck and solution checks](../../simcenter-nastran/references/deck-and-solutions.md) for syntax, closures and supported local tooling. The beam reference below applies to linear elastic bending. Assess joint releases, offsets, coordinate transformations, shear, contact and prestress when effective.

Basic coordinates and SI N–m–kg or coherent N–mm–tonne are supported. In the
latter system, E is N/mm², density tonne/mm³, and rotational inertia
tonne·mm². A force spectrum expressed against a dimensional load pattern is a
spectrum of the **pattern multiplier**. Treat a force direction, a geometry
vector, an axial rotational DOF and a translational DOF differently under
unit or frame changes.

Use the documented field width for the installed solver. For a CBAR verify whether its orientation comes from a GRID or an explicit vector. Check PBAR shear factors when comparing to the Euler-Bernoulli limit.

Each node has six DOFs. Each CBAR has axial EA/L, Saint-Venant torsion GJ/L,
and two cubic-Hermite bending operators. For a local bending pair, the nodal
matrix is

\[
K_b={EI\over L^3}
\begin{bmatrix}
12&6L&-12&6L\\6L&4L^2&-6L&2L^2\\
-12&-6L&12&-6L\\6L&2L^2&-6L&4L^2
\end{bmatrix}.
\]

The other plane has the appropriate rotation signs. The element coordinate
triad is orthonormal and right-handed; the congruence transformation preserves
virtual work. Assemble the whole flexible frame, eliminate only selected SPC
DOFs and solve `Kff uf = ff`. Reactions are the constrained rows of `Ku-f`,
not a hand-assigned split of the total load. The consistent mass includes
distributed translational inertia, Hermite bending mass and polar torsional
inertia ρ(I1+I2); bending rotary inertia is omitted. CONM2 inertia must be
positive semidefinite and satisfy principal-inertia triangle inequalities at
its own physical scale. J is a torsional stiffness constant, not generally
the polar mass second moment; they are equal for a circular section.

Solve `K φ = λ M φ` by a mass-Cholesky transformation and a symmetric
eigensolver, then mass-normalize the basis. A stiffness mechanism, invalid
mass, ill-conditioned operator or physically incompatible interpretation is
an engineering finding. The normal-stress recovery at a PBAR point is
`σ = N/A + My z/Iy - Mz y/Iz`; it is not a full shear/torsional equivalent
stress, notch stress or weld/bolt capacity.

## Job/result interpretation and independent checks

Use scoped original F06 tables and qualified readers for displacement,
applied-load, SPC-force, eigenvalue and eigenvector evidence. Retain the
source line numbers, subcase and static/time/frequency/mode state. Check
the exact requested state, recording any missing or duplicate rows.
Check the separately bound job log for fatal evidence even when printed
tables and an end-of-job marker are available.

Apply independent checks in physically meaningful groups:

- **Displacement compatibility:** compare every translation/rotation with the
  independent flexible model using separate m/rad tolerances; check constrained
  components and the assumed small-motion regime.
- **Local equilibrium:** calculate `Ku-f-r` at every DOF. Total force and
  moment are necessary, but a self-equilibrated erroneous pair of support
  reactions can preserve both.
- **Energy:** for the elastic force-controlled state, `U = uᵀKu/2` and
  external work `uᵀf = 2U`. Include imposed displacement/thermal work before
  applying this identity to another model family.
- **Modes:** preserve mode IDs; compare eigenvalues, eigen-equation residuals,
  constraints and mass-weighted subspaces. Eigenvectors have arbitrary sign;
  repeated modes have arbitrary bases. Whiten the observed repeated-mode
  subspace, then use singular values of `Φoᵀ M Φr` instead of requiring
  componentwise equality. Frequencies alone cannot detect swapped shapes.
- **Model form:** a flexible linear welded frame does not model frictional
  contact, pretension history, gyroscopic coupling or large deflection. Good
  algebraic agreement only verifies the chosen reference formulation.

Comparison tolerances are explicit verification inputs with distinct units.
They are not material allowables. Never infer safety, material yield or an
acceptable fatigue life from a small residual or agreement between solvers.

## Discriminating repair

Rank explanations by the evidence each predicts. If total force and moment
balance but local `Ku-f-r` fails at two supports, first examine state selection,
SPC inheritance, result mapping and a self-equilibrated reaction alteration.
Changing Young's modulus cannot generally repair an incompatible reaction
vector while leaving all displacements and the stiffness graph unchanged.

If extra SPCs appear after a remesh, compare the physical region and current
coordinates before deleting restraints. On a proposed model copy, remove only
the unintended constraints, re-export the effective deck, then compare
compliance and mode subspaces. If a local shell/solid region governs stress,
perform a work-conserving global/local transfer and a local discretization
study; use a recovery that resolves the local stress state.

If the intended structure is pretensioned and frictional, obtain its current
equilibrated operating state, contact active set and tangent. Establish whether
a linear perturbation preserves those states. Otherwise choose nonlinear
response or another suitable model. The correct action can be to reject the
apparent random-response solver while still identifying the discriminating
measurement or computation needed next.

## Reconcile solver artifacts

Check that the effective deck defines the claimed model, solution and load scope. Compare response and reactions against the expected load path. If equilibrium and recovery disagree, isolate the first inconsistent mapping or physical assumption before rerunning the job.

## Siemens and Runtime operation boundary

Use the [qualified CAE catalog](../../designcenter-open-journal-authoring/references/cae-2612.md) for matching solution setup and deck export. Use the [runtime gate](../../fea-native-runtime-gate/SKILL.md) to reconcile an uncertain live effect. Use [Solution Sequence](solution-sequence.md) to qualify the effective deck and verify the exact batch job and result files.
