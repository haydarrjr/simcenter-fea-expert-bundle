---
name: fea-artifact-forensics
description: "Investigate real BDF/OP2/OP4, mesh and field files; preserve source identity, include graphs, node/element mapping, subcase/time/frequency/mode and ply/side/complex state. Use for unfamiliar solver files, mismatched results, matrix provenance and format interchange."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Artifact forensics

Start with the actual files and the physical question. Call `fea_capabilities`
to see the qualified formats and dependency state, then `fea_inspect_artifact`
on a relative path in the explicitly configured artifact directory. Preserve
source hashes and record unit declarations as declarations. A recognized suffix
does not prove a solver, unit system, frame, complete output or successful run.

## Investigation

1. Distinguish a native Siemens FEM/SIM binary from an exported text deck.
   Request an explicit format only after inspecting evidence of the representation.
2. Inspect effective case control, mesh labels/connectivity, material/property
   records, orientation, loads and constraints. Resolve supplied INCLUDE files
   with `fea_inspect_bdf_bundle`; never chase an operating-system INCLUDE path.
3. Select the necessary result tables, states and rows. Preserve every physical
   recovery key, including centroid/node, ply, layer, station, side and complex
   phase. Re-request a bounded selection when the report declares omissions.
4. Use `fea_compare_artifacts` with `kind=model_results` to reconcile mesh and
   recovery identity; use `kind=result_tables` only for complete compatible
   selections. Matching norms or von Mises values do not prove matching tensors.
5. For qualified linear solid decks, call `fea_prepare_continuum_from_bdf` with
   explicit length/force/mass scales, then `fea_solve_continuum` on the returned
   request. Compare all selected displacement/reaction rows to source results.
6. For an actual CalculiX job, use `fea_calculix_job_to_series` with its receipt
   hash and explicitly selected nodal fields; re-establish every requested
   step's completion from original FRD/STA before selecting a subset. Use
   `fea_export_result_series` / `fea_import_result_series` for lossless
   fixed-mesh XDMF/HDF5. Preserve body, state, unit, frame and recovery metadata;
   refuse a contact/Gauss/pretension-cut projection without an explicit mapping.
   The open workflow method (source: fea_expert_agent_plugin/docs/engineering/source-tools-v4.md)
   explains full physical tensors and independent-consumer checks.

Read [method, options and falsifiers](references/engineering-method.md) before
making a cross-file comparison. Route thermal/structural recalculation to
[Continuum thermomechanics](../fea-continuum-thermomechanics/SKILL.md), laminates
to [Composite laminates](../fea-composite-laminates/SKILL.md), and authenticated
job custody to [Runtime gate](../fea-native-runtime-gate/SKILL.md).

Return the physical interpretation, exact evidence and omissions, the strongest
contradiction tested and the next useful computation. Keep parser compatibility,
model/result compatibility and engineering acceptance distinct.
