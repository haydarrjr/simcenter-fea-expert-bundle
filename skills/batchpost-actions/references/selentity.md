# Create a BatchPost Selection Entity File

## Scope

This document is a self-contained guide to the BatchPost node and element selection format. It does not define additional geometry or query interfaces.

## Workflow

1. Establish whether the selection contains nodes, elements, or both, and obtain exact FEM labels and the output path. If the user supplies a geometric description without labels, request the mapping or use an explicitly available discovery interface. Never invent labels or infer them from filenames.
2. Write a new `<SelectionEntities>` XML file using `<ElementIds>` and/or `<NodeIds>` as documented below. Omit unused entity types. Preserve compact lists/ranges and reject malformed or reversed ranges instead of silently changing the selection.
3. Parse the XML and check the selected labels against available model/result evidence. XML parsing validates syntax, not the existence of entities or availability of their results. Missing mesh evidence must be reported as unverified.
4. For the whole model in a contour, use the server's supported `selentity` all selection instead of inventing an all-IDs XML file. A graph needs specific entities; do not use all for `graphi`. If the user explicitly requests a reusable XML file, still create one for their known labels rather than silently replacing it with inline IDs.
5. For an export test, inspect the live MCP tool schema, open the intended result if needed, discover available results, and pass the file path using the actual `selentity` argument shape. Do not combine inline node/element arguments with a selentity file. Do not guess an alternative API if a tool is unavailable.
6. Verify actual output against the requested selection, ideally using exported CSV entity labels. Rendering alone does not prove the correct labels were selected. Preserve source files and report failures or missing-data warnings. Close only a result opened and owned by this task.
7. Return the XML path, selected entity types and labels, and the checks actually completed.

## Selection Format Reference

BatchPost selection entity XML — annotated reference
=====================================================

Root element: <SelectionEntities>
  Child: <ElementIds>   (optional) — element IDs to include
  Child: <NodeIds>      (optional) — node IDs to include

ID format (for both children):
  Comma-separated integers and/or closed ranges, e.g.:
    "1, 5, 10-20, 50"   → IDs 1, 5, 10 through 20, and 50
    "101-250"            → all IDs from 101 to 250 inclusive
    "1-100, 201-300"     → two ranges combined
  - Whitespace around commas and dashes is tolerated.
  - Both children are optional; omit the child element to include no entities of that type.
  - To select all entities, pass selentity=all on the command line instead of using a file.

Minimal example — nodes only:
<?xml version="1.0" encoding="UTF-8"?>
<SelectionEntities>
  <NodeIds>1-500</NodeIds>
</SelectionEntities>

Minimal example — elements only:
<?xml version="1.0" encoding="UTF-8"?>
<SelectionEntities>
  <ElementIds>101, 205, 310-450</ElementIds>
</SelectionEntities>

Combined nodes and elements:
<?xml version="1.0" encoding="UTF-8"?>
<SelectionEntities>
  <ElementIds>1-1000, 2001-2500</ElementIds>
  <NodeIds>5001-6000</NodeIds>
</SelectionEntities>

Notes:
- The ID values must be exact FEM labels from the mesh; BatchPost does not
  translate or resolve them further.
- What those IDs represent (e.g., "nodes 1-500 are the left wing skin") is
  model-specific knowledge that must be provided by the user or the driving
  agent — BatchPost only needs the raw IDs.
- BatchPost writes selentity files using the same compact range format shown
  above when it exports them from NX.
