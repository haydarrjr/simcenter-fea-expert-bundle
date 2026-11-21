# BatchPost post-template XML

For a display change, derive a copy of a compatible exported template when available. Edit only the relevant sections with an XML parser, preserving their spelling, nesting and order. Use the observed `unique_name` in `Result`, the catalog's component name and `template_index` values for `LoadCase` and `Iteration`. Catalog MCP selector indices are 1-based. Result color and deformation may refer to different fields or states.

## Minimal display template

This partial template sets mesh display and disables deformation. Select the result with the connected tool's supported selectors. The 2612 worker accepted the installed partial-template format with the `NX8.5` serialization tag. Substituting the product build tag `NX2612` in the post template returned invalid document structure. Preserve the exported wrapper and its version for the intended reader.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NXPostProcessingTemplate xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                          Version="NX8.5" TemplateType="User"
                          xsi:noNamespaceSchemaLocation="PostTemplate.xsd">
  <PostView>
    <ColorScheme>Mesh</ColorScheme>
    <DeformationOptions>
      <ShowDeformation>0</ShowDeformation>
    </DeformationOptions>
  </PostView>
</NXPostProcessingTemplate>
```

## Where to edit

| Goal | Template section |
|---|---|
| Contour, vectors, tensors or streamlines | `ColorScheme` and `ResultDisplayOptions` |
| Result, units, coordinate frame, complex phase, recovery or averaging | `ResultOptions`. Use the selected result's actual component, support and section. Limit averaging across discontinuities to the intended engineering scope |
| Deformation | `DeformationOptions` with its own `ResultOptions` when applicable, plus the intended absolute or percent-model scale |
| Exposed faces, volume or a cut | `DisplayOnOptions`, with the actual cutting plane and coordinate system when needed |
| Legend, range, annotations or model edges | `HeaderOptions`, `ColorbarOptions`, `EdgefaceDisplayOptions`, `TextOptions` and marker options |
| Group visibility or translucency | `GroupVisibilities` or `GroupTranslucency`; derive the group order, count and matching flags from the current model |

Use [PostTemplate.xsd](PostTemplate.xsd) for element structure and [the indexed palette](color-table.md) for color IDs. Check the model's custom color definition when applicable. Use [result-options XML](result-variable.md) for the subset accepted by the dedicated `result` argument.

The reader uses numeric Booleans `0` and `1`, `Contour` for fringe color, and `Iso-Surface` for the corresponding display style. Use `Contour` in place of legacy `Element` display style. Retain the native spellings `DisplayShellResultsInPojectedCoordinateSystem` and computation tags such as `AccrossMaterials`. A mark's text-color enum is `TextColor`; the streamline equivalent is `Text Color`. Use the connected release's exported representation for options where the schema and reader disagree.

Parse the new file and, when export is requested, send that exact path as the post template through the live tool schema. Start with one selected output. Check the actual output files, image, quantity, units, scope and changed display behavior. Record structural checks and reader evidence separately.
