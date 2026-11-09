# Create a BatchPost Result Variable

## Scope

A result variable file is a result-settings subset of a post template, not a separate XML vocabulary. It keeps the `NXPostProcessingTemplate / PostView / ResultOptions` hierarchy and is supplied through the BatchPost `result` argument. The base post template or snapshot supplies the view/display settings.

## XML Contract

- Use `NXPostProcessingTemplate` as the root, containing `PostView` and `ResultOptions`. Do not emit a `ResultVariable` root or a bare `ResultOptions` root.
- Use `<Result>` with the exact bracketed `unique_name` from result discovery, such as `[Strain][Element-Nodal]`. Do not use `<ResultType>` or a display name such as `Strain - Element-Nodal` in its place.
- Use the actual supported `<Component>` name. Do not infer it from the result filename or a familiar result convention.
- Retain appropriate wrapper attributes from a user-provided exported file when deriving one. In the example below, `Version="NX2512"` is illustrative and is not a universal runtime version to force onto other files.
- Display-only sections, legends, colors and cameras are not needed in a result-only file. For the broader template structure, see [Post template](./post-template.md).
- The result-file path supports only a subset of the full post-template settings. Do not assume every field in a full template or [PostTemplate.xsd](./PostTemplate.xsd) is consumed.

### Supported Settings

Supported settings include result and component; beam/shell sections; section, ply and layer settings; midnodes and node-normal projection; computation options; coordinate-system settings; element-value options; complex component/phase and absolute value; beam stress/strain calculation and fillets; spectrum scaling and acoustic weighting.

Preserve documented spellings and numeric `0`/`1` booleans. Fields such as ply IDs, section choices and coordinate-system IDs are model-specific: copy them only when applicable, not merely because they appear in an example.

This result-file path does **not** consume `Unit`, `LoadCase`, `Iteration`, `SubIteration`, `ResultScale`, or the full set of post-template options. Specify loadcase/iteration and requested output units through supported tool arguments or an appropriate base template, and verify the effective settings in the export. In particular, adding `<Unit>` to this file is not evidence of a unit override.

Do not promise that every omitted setting inherits the base template unchanged. Runtime defaults may apply. Prefer deriving result options from a suitable user-provided file and verify the settings that matter for the requested calculation.

## Workflow

1. Identify the result file, requested physical result/component, optional unit, and destination file. Preserve the user's original files by writing a derived copy unless overwrite is explicitly requested.
2. Read the current MCP definitions and discover results through `list` or `batchpost://results`. Obtain the exact `unique_name` for XML `<Result>` and a supported component at the intended loadcase/iteration. Do not construct these names from a filename or substitute a familiar physical quantity.
3. Use an XML parser to derive a result-settings file from a suitable user-provided result XML or the `PostView/ResultOptions` section of a post template. If neither is available, adapt the self-contained example below. Keep the wrapper and requested supported settings; omit unrelated display sections. The strain example is illustrative, not a default for acoustic or other models.
4. Parse the saved XML and explicitly check the required hierarchy plus nonempty Result/Component. Missing child sections may still parse without proving they have any effect. XSD checks are supplementary, not proof that the runtime consumes each field.
5. Pass the new file path as `result` according to the live tool schema. Keep `resulttype` (a tool name/pattern selector) distinct from `result` (an XML path) and XML `Result` (a bracketed unique name). Supply a compatible posttemplate or snapshot as required by the server. For an effectiveness test, avoid direct resulttype/component overrides that could hide an ignored file.
6. Verify that the export actually uses the file's result and component, preferably choosing a result different from the base template for the test. Check relevant computation, complex and coordinate settings and effective units. A direct-selector control request is not a replacement for testing the file path.
7. Check JSON-RPC errors, tool `isError`, execution messages and real output files together. Close only a result opened and owned by this task. Return the XML path and distinguish structural checks from actual reader/export verification.

## Result-Options Example

This compact example demonstrates the required wrapper and a subset of supported options. Replace its result, component and version with values appropriate to the connected server and the user's result.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NXPostProcessingTemplate TemplateType="User" Version="NX2512">
     <PostView>
          <ResultOptions>
               <Result>[Strain][Element-Nodal]</Result>
               <Component>XY</Component>
               <IncludeMidnodes>1</IncludeMidnodes>
               <ProjectOnNodeNormal>0</ProjectOnNodeNormal>
               <CoordinateSystem>Absolute Rectangular</CoordinateSystem>
               <CoordinateSystemSource>None</CoordinateSystemSource>
               <CoordinateSystemID>-1</CoordinateSystemID>
               <ComplexComponent>Amplitude</ComplexComponent>
               <ComplexPhaseAngle>0.0</ComplexPhaseAngle>
               <AbsoluteValue>0</AbsoluteValue>
          </ResultOptions>
     </PostView>
</NXPostProcessingTemplate>
```

## Validation Notes

Do not use a `ResultVariable/ResultType` structure: the supported hierarchy is the one documented above. The generated file must still be verified against the intended data and connected server before claiming a successful export. Also inspect execution messages and output artifacts because a tool may report protocol success even when no files were exported.
