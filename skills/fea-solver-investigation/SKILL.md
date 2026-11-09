---
name: fea-solver-investigation
description: "Investigate FEM/SIM hierarchies, effective Nastran decks, solver logs and physical result states together. Use for stale mesh selections, wrong subcases, missing load paths or apparently valid results that contradict independent mechanics."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Solver investigation

Resolve the engineering question from the actual model and result artifacts.
Trace CAD/idealized-part/FEM/SIM ownership, exclusive component elements,
selected supports and loads, effective solver sequence and physical result state.
The source export is evidence to reconcile, not authenticated native readback.

## Technical resources

- [Engineering method, artifact contract, falsifiers and repair](references/engineering-method.md).
- [Random response](../fea-random-response/references/engineering-method.md) for stationary correlated forcing after a valid linear operating state is established.
- Siemens solution/export/result operations (source: fea_expert_agent_plugin/docs/engineering/vendor-api-next.md) for exact 2606 factories, lifecycle and readback.
- Runtime handoff (source: fea_expert_agent_plugin/docs/architecture/runtime-fea-handoff.md) for the actual transport and missing native handlers.

```sh
python -m fea_agent run-case examples/solver_linked/captured/gantry_case.json
python -m fea_agent run-case examples/solver_linked/captured/wrong_support_case.json
python -m fea_agent read-f06 /path/to/original-output.f06
```

The first case joins real OpenSees output with a manufactured source FEM/SIM
hierarchy and a flexible gantry deck. The second preserves total force and
moment but corrupts the local support reactions. Explain the compatibility
and nodal-equilibrium evidence, then propose a correction with a discriminating
rerun/readback. A checksum match or end-of-job banner is insufficient.

## Source solid and artifact investigation

The source MCP exposes `fea_investigate`, authentic artifact inspection and
independent solid computations. Inspect the full imported deck first, then
call `fea_prepare_continuum_from_bdf` with explicit length/force/mass factors,
a unit-basis statement and selected subcase. Pass its reusable request to
`fea_solve_continuum` only after the closed SOL101 MAT1/PSOLID tet4/hex8
admission passes. Preserve inherited loads/SPCs. Compare mapped displacement
and support-reaction fields with original OP2 bytes; never infer historical
units from material magnitudes or omit unsupported cards to get agreement.
Archived comparison does not authenticate the old solver run. See
solid and thermal methods (source: fea_expert_agent_plugin/docs/engineering/multiphysics-v3.md) and
artifact reconciliation (source: fea_expert_agent_plugin/docs/engineering/artifacts-v3.md).

## Completion

Return the engineering decision, quantitative discrepancies, competing physical
causes, smallest discriminating correction and remaining evidence gap. Preserve
imported-source, reproduced open-solver, documented API, stub compile, installed
SDK, native writer and engineering acceptance as separate observations. For
physics outside the implemented frame, select the appropriate model and state
why its discriminating verification changes; do not remove unsupported cards
merely to make a calculation run.
