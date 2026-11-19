---
name: fea-solver-investigation
description: "Export and verify Simcenter Nastran solution decks, run Siemens batch analyses, and post-process compatible SCD5 with BatchPost. Investigate solver logs, reactions, energy, warnings and archived result consistency."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Solver investigation

Bind the FEM/SIM, solution, subcase, effective deck, F06 and result database to the same run before joining their facts. Use [tool routing](../fea-sc3d-tool-routing/SKILL.md) and [artifact forensics](../fea-artifact-forensics/SKILL.md).

For setup, batch submission, SCD5 and BatchPost, follow [Solution Sequence](references/solution-sequence.md).

- Inspect actual element/property/material mappings, INCLUDEs, SPC/MPC selection and expanded loads. Distinguish part-wide boundary objects from effective subcase assignments.
- Review solver completion, warnings/fatals, AUTOSPC and conditioning. Check applied and reaction force/moment in the same frame and about the same point. Verify units, directional results and energy only where dependency and sign conventions are established.
- Use [BatchPost](../batchpost-actions/SKILL.md) for archived result data and traceable figures. For nonlinear cases inspect the actual load step and converged increments; inspect residuals, contact/constitutive status and step retry history.
- Use the [engineering method](references/engineering-method.md) for state reconciliation, load mapping and independent checks. Document missing evidence and preserve the strongest physical falsifier. Native setup and solve have separate capability gates. Look up the relevant release through Siemens Help Server.
