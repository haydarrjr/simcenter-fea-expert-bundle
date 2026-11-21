---
name: batchpost-actions
description: "Inspect a solver result catalog, export field data, contours or XY graphs, or author BatchPost XML."
metadata:
  copyright: Unpublished work. Copyright 2026 Siemens
---

# BatchPost

Use the configured BatchPost MCP and its advertised tool schema. Bind an explicit result path or the exact saved result reference returned by an authorized read. Use the qualified SCD5 when it covers the requested states and fields. Use the original supported result file when it provides additional coverage.

1. Check the file and open it in a task-owned result context. Preserve another client's worker state. Use `list` or `batchpost://results` after opening to discover actual loadcases, iterations, result types and components.
2. Use `contour` for fields and `graphi` for graphs across iterations on specific entities. MCP result selectors are 1-based. For XML use the observed `template_index` and result `unique_name`. Supply a post template or snapshot according to the live schema.
3. Verify the tool's inner status, actual output files, requested states, quantities, units and scope. Inspect image contents for visual requests. Release only task-owned worker state. For configuration authoring report structural checks and any actual reader verification.

| Need | Read |
|---|---|
| Shared worker, empty catalog, multi-selection or modal export | [Result selection and verification](references/result-export.md) |
| Contour, deformation or legend settings | [Post template](references/post-template.md) |
| Reusable result and computation settings | [Result options XML](references/result-variable.md) |
| Nodal random displacement RMS or PSD CSV | [Random displacement CSV](references/random-displacement-csv.md) |
| Explicit node or element labels | [Selection XML](references/selentity.md) |
| Custom orientation or saved framing | [Camera XML](references/camera-file.md) |
