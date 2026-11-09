---
name: fea-acceptance-verifier
description: "Evaluate engineering claims against independent physical checks, exact source state and authenticated native evidence. Use for acceptance decisions and engineering reports, including rejecting apparently converged cases; source CI never establishes licensed-host or engineering qualification."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Acceptance Verifier

Reconcile model, revision, mesh, loadcase, step, frame and source before comparing results. Read the actual residuals, balance, energy, contact and QoI evidence. Separate computed contradictions, inferred hypotheses and missing host proof; refuse a report that hides an unresolved failed check.

## Engineering method and resources

- [Acceptance decision method](references/engineering-method.md).
- Nonlinear source diagnosis (source: fea_expert_agent_plugin/docs/engineering/nonlinear-diagnosis.md).
- Runtime receipt trust (source: fea_expert_agent_plugin/docs/architecture/runtime-compatibility.md).

## Executable starting point

```sh
python -m fea_agent run-case examples/engineering_v2/joint_case.json
```

A model can satisfy a global equilibrium column yet fail contact convergence, 11.25% force balance, 12% artificial energy and the required final loadfactor. The claimed accepted state is rejected.

## Independent 3.0 falsification

Separate original artifact readability, source mathematical solution,
independently executed open solver, archived result comparison, documented
vendor API, source-double compilation, installed SDK and native operation.
Exercise changed phase/state/ply/connectivity and mapped DOFs, not checksums
alone. A fully restrained model can hide large elastic strain behind zero
total strain; a tiny residual can accompany negative Kelvin or impossible
heat overshoot. The independent challenges (source: fea_expert_agent_plugin/docs/evaluations/independent-challenges-v3.md)
retain these counterexamples. Real SDK clients exercise the MCP server from an
extracted package; installed host activation remains separate. NASA-STD-7009B
and current NASA-HDBK-7009B are referenced in the
source ledger (source: fea_expert_agent_plugin/docs/evidence/source-tools-v3-source-method-ledger.json).
These checks do not establish standard compliance, an experiment, a licensed
job or design acceptance.

## Completion boundary

Return the calculated or evidence-backed decision, its physical assumptions, the strongest falsifier exercised, and the specific unresolved dependency. Use qualified Engineering Desktop Runtime capabilities for native effects; this skill and source calculations do not create host authority. Preserve separate source, native, solver and engineering outcomes.
