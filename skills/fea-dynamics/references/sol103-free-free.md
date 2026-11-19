# Simcenter Nastran SOL 103 free-free normal modes

## Establish the native path

1. Use the [2612 CAE operation catalog](../../designcenter-open-journal-authoring/references/cae-2612.md) to bind release, backend session, work/display, SIM/FEM, revision, dirty state and original SOL 101. Use an owned copy with traceable backup and dependencies; do not save a dirty original.
2. Use the catalog's setup/readback operations on the qualified build. Only do targeted API discovery for a release or operation gap. Inspect the exported input with [Simcenter Nastran](../../simcenter-nastran/SKILL.md).
3. Qualify solution setup and deck export through the [runtime gate](../../fea-native-runtime-gate/SKILL.md). A batch solve uses a verified deck exported from the current in-session model. The user saves the SIM/FEM.

On the observed 2612 Designcenter Open host, a live read-only journal using
`Parts.BaseWork` and direct iteration of `Simulation.Solutions` read an actual
SIM solution even though the discovery index did not list the CAE classes.
The 2612 live route created a new `SEMODES 103` solution and exported its
deck from the identified in-memory SIM using `WriteSolverInputFile`. The
installed Siemens batch solver ran that deck and produced F06 and OP2.

## Prepare and verify the solution

- Use `SOL103_FREE_FREE`, normal modes, unloaded, undamped and without prestress. Create a separate solution on the owned SIM. Preserve the intended FEM, materials, mass, internal MPC/rigid/connectivity and the original SOL 101.
- The installed 2612 solver language descriptor identifies `NX NASTRAN`,
  `Structural`, and `SEMODES 103`. Verify the accepted runtime identifiers and
  effective deck on the owned copy. If using the count-only Lanczos setting,
  verify that the exported `EIGRL` has the requested `ND` and blank bounds so
  the lowest roots remain eligible. [Siemens Lanczos extraction guidance](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.basic_dynamics/html/id472276?audience=external)
- In this 2612 path, create the `Real Eigenvalue - Lanczos` modeling object
  with language `NX NASTRAN - Structural` and solver `NX NASTRAN`. Set integer
  `ND`. Bind it through the solution's `Lanczos Method` named property table.
  Attach a separate `Structural Output Requests` object and verify
  `DISPLACEMENT(PLOT,REAL) = ALL` in the exported deck for mode shapes.
- Inspect effective case control and bulk data. Verify `SOL 103` and `METHOD` selecting the intended eigensolver entry, commonly `EIGRL` (Lanczos). Include near-zero modes in the extraction, choose compatible range/count settings and request at least 26 candidates where feasible. Confirm the realized output count from the run. Record normalization and units. [Real eigenvalue modeling object](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/id628741?audience=external)
- Exclude effective external SPCs, enforced displacements, static load/prestress sets, accidental grounded MPC paths and artificial springs. Inspect permanent constraints, automatically removed DOFs, connector end ownership, density, nonstructural/concentrated mass and inertia. Confirm one structurally connected body assembly for a six-mode expectation. Keep intentional internal kinematic constraints. Read back the new in-session solution and its effective deck before submission.
- Export the exact deck with `SolveOption.WriteSolverInputFile`. After verifying the deck, submit it to the installed Siemens Nastran executable through [Solution Sequence](../../fea-solver-investigation/references/solution-sequence.md). Capture the solver release, job identity, completion status, submitted deck, F06, OP2 and qualified SCD5 linked to the in-session setup. Inspect F06 warnings and singularity diagnostics.

## Verify the modes

- Read the actual signed eigenvalues and frequencies from the eigenvalue summary. For positive eigenvalues, check the conversion to cycles per consistent time unit using sqrt(lambda)/(2 pi). Preserve the sign of negative eigenvalues and investigate material negative values rather than converting them to positive frequencies.
- A connected nondegenerate 3D structure without mechanisms has six independent rigid motions. Classify candidate near-zero modes with a declared solver/model-scaled tolerance, using `sqrt(abs(lambda))/(2*pi)` for classification only. Join labeled XYZ vectors to GRID coordinates in one frame. Form translations and `axis x (x - centroid)` rotations, scale columns, and use QR/SVD to check rank and quantify the measured subspace residual. Centroid translation changes the basis, not the span; an unweighted geometric check is not mass orthogonality. Extra, missing or significantly shifted modes trigger a grounding, connectivity, mechanism or mass investigation. [Siemens rigid-body mode guidance](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.basic_dynamics/html/id472466?audience=external)
- Use the first approximately 20 verified flexible modes if available. Report mode, frequency, deformation characterization and normalization. Check residual, mass orthogonality or participation only when the required matrices/vectors and the correct metric are available. Treat close/repeated modes as a subspace. Mode shape amplitudes are normalized, and resonance requires excitation evidence.
- Open the exact verified modal SCD5 in [BatchPost](../../batchpost-actions/SKILL.md). In the observed 2612 conversion, SCD5 exposed frequency and iteration index in extraction order. Reconcile both against the F06 root table before labeling the modes. Use the original OP2 through BatchPost for required metadata or fields unavailable in SCD5. Export genuine views with consistent camera, units, scale and normalization captions. Retain spectra, shapes and verification as independent evidence.
