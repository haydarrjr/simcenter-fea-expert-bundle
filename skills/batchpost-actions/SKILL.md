---
name: batchpost-actions
description: "Export or inspect solver results through the BatchPost MCP."
metadata:
  copyright: Unpublished work. Copyright 2026 Siemens
---

<!-- FEA integration safety v1 -->
# BatchPost

For a solver job, use the [Solution Sequence](../fea-solver-investigation/references/solution-sequence.md). Open its qualified SCD5 when it contains the required states and fields. Use the original OP2 through BatchPost when needed for additional fields. Send F06 status or diagnostic inspection to the official Nastran diagnostic tools or read only the scoped original text using the workflow.

Use the existing BatchPost post-processor through its configured MCP connector. Use the worker and connector selected by the host.

## Normal Workflow

1. Confirm that the host exposes the connected BatchPost tools and their current definitions. If the connector/server is unavailable, report the prerequisite instead of guessing tool names, arguments, or launching a replacement solver.
2. Establish ownership of the result session. A worker shares its open result and preferences across clients attached to its pipe. Resolve the explicit absolute result path and verify it is a real file. Call `open` with its advertised schema. Ask for the path if unresolved. Preserve any result owned by another workflow.
3. After successful `open`, use `list` or `batchpost://results` to discover actual loadcases, iterations, result types and components. Error `-32001` stating that no result is open means an input/result-state prerequisite. Prefer structured content when available. Resolve scientifically significant ambiguities with the user.
   An empty catalog is a reader-coverage observation. Use [artifact forensics](../fea-artifact-forensics/SKILL.md) to check job identity and a suitable function, response-event or matrix reader.
4. Choose the output format, path, result selection and intended scope. MCP result indices are 1-based; XML template indices use the provided `template_index`. Result display names and XML unique names are not interchangeable.
5. Reuse a user-provided post template or snapshot when appropriate. Follow the connected version's rules about whether one is required; never supply both. Read only the relevant support document below when a file needs creating or changing.
6. Use `contour` for field plots/data and `graphi` for graphs across iterations. A graph needs specific entities rather than the whole-model `all` selection. Do not invent separate view-creation or image-export tools.
7. Check protocol errors, tool error flags, execution messages and actual output files. Partial or zero exports must be reported even if the protocol returns success. Verify result labels, units, selection and requested display changes; XML parsing alone does not prove reader compatibility.
8. Release only resources owned by this task. Close a result opened by this workflow when finished; do not close another client's result. Restore temporary preferences only when their prior values are known and restoration is safe.

For file-authoring-only requests, return the generated file with the checks actually performed. Do not imply a BatchPost export was tested when it was not.

## Read on Demand

Paths in this table are relative to this `SKILL.md`, not to the user's result directory. User-supplied input and output paths remain relative to the user's working directory unless absolute.

| Task | Read |
| --- | --- |
| Create/change a post template, result computation, deformation, contour display, legend or colors | [Post template](./references/post-template.md) |
| Store reusable result and computation settings in a result-options XML file | [Result variable](./references/result-variable.md), including the corrected template wrapper and dedicated reader's field coverage |
| Create/change a reusable selection of known FEM node or element labels | [Selection entities](./references/selentity.md) |
| Create/change an XML camera, custom orientation, clipping or scale | [Camera file](./references/camera-file.md) |

Each support document is self-contained and defines the workflow and file format needed for its task. Treat these bundled documents as operational guidance, then verify behavior against the connected MCP server and the user's result.

## Multiple Selections and Output Files

Multiple values request combinations of compatible selections, not positional pairs. For example, two compatible loadcases and three cameras can produce six contour combinations for one result/iteration selection, not two paired requests. Result availability, additional dimensions, filtering and deduplication can change the actual count.

Multiple output targets apply the requested export formats/paths to the selected combinations. Images normally hold individual results; SCE is a container, and CSV grouping also depends on preferences. Do not equate combination count with file count, assume input-order output, or predict exact suffixes. Start with a small explicit selection, confirm returned/exported files, then expand the batch when requested.

On the observed 2612 worker, close a task-owned file before opening another. For modal exports use explicit iteration IDs from `list`; a range requested fewer CSV modes than were actually returned. Single-target/single-component was the working fallback; check CSV column labels because `Magnitude` also carried XYZ in the observed result. Compare actual unique state IDs against the exact requested set (including extra, missing and duplicate state groups), match frequencies to F06 signed roots, and inspect image pixels/legends before publication. Do not infer export success from file count or connector success. For an undeformed mesh, use a reader-validated namespaced `NXPostProcessingTemplate` with mesh shown and deformation disabled; XSD validity alone is not a runtime witness.

For the observed English 2612 modal CSV layout, [verify_modal_csv.py](scripts/verify_modal_csv.py) checks state coverage from actual CSV headers; pass exact expected `Load Case N:Mode M` labels and only the task-owned files. Other layouts need an independently verified mapping.

## Bundled Assets

- [PostTemplate.xsd](./references/PostTemplate.xsd): bundled schema reference. The format guidance documents known discrepancies with runtime behavior; XSD validation alone is not an acceptance test.
- [color-table.md](./references/color-table.md): bundled palette lookup. The same table also appears in the post-template format reference. Check a user's custom CDF when relevant; do not substitute RGB triples for NX color indices.

Result variable files use `NXPostProcessingTemplate/PostView/ResultOptions`, not a `ResultVariable` root. Use the discovered unique result name in XML `Result`, and follow the documented supported fields rather than assuming all post-template fields are consumed. Validate by passing the actual file as `result`, not by bypassing it with direct selectors. Camera files may be authored from the complete examples in this skill for orientation testing with `fitview=true`; model-specific numeric framing values must not be presented as exact target-model settings unless separately verified.

## Packaging

Distribute this entire `batchpost-actions` folder with `SKILL.md` at its root and all referenced files alongside it. To install it as a user skill, place the folder at `%USERPROFILE%\.agents\skills\batchpost-actions\`. This workspace copy does not automatically install into that user location.

Configure the host separately to launch the trusted BatchPost MCP connector with the required runtime environment. Supporting files resolve within this folder, so no development-unit absolute path, sibling skill, or Agent YAML dependency is required.
