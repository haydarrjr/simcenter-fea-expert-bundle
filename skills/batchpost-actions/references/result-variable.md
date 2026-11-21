# BatchPost result-options XML

Use the dedicated `result` argument to supply result and computation settings. The post template or snapshot supplies the base view when required by the connected schema.

The root is `NXPostProcessingTemplate` with `PostView/ResultOptions`. Bind `Result` to the exact bracketed `unique_name` and `Component` to the actual name returned by the catalog. Keep the wrapper attributes from a compatible exported file when deriving a copy. This synthetic structure illustrates one possible catalog entry.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NXPostProcessingTemplate TemplateType="User" Version="NX2612">
  <PostView>
    <ResultOptions>
      <Result>[Displacement][Nodal]</Result>
      <Component>Magnitude</Component>
    </ResultOptions>
  </PostView>
</NXPostProcessingTemplate>
```

Preserve the names, nesting and numeric `0`/`1` flags for supported settings. These include beam and shell sections, ply/layer, midnodes, projection, computation and coordinate systems, element values, complex phase, absolute value, beam recovery, spectrum scaling and acoustic weighting. Bind section, ply and coordinate IDs to the current model. Verify effective values because omitted fields may use reader defaults.

The dedicated reader does not consume `Unit`, `LoadCase`, `Iteration`, `SubIteration` or `ResultScale`. Use the live selectors or the [base post template](post-template.md) for those settings as appropriate. The `resulttype` tool selector uses the display name. The `result` argument takes the XML path.

Parse the saved file and check its hierarchy, result and component. For reader validation pass the actual path without competing direct result/component overrides. Check the actual written file, result identity, units and intended computation or frame.
