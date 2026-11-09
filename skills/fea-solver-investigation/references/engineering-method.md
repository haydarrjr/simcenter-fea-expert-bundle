# Solver-linked engineering investigation

## Contents

1. Evidence graph and physical state
2. Effective deck and flexible mechanics
3. Job/result interpretation and independent checks
4. Discriminating repair
5. Worked gantry and counterexamples
6. Siemens and Runtime operation boundary

## Evidence graph and physical state

A solver result belongs to a particular **submitted model**, boundary/load
selection and physical state. A CAD name, SIM filename or last-modified date
does not identify that state. In the executable investigation, the manifest
binds the bytes of the effective deck, source-exported FEM/SIM hierarchy, job
sidecar, log and every result file before any calculation occurs. The common
identity contains model, revision, mesh revision, basic frame and coherent
units. The selected solution, subcase and static load factor are separate.

The hierarchy links SIM → FEM → idealized part → CAD part, with a component
parent graph and exclusive structural/mass-element ownership. Shared GRID
nodes are legitimate interfaces; double-counting an element as owned by both
an assembly and its child is not. The importer checks missing owners, cycles,
duplicate IDs and deck membership. Physical support and load regions carry
their own mesh revisions. A remesh may reuse numeric tags, so matching old
GRID numbers does not clear a stale region.

`fea.solver-investigation.v1` artifacts use relative paths and SHA-256. The
reader rejects traversal, symlinks, changing files, nonfinite JSON, duplicate
JSON fields and unmatched hashes. These measures protect interpretation of
the supplied bytes. **They do not authenticate their origin.** A manufactured
result can be rehashed correctly; the independent physics checks must still
find it wrong. Job metadata, a log marker or a caller-supplied grant never
creates native authority.

Use `python -m fea_agent investigate <manifest.json>` or the common `run-case`
entrypoint. The captured gantry directory is a complete, portable worked
bundle; its job, hierarchy, manifest and comparison tolerances show the exact
typed contract. The source hierarchy is manufactured to match the source
deck; it is not an NX export. The recorded OpenSees outputs were executed
independently, while the importer retains their unauthenticated-source status.

## Effective deck and flexible mechanics

The implemented profile interprets complete SOL101/SOL103 decks containing
GRID, MAT1, CBAR, PBAR, CONM2, FORCE, MOMENT, LOAD, SPC/SPC1/SPCADD and EIGRL
within its stated field restrictions. It resolves global/local Case Control
selection and all referenced sets. Solver output commands do not substitute
for a selected stiffness/load model. Unsupported offsets, releases, coordinate
systems, contact, prestress, INCLUDEs and arbitrary cards stop the affected
reference computation with a specific reason. Obtain the flattened effective
deck and select a justified model rather than silently dropping those cards.

Basic coordinates and SI N–m–kg or coherent N–mm–tonne are supported. In the
latter system, E is N/mm², density tonne/mm³, and rotational inertia
tonne·mm². A force spectrum expressed against a dimensional load pattern is a
spectrum of the **pattern multiplier**. Treat a force direction, a geometry
vector, an axial rotational DOF and a translational DOF differently under
unit or frame changes.

Siemens 2606 free-field documentation states that overlong real fields can be
rounded. The parser rejects free fields longer than eight characters instead
of guessing the solver's rounding algorithm. Use fixed large fields when
precision matters. Integer CBAR X1 denotes an orientation GRID (G0); this
profile requires an explicit floating-point orientation vector. PBAR K1/K2
blank or zero selects the documented Euler–Bernoulli limit; a nonzero shear
factor requires another formulation. See the source ledger in
`docs/evidence/siemens-2606-solver-linked.json` for exact release/card evidence.

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
the polar mass second moment; the circular-tube reference makes them equal.

Solve `K φ = λ M φ` by a mass-Cholesky transformation and a symmetric
eigensolver, then mass-normalize the basis. A stiffness mechanism, invalid
mass, ill-conditioned operator or physically incompatible interpretation is
an engineering finding. The normal-stress recovery at a PBAR point is
`σ = N/A + My z/Iy - Mz y/Iz`; it is not a full shear/torsional equivalent
stress, notch stress or weld/bolt capacity.

## Job/result interpretation and independent checks

The F06 reader consumes real formatted displacement, applied-load, SPC-force,
eigenvalue and eigenvector tables. It retains source line numbers, explicit
subcase and static/time/frequency/mode state. Missing subcase context remains
missing. Header order, a single end-of-job marker and printed numbers cannot
prove complete solver success or imply units. Fatal evidence from a separately
bound console log overrides an apparently complete result table.

The OpenSees reader consumes actual Node recorder whitespace rows. The job
sidecar explicitly supplies node order, quantity, units and time. It checks
every row, rejects duplicate/reversed states and selects the **exact requested
time**, never the last available row. This is not an F06 dialect or a claim
that a licensed Siemens solver executed the source deck.

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
study; this frame's nodal normal stresses are insufficient for that decision.

If the intended structure is pretensioned and frictional, obtain its current
equilibrated operating state, contact active set and tangent. Establish whether
a linear perturbation preserves those states. Otherwise choose nonlinear
response or another suitable model. The correct action can be to reject the
apparent random-response solver while still identifying the discriminating
measurement or computation needed next.

## Worked gantry and counterexamples

The gantry has two flexible columns, a cross tube, an eccentric sensor arm,
two concentrated bodies and 36 free DOFs. Its tube/body mass is about 72.125 kg.
The static benchmark applies the **47 kg payload weight only**, 461.07 N;
tube self-weight is deliberately absent. It therefore cannot be described as
the complete gravity loading of the 72.125 kg assembly.

An independently constructed OpenSees model uses circular-tube areas/inertias,
consistent beam mass and separate geometric transforms. Actual solver recorders
and eigenvectors are compared against the deck-based implementation. Its first
mode is about 7.915 Hz. Sensor displacement under payload weight is about
0.804 mm in Y and −2.344 mm in Z. The typed output provides all reactions,
element-end actions, recovered normal stresses and the complete modal basis.

`wrong_support_case.json` adds +350 N and −350 N along the line connecting
the feet. Net force and moment remain unchanged. Local equilibrium and support
distribution must reject it. `stale_mesh_case.json` retains plausible numeric
GRID IDs but carries an old region mesh revision. `wrong_subcase_case.json`
tries to use payload-weight results for a lateral-load subcase. The contact
variant asks the same linear model to represent a pretensioned frictional
operating structure; random response is withheld and a physical-state repair
is required. These variants are explicitly manufactured falsifiers.

## Siemens and Runtime operation boundary

The verified 2606 source paths are composed from borrowed simulation/part/BC
objects and observed installation descriptors. Solution creation uses the
documented factory, explicitly attaches steps and BCs, and checks returned
membership. Export creates and disposes its owned options container, verifies
typed option readback, and requires actual exported-deck digest/readback.
Borrowed result access is bound to the selected solution, subcase, quantity,
location, components, frame, units and physical state. Source helper generation
does not prove handle acquisition, installed descriptors or a completed write.

Runtime discovery and job inspection use the observed upstream DTOs. A job
labelled COMPLETED with unknown outcome remains unresolved. The six-stage FEA
handoff binds the case, owner graph, effective deck, physical state and optional
recipe digests; it is **not dispatchable** while qualified CAE handlers are
absent. A timeout or uncertain commit requires exact-job reconciliation,
not a fresh request that might repeat the native effect.
