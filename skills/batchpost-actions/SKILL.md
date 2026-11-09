---
name: batchpost-actions
description: "Post-process simulation result files with the BatchPost MCP connector. Use when exporting contours, graphs across iterations, CSV or SCE, or creating/modifying post templates, result variables, selection entity XML, or camera files."
metadata:
  copyright: Unpublished work. Copyright 2026 Siemens
---

<!-- FEA integration safety v1 -->
## FEA integration safety contract (overrides conflicting legacy guidance)

- Discover the current tool catalog and exact input schemas before calling tools.
  A connected server need not expose every tool from older documentation.
  If a call fails, check dc_connection_status first. Retry bounded read-only
  discovery after recovery; never replay an uncertain mutation blindly.
- Documentation: use documentation-search-tool only when currently advertised.
  If absent after connectivity recovery, route to the advertised Product Support
  search tool using its current schema and version-specific Siemens sources.
  If neither route is available, report BLOCKED_BY_OFFICIAL_MCP_CAPABILITY /
  NOT_RUN; do not invent syntax, citations, or answers from memory.
- Pagination: send PAGE or CURSOR only if that exact parameter exists in the
  current tool input schema. A response mentioning hasMoreSchema/hasMoreData
  does not authorize unsupported arguments. If continuation is unavailable,
  report the read as PARTIAL with the unresolved scope; do not claim completeness.
- Journal sandbox: import only NXOpen modules. Never import sys or another
  standard-library module. Use sys.argv only when the current journal tool
  explicitly supplies sys; otherwise stop and verify the supported entry point.
  Keep main(args), session acquisition and builder cleanup requirements.
- A sandbox SUCCESS, exit code zero, or no captured stdout is not observable
  proof that statements, assertions, or error paths executed. Report execution
  transport status separately from observable test evidence. Without inspectable
  output/readback, the claimed behavior remains UNVERIFIED, not tested-correct.
- Action verbs alone do not authorize an ambiguous target, save, solve, or
  overwrite. Live changes require explicit user intent, an identified owned
  working copy, current advertised capability and applicable host approval.
  After a change, obtain independent native readback tied to model identity.
- Mesh metrics: null, zero, placeholder, unavailable or uncomputed values are
  UNVERIFIED unless the metric definition, element applicability and computation
  status establish their meaning. Never convert missing evidence into PASS.
  Free edges may be intentional shell boundaries; interpret topology explicitly.
  Use project/solver/element-specific documented thresholds, not universal limits.
  Shape quality alone does not establish QoI mesh convergence or solve acceptance.
<!-- End FEA integration safety v1 -->

# BatchPost

Use the existing BatchPost post-processor through its configured MCP connector. This folder is one portable skill, not an agent definition. Agent roles, orchestration, and MCP server configuration belong to the host/user; no Agent YAML or solver workflow is supplied here.

## Normal Workflow

1. Confirm that the host exposes the connected BatchPost tools and their current definitions. If the connector/server is unavailable, report the prerequisite instead of guessing tool names, arguments, or launching a replacement solver.
2. Establish ownership of the result session. The tested server shares a single open result and preferences across clients. Open the user's intended file only when the session is available; never replace another workflow's result.
3. Use `list` or `batchpost://results` resources to discover actual loadcases, iterations, result types and components. Prefer structured content when available; do not concatenate separate text blocks into JSON. Resolve scientifically significant ambiguities with the user.
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

## Bundled Assets

- [PostTemplate.xsd](./references/PostTemplate.xsd): bundled schema reference. The format guidance documents known discrepancies with runtime behavior; XSD validation alone is not an acceptance test.
- [color-table.md](./references/color-table.md): bundled palette lookup. The same table also appears in the post-template format reference. Check a user's custom CDF when relevant; do not substitute RGB triples for NX color indices.

Result variable files use `NXPostProcessingTemplate/PostView/ResultOptions`, not a `ResultVariable` root. Use the discovered unique result name in XML `Result`, and follow the documented supported fields rather than assuming all post-template fields are consumed. Validate by passing the actual file as `result`, not by bypassing it with direct selectors. Camera files may be authored from the complete examples in this skill for orientation testing with `fitview=true`; model-specific numeric framing values must not be presented as exact target-model settings unless separately verified.

## Packaging

Distribute this entire `batchpost-actions` folder with `SKILL.md` at its root and all referenced files alongside it. To install it as a user skill, place the folder at `%USERPROFILE%\.agents\skills\batchpost-actions\`. This workspace copy does not automatically install into that user location.

Configure the host separately to launch the trusted BatchPost MCP connector with the required runtime environment. Supporting files resolve within this folder, so no development-unit absolute path, sibling skill, or Agent YAML dependency is required.