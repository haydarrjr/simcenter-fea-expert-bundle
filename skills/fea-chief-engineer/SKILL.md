---
name: fea-chief-engineer
description: "Lead coupled FEA investigations from physical evidence, choose modeling and verification methods, and execute multi-artifact engineering cases. Use for whole-analysis decisions spanning solver-linked artifacts, contacts, nonlinear history, assembly dynamics, random response and acceptance."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Chief Engineer

Start from the requested physical decision and inspect its evidence. Run the case runner when compatible artifacts exist; acquire missing source or qualified Runtime observations before asking the caller to supply facts that tools can obtain. Use the calculations to decide whether the current model can answer the question.

## Choose the engineering path

- Begin tool discovery with `fea_capabilities`; use `fea_get_example` to obtain
  complete request contracts, then replace their assumptions with inspected
  evidence. The bounded source MCP can execute computations and read supplied
  files; it never submits native work or confers engineering acceptance.
- For an imported STEP/IGES/BREP assembly, begin with
  [Model preparation](../fea-model-preparation/SKILL.md), establish body/face
  ownership and connection intent, then choose a solver. Use
  [Multistep nonlinear](../fea-multistep-nonlinear/SKILL.md) for actual external
  CalculiX contact/plastic/thermal/pretension histories. External execution
  requires the configured effectful capability and exact prepared-input hash.
  Keep the complete force/moment, contact, mesh and step findings even when
  the process exits successfully.
- For a transient stress or life question, use
  [Dynamics](../fea-dynamics/SKILL.md) and [Durability](../fea-durability/SKILL.md).
  Verify signed histories and time resolution before counting reversals. Use
  the open workflow contract (source: fea_expert_agent_plugin/docs/engineering/source-tools-v4.md) to
  carry the actual solver/model/state evidence into result interpretation.
- For original BDF/OP2/OP4/mesh fields, use [Artifact forensics](../fea-artifact-forensics/SKILL.md).
  A recognized file or matching value is insufficient without physical state,
  unit/frame and element/node/ply identity.
- For actual solid models and temperature histories, use
  [Continuum thermomechanics](../fea-continuum-thermomechanics/SKILL.md). Apply
  energy/heat and physical-temperature checks before using a computed stress.
- For laminate coupling, use [Composite laminates](../fea-composite-laminates/SKILL.md);
  for repeated-mode equivalence use [Modal correlation](../fea-modal-correlation/SKILL.md).
  For a qualified primitive-based geometry/mesh/load pipeline use
  [Open meshing](../fea-open-meshing/SKILL.md).

- For FEM/SIM hierarchy, effective deck, solver log or state-specific result claims, use [Solver investigation](../fea-solver-investigation/SKILL.md). Reconcile ownership, supports, loads and the physical result state, then exercise compatibility and local equilibrium checks before accepting a response.
- For stationary correlated excitation and RMS/covariance, use [Random response](../fea-random-response/SKILL.md). Establish a valid linear operating state first; retain spatial load patterns and the full complex spectral matrix. Reject inadmissible spectra; if the response changes contact state, reassess the operating model before using RMS for acceptance.
- Keep preload/contact and nonlinear-history questions with their existing specialist methods; combine them with [Dynamics](../fea-dynamics/SKILL.md) when the operating tangent or response regime changes. Route gyroscopic, cyclic and other coupled dynamics through its explicit specialist methods and implementation limits.

## Engineering method and resources

- [Complete engineering method](references/engineering-method.md).
- [Solver-linked artifact method and discriminating repairs](../fea-solver-investigation/references/engineering-method.md).
- [Stationary random-response equations, validation and output scope](../fea-random-response/references/engineering-method.md).
- Vendor API implementation (source: fea_expert_agent_plugin/docs/engineering/vendor-api-workflows.md).
- Runtime client contract (source: fea_expert_agent_plugin/docs/architecture/runtime-compatibility.md).

## Executable starting point

```sh
python -m fea_agent run-case examples/engineering_v2/joint_case.json
python -m fea_agent run-case examples/solver_linked/captured/gantry_case.json
```

An eight-bolt thermal/service case changes contact state and exposes a false convergence claim. Explain opening, local slip and the 18 kN balance defect; do not convert the converged label into acceptance.

## Completion boundary

Return the calculated or evidence-backed decision, its physical assumptions, the strongest falsifier exercised, and the specific unresolved dependency. Use qualified Engineering Desktop Runtime capabilities for native effects; this skill and source calculations do not create host authority. Preserve separate source, native, solver and engineering outcomes.
