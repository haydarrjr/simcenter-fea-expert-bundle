# Parametric SOL 101 evidence

1. Record CAD/FEM/SIM revisions, parameters, target regions, all active load and constraint inputs, units, and acceptance quantities.
2. For each parameter change, record expected and observed geometry, semantic selection regions, applied resultants and solution membership. Trace the new deck revision and source analysis. Protect task-owned targets from accidental duplication.
3. Compare the submitted deck, F06 and OP2 by exact job, subcase and content identity. Record solver termination and warnings. Keep strength claims scoped to the stress recovery location and model assumptions.
4. Report separately the observed associative update, saved-and-reopened model, licensed solve, result recovery and engineering comparison. Use [acceptance verification](../../fea-acceptance-verifier/SKILL.md) for scoped status.

## Synthetic benchmarks

For a uniform axial bar, compare tip displacement to `FL/(EA)`, axial stress to `F/A` and the axial support reaction to `-F`. Use an explicit consistent unit system. Choose tolerances based on formulation and expected numerical error.

For a slender prismatic cantilever under a transverse tip force, compare displacement to `FL^3/(3EI)`, rotation to `FL^2/(2EI)`, and reactions to the applied force and moment. Check the beam theory's applicability, element order, shear and extraction region before drawing conclusions from the comparison. Evaluate a local stress away from idealized load and support singularities. These are independently specified tests for the measured quantities.
