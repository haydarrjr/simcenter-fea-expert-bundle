---
name: fea-multistep-nonlinear
description: "Build and scrutinize real 3D nonlinear histories with a separately configured CalculiX solver, or diagnose Siemens histories from effective deck and bound evidence. Use for preload locking, contact/friction, plastic and thermal state transfer, apparent convergence, discretization studies and SOL106 versus SOL401/402; preserve engine-specific semantics."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Multistep Nonlinear

For an actual source-side analysis, use the typed external solver workflow and its explicit effectful execution operation. For imported Siemens evidence, choose the solver family from the effective executive statement and resolve exact case-control semantics. Keep raw F06 observations distinct from a normalized diagnostic trace. The diagnosis operation itself never launches a solver.

## Engineering method and resources

- [Nonlinear decision method](references/engineering-method.md).
- [Real external solver and physical scrutiny](references/open-solver-workflows.md): read for model construction, actual CalculiX execution, FRD/DAT interpretation, independent references and load-path near misses.
- Parser and diagnostic details (source: fea_expert_agent_plugin/docs/engineering/nonlinear-diagnosis.md).
- Documented API lifecycle (source: fea_expert_agent_plugin/docs/engineering/vendor-api-workflows.md).

## Executable starting point

```sh
python -m fea_agent diagnose-nonlinear examples/engineering_v2/nonlinear_false_convergence.json
```

EQU=y with CON=n, 0.04 force error against 0.001, 18 kN imbalance, 12% artificial energy and load factor 0.8 cannot support the claimed completed loadcase.

## Completion boundary

Return the calculated or evidence-backed decision, its physical assumptions, the strongest falsifier exercised, and the specific unresolved dependency. Use qualified Engineering Desktop Runtime capabilities for native effects; this skill and source calculations do not create host authority. Preserve separate source, native, solver and engineering outcomes.
