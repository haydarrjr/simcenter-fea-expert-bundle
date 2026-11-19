---
name: fea-artifact-forensics
description: "Inspect original Simcenter Nastran deck, F06 and OP2 evidence through Siemens MCPs. Verify provenance, scope and physical result identity."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Artifact forensics

Identify the original named files, model revision, solution/subcase, run time, units and coordinate frame. Record exact paths, hashes and sizes before reading; filenames alone do not bind an archive to the open model.

1. Use the Nastran MCP for authorized deck, include, F06 and log inspection when advertised. Otherwise use bounded reads of the explicitly scoped original text artifacts. Reconcile include paths inside the authorized root and mark unresolved references.
2. Open the exact OP2 through official [BatchPost](../batchpost-actions/SKILL.md), list its actual result states, then export the requested quantities. Preserve labels, element/node/ply location, layer, component, frame, averaging, physical units and state indices.
3. For matrices or formats without an advertised Siemens reader, retain provenance and report the unsupported data as NOT_RUN. Select a compatible original export only from the same solved state.
4. Use [solver investigation](../fea-solver-investigation/SKILL.md) to reconcile the effective deck, F06 and result. Preserve distinct states when IDs, hashes or mesh/BC revisions differ.

Read [artifact custody and compatibility](references/engineering-method.md).
