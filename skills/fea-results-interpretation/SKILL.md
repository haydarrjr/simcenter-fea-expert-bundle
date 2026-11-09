---
name: fea-results-interpretation
description: "Interpret identity-bound FEA results, recovery locations, tensors, modal subspaces and eigen-buckling references. Use for component decoding, principal/von-Mises/Tresca quantities, frame changes and coherent envelopes; unsupported complex or averaged fields stay explicit."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Results Interpretation

Read labels through the result-index mapping and retain parent elements for element-nodal values. Evaluate tensors and envelopes within coherent states. Distinguish solver convergence, numerical result validity and engineering acceptance; use the actual residual and force/energy evidence.

## Engineering method and resources

- [Result reasoning method](references/engineering-method.md).
- [Real tensor implementation](references/real-tensor-qoi.md).
- [Modal and buckling reference](references/sol103-sol105-quant.md).
- Verified extraction API (source: fea_expert_agent_plugin/docs/engineering/vendor-api-workflows.md).
- Complete field histories and physical tensor interchange (source: fea_expert_agent_plugin/docs/engineering/source-tools-v4.md).
- Super-iteration readback and restoration (source: fea_expert_agent_plugin/docs/engineering/vendor-readback-v4.md).

## Executable starting point

```sh
python -m fea_agent assess-tensor examples/tensor_uniaxial_v1.json
```

A 1 Pa shear atop 1e16 Pa hydrostatic stress has Tresca 2 Pa. A soft modal error beside a 1e20 stiffness is rejected by action residual 1/3 even when a matrix-norm residual looks excellent.

## Read authentic results before interpreting them

Use `fea_inspect_artifact` with `fea-artifact-forensics` to inspect OP2, OP4,
Gmsh, VTK/VTU, MED, Exodus or UNV/UFF data under explicit artifact custody.
Select physical state and table first, retaining original labels, ply/layer,
centroid/element-node meaning, complex phase and omissions. Reconcile recovery
nodes against their element connectivity, not merely all model GRID IDs.
For repeated modes, compose with `fea-modal-correlation` and compare mapped
metric-aware subspaces; do not reject a rotated degenerate basis from pairwise
MAC alone. For Siemens preparation, `fea_compile_siemens_extension` inventories
loadcases, iterations, units and sections through documented release-specific
source. Artifact semantics (source: fea_expert_agent_plugin/docs/engineering/artifacts-v3.md) and
vendor readback boundaries (source: fea_expert_agent_plugin/docs/engineering/vendor-runtime-v3.md)
distinguish actual fields from metadata and unqualified native access.

For a durable CalculiX job, use `fea_calculix_job_to_series` with the exact
receipt hash and explicit fields/states, then `fea_export_result_series` and
`fea_import_result_series` for verified XDMF/HDF5 interchange. Retain original
DAT integration-point values for local stress and energy reasoning: FRD nodal
averaging is a distinct recovery operation. A zero CONTACT gap can be an open
surface; check deformed geometric separation and transmitted force. A pretension
MPC reference force is not automatically the bolt section force. Read the
[nonlinear output method](../fea-multistep-nonlinear/references/open-solver-workflows.md)
before drawing those conclusions.

## Completion boundary

Return the calculated or evidence-backed decision, its physical assumptions, the strongest falsifier exercised, and the specific unresolved dependency. Use qualified Engineering Desktop Runtime capabilities for native effects; this skill and source calculations do not create host authority. Preserve separate source, native, solver and engineering outcomes.
