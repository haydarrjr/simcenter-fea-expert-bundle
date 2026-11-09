---
name: fea-thermal
description: "Reason about heat balance, temperature mapping, stress-free references and thermo-structural restraint. Use for differential expansion, temperature-sequenced joints and mounts; imported temperature fields are not automatically validated heat-transfer solutions."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Thermal

Distinguish absolute temperature, temperature change, initial condition and thermal strain. Preserve load-step history and effective properties. Use the joint and mounted-assembly calculations for constant-property reduced models; identify missing heat-field or nonlinear correlation explicitly.

## Engineering method and resources

- [Thermal and restraint method](references/engineering-method.md).
- Bolt thermal history (source: fea_expert_agent_plugin/docs/engineering/bolted-joint-workflow.md).
- Native load-step binding (source: fea_expert_agent_plugin/docs/engineering/vendor-api-workflows.md).

## Executable starting point

```sh
python -m fea_agent assess-assembly examples/engineering_v2/mounted_assembly_model.json
```

At 100 K temperature change, M1 axial reaction reverses from +206.174 N to -9.905 N while global equilibrium remains accurate. A compression-only mount would require a changed active set.

## Source heat-field and stress workflow

For spatial conduction or a thermal history, compose with `fea-continuum-thermomechanics`
and call `fea_solve_continuum` using the `bimaterial_history` request from
`fea_get_example`. Preserve absolute Kelvin, previous thermal state, load
replacement versus inheritance, and the stress-free reference separately.
Compute heat input, storage and boundary heat reaction before transferring the
field to mechanics. Small algebraic residual does not establish a physical
thermal field: source-free temperatures must respect the previous/boundary
extrema, and negative Kelvin is rejected even with sources. Compare total,
elastic and thermal strains; fully restrained heating has zero total strain
without having zero stress or small elastic strain.

Read the full continuum/heat method (source: fea_expert_agent_plugin/docs/engineering/multiphysics-v3.md)
and its primary-source ledger (source: fea_expert_agent_plugin/docs/evidence/physics-v3-source-method-ledger.json).
Capacity lumping is an explicit discretization choice, not an arbitrary-mesh
monotonicity guarantee. Mechanical transient inertia, radiation, phase change
and temperature-dependent properties are outside this source solver.

## Completion boundary

Return the calculated or evidence-backed decision, its physical assumptions, the strongest falsifier exercised, and the specific unresolved dependency. Use qualified Engineering Desktop Runtime capabilities for native effects; this skill and source calculations do not create host authority. Preserve separate source, native, solver and engineering outcomes.
