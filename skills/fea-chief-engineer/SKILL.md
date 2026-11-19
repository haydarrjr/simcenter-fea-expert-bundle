---
name: fea-chief-engineer
description: "Lead coupled FEA investigations from physical evidence, choose modeling and verification methods, and execute multi-artifact engineering cases. Use for whole-analysis decisions spanning solver-linked artifacts, contacts, nonlinear history, assembly dynamics, random response and acceptance."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Chief Engineer

Start with the requested physical decision. Select the needed global Siemens MCP through [tool routing](../fea-sc3d-tool-routing/SKILL.md). For CAD or NXOpen in Designcenter, connect directly to Designcenter Open. Check Simcenter 3D Model Inspection only when the task needs FEM/SIM inspection. For a model read, bind available session, work and display part, release, ownership, revision and dirty-state evidence. Open the explicitly identified result file through BatchPost before listing or exporting. Use [artifact forensics](../fea-artifact-forensics/SKILL.md) for deck/F06 lineage and evidence gaps.

- For model idealization, materials, connectors and mesh, use [model preparation](../fea-model-preparation/SKILL.md), [materials](../fea-materials-properties/SKILL.md), [connectors](../fea-connector-contact/SKILL.md) and [mesh quality](../fea-mesh-quality/SKILL.md). Keep material assignment, coordinate frames, BC scope, mesh quality and QoI convergence separate.
- For static or nonlinear solver evidence, use [solver investigation](../fea-solver-investigation/SKILL.md) and [multistep nonlinear](../fea-multistep-nonlinear/SKILL.md). Check effective constraints, force and moment balance, contact state and energy on the actual subcase.
- For authorized solver jobs, use [Solution Sequence](../fea-solver-investigation/references/solution-sequence.md) for deck export, Siemens batch submission, SCD5 and BatchPost. For SOL 103, apply the [free-free workflow](../fea-dynamics/references/sol103-free-free.md). Qualify live setup and deck export through the [runtime gate](../fea-native-runtime-gate/SKILL.md). The user saves the SIM/FEM.
- Use [continuum thermomechanics](../fea-continuum-thermomechanics/SKILL.md) for heat and mechanical coupling, [composite laminates](../fea-composite-laminates/SKILL.md) for ply evidence, [random response](../fea-random-response/SKILL.md) for correlated spectra, and [durability](../fea-durability/SKILL.md) for signed histories. Preserve assumptions, state, tensor conventions, provenance and validation scope.

Use the [engineering method](references/engineering-method.md), [acceptance verifier](../fea-acceptance-verifier/SKILL.md) and [report method](../fea-results-interpretation/references/engineering-report.md). Follow the tool routing even when a task names a tool absent from the installed catalog. Report native, archived, derived and engineering acceptance states independently.
