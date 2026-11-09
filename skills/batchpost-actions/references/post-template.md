# Create a BatchPost Post Template

## Scope

This document is a self-contained guide to the BatchPost post-template format, including a complete XML example and color table. It describes files consumed by an existing BatchPost MCP connector, not a new tool API.

## Workflow

1. Identify the requested output file and display changes. Without a specific display request, use a standard contour display. Prefer deriving a new file from the user's existing template; never overwrite it without permission.
2. For result-dependent settings, inspect the connected server's tool definitions and use `list` or results resources for the chosen result file. Reuse an already-open matching result only with appropriate ownership; do not replace another client's result. If MCP is unavailable, report that runtime validation is blocked instead of guessing tool arguments or result names.
3. Use the discovered `unique_name` for `<Result>`, the actual component name, and `template_index` for XML loadcase/iteration indices. MCP selectors use different, 1-based indices. Do not copy the sample's stress, displacement, units, groups, or indices into an acoustic or unrelated model without checking availability. Confirm any scientifically significant ambiguity with the user.
4. Apply only the requested changes using an XML parser when editing an existing file. Preserve the documented spelling, nesting, numeric booleans, and enum values. Keep result color and deformation selections distinct. If deformation is not requested or its result is unavailable, do not assume displacement exists.
5. Parse the saved XML for well-formedness. The retained [PostTemplate.xsd](./PostTemplate.xsd) is a reference, not proof of reader acceptance; a schema-location attribute does not run validation. Report schema findings separately from actual reader acceptance because the reference documents known disagreements.
6. When export is requested, use the current MCP schema to supply the file to `contour` or `graphi`. A post template and snapshot are alternatives, not simultaneous inputs. Start with one explicitly selected result and output before expanding a batch. Multiple selections may expand combinations rather than pair entries; do not promise a fixed output count or filename without evidence.
7. Check JSON-RPC errors, tool `isError`, execution messages, and actual generated files. A successfully parsed XML or a success message alone is insufficient to verify the intended display. Inspect the exported image and its result labels. Close a result opened by this task when finished, but do not unconditionally close a shared result owned by another workflow.
8. Deliver the XML file path, summarize the changed settings and verification performed, and explain relevant settings the user may change. Distinguish generated, XML-parsed, and BatchPost-rendered outcomes; preserve warnings and do not claim unexecuted checks passed.

## Post-Template Format Reference

Below is the annotated reference for BatchPost post-processing XML templates.

This reference records the BatchPost XML contract used at runtime. The bundled
PostTemplate.xsd differs from runtime behavior in several places and is not an acceptance test.
Follow this document when a rule conflicts with the XSD.

Critical reader rules that differ from the XSD / are easy to get wrong:
- Booleans MUST be written as 0 or 1. The reader rejects "true"/"false" (it warns and discards
  the value). Every flag below therefore uses 0/1.
- ColorScheme uses "Contour" for fringe display, NOT "Fringe".
- DisplayStyle uses "Iso-Surface" (the XSD typo "so-Surface" is wrong). The legacy "Element"
  style was removed; use "Contour" instead.
- The shell-projection tag is literally spelled <DisplayShellResultsInPojectedCoordinateSystem>
  (note the missing "r": "Pojected"). That misspelling is the real tag the reader looks for.
- The mark-color enum value "TextColor" is one word, but the streamline-color enum value
  "Text Color" is two words. They are different tables; do not interchange them.
- Element order and section nesting below match what the reader expects -- preserve them.
- Numeric values may be written in any C float format (e.g. 15.0 or 1.500000e+01); leading
  whitespace is tolerated.

The example below is a complete template. Allowed enum values are listed in comments next to
each enumerated element. Replace all model-specific result names, units, groups and indices with
values discovered from the user's result before execution.

```xml
<NXPostProcessingTemplate TemplateType="User" Version="NX2606" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="PostTemplate.xsd">
  <PostView>
    <!-- General Display Options -->
    <Lighted>1</Lighted> <!-- Render with lighting (0/1). Consider 0 for hardcopy/publishing. -->
    <!-- ColorScheme: color distribution scheme. Allowed: "Contour" (fringe), "Mid", "Pid"
         (physical property id), "Mesh". NOTE: "Contour", not "Fringe". -->
    <ColorScheme>Contour</ColorScheme>
    <Compress>0</Compress> <!-- Enable display compression (0/1) -->
    <FaceNormalTolerance>15.0</FaceNormalTolerance> <!-- Angle tol (deg) for feature/coplanar elements -->
    <ValueBandTolerance>10.0</ValueBandTolerance> <!-- Tolerance for values within the same contour band -->

    <ResultDisplayOptions>
      <ResultDisplay>1</ResultDisplay> <!-- Toggle result display (0/1) -->
      <!-- DisplayStyle. Allowed: "Contour", "Iso-Line", "Iso-Surface", "Cubes", "Spheres",
           "Arrows", "Tensors", "Streamlines". "Streamlines" needs a streamline seed set.
           NOTE: "Iso-Surface" (not "so-Surface"); the legacy "Element" style is gone, use "Contour". -->
      <DisplayStyle>Contour</DisplayStyle>
      <ColorbarStyle>Smooth</ColorbarStyle> <!-- Allowed: "Smooth", "Banded" -->
      <DrawLines>0</DrawLines> <!-- Boundary lines between color bands (0/1) -->
      <Lighted>1</Lighted> <!-- Lighting for the contour faces (0/1) -->
      <BeamDisplayStyle>Line</BeamDisplayStyle> <!-- Allowed: "Line", "Line and Diagram", "Solid" -->
      <BeamContourScaleMethod>%Model</BeamContourScaleMethod> <!-- Allowed: "%Model", "Absolute" -->
      <BeamContourScaleFactor>10.0</BeamContourScaleFactor>

      <!-- CompressOptions: polygon-reduction tolerances -->
      <CompressOptions>
        <DisplayCompression>0</DisplayCompression> <!-- 0/1 -->
        <ValueTolerance>10.0</ValueTolerance>
        <FaceNormalTolerance>15.0</FaceNormalTolerance> <!-- Degrees -->
      </CompressOptions>

      <!-- MarkOptions: arrows/tensors when DisplayStyle is "Arrows" or "Tensors" -->
      <MarkOptions>
        <ArrowComponentX>0</ArrowComponentX> <!-- 0/1 -->
        <ArrowComponentY>0</ArrowComponentY> <!-- 0/1 -->
        <ArrowComponentZ>0</ArrowComponentZ> <!-- 0/1 -->
        <ArrowComponentMag>0</ArrowComponentMag> <!-- 0/1 -->
        <ArrowComponentResultant>0</ArrowComponentResultant> <!-- 0/1 -->
        <ArrowComponentCombinationType>None</ArrowComponentCombinationType> <!-- Allowed: "None", "XY", "YZ", "ZX" -->
        <!-- Allowed: "Normal Component", "Principal Component", "Shear Component", "Force Component", "Moment Component" -->
        <MarkComponentCombinationType>Normal Component</MarkComponentCombinationType>
        <Component1>0</Component1> <!-- 0/1 -->
        <Component2>0</Component2> <!-- 0/1 -->
        <Component3>0</Component3> <!-- 0/1 -->
        <Component4>0</Component4> <!-- 0/1 -->
        <MarkStyle>Line</MarkStyle> <!-- Allowed: "Line", "Solid" -->
        <TensorStyle>Detailed</TensorStyle> <!-- Allowed: "Detailed", "Arrow", "Box", "Line" -->
        <MarkColor>Colorbar</MarkColor> <!-- Allowed: "Colorbar", "Specified", "TextColor" -->
        <SpecifiedColor>211</SpecifiedColor> <!-- Color index [1..216]; see table below -->
        <MarkSize>Result</MarkSize> <!-- Allowed: "Result", "Specified" -->
        <MaxMarkSize>% Model</MaxMarkSize> <!-- Allowed: "% Model", "Specified" -->
        <ModelPercentSizeValue>5.0</ModelPercentSizeValue> <!-- Size as % of model bounding box -->
        <SpecifiedMaxMarkSizeValue>1.0</SpecifiedMaxMarkSizeValue> <!-- Absolute size -->
        <HideMarksBelow>0</HideMarksBelow> <!-- 0/1 -->
        <BelowOption>% Maximum Result</BelowOption> <!-- Allowed: "% Maximum Result", "% Absolute Maximum Result", "Result Value" -->
        <BelowResultPercentValue>50.0</BelowResultPercentValue>
        <BelowSpecifiedResultValue>0.0</BelowSpecifiedResultValue>
        <BelowAbsoluteResultPercentValue>50.0</BelowAbsoluteResultPercentValue>
        <DisplayNumericValueWithArrow>0</DisplayNumericValueWithArrow> <!-- 0/1 -->
        <DisplayLabelWithArrow>0</DisplayLabelWithArrow> <!-- 0/1 -->
        <DoubleSidedArrow>0</DoubleSidedArrow> <!-- 0/1 -->
      </MarkOptions>

      <NodalForceReportDisplayOptions>
        <DisplayAtCentroid>0</DisplayAtCentroid> <!-- 0/1 -->
      </NodalForceReportDisplayOptions>

      <!-- Display of lumped mass elements -->
      <MassOptions>
        <MassSizeOption>% Model</MassSizeOption> <!-- Allowed: "% Model", "Specified" -->
        <ModelPercentSizeValue>2.5</ModelPercentSizeValue>
        <SpecifiedSizeValue>5.0</SpecifiedSizeValue>
      </MassOptions>

      <!-- Display of spring elements -->
      <SpringOptions>
        <SpringSizeOption>% Model</SpringSizeOption> <!-- Allowed: "% Model", "Specified" -->
        <ModelPercentSizeValue>2.5</ModelPercentSizeValue>
        <SpecifiedSizeValue>5.0</SpecifiedSizeValue>
      </SpringOptions>

      <!-- StreamlineOptions: used when DisplayStyle is "Streamlines" -->
      <StreamlineOptions>
        <StreamlineSeedSet>-1</StreamlineSeedSet> <!-- Seed Set group tag id, or -1 if none. Only set this if told to. -->
        <StreamlineDataOptions>
          <ValueSharing>Average</ValueSharing> <!-- Allowed: "Average", "Minimum", "Maximum" -->
          <NoDataTreatment>Ignore</NoDataTreatment> <!-- Allowed: "Ignore", "Use Value" -->
          <NoDataValue>0.0</NoDataValue>
        </StreamlineDataOptions>
        <StreamStyle>Line</StreamStyle> <!-- Allowed: "Line", "Ribbon", "Tube", "Bubbles" -->
        <StreamColor>Result</StreamColor> <!-- Allowed: "Result", "Specified", "Text Color" -->
        <SpecifiedColor>211</SpecifiedColor> <!-- Color index [1..216] -->
        <StreamSize>% Model</StreamSize> <!-- Allowed: "% Model", "Specified" -->
        <ModelPercentSizeValue>1.0</ModelPercentSizeValue>
        <SpecifiedSizeValue>1.0</SpecifiedSizeValue>
        <LineWeight>Normal</LineWeight> <!-- Allowed: "Thin", "Normal", "Thick" -->
        <BubbleSynchronization>At Seed Point</BubbleSynchronization> <!-- Allowed: "Upstream", "Downstream", "At Seed Point" -->
        <BubbleTimeStep>0.5</BubbleTimeStep>
      </StreamlineOptions>
    </ResultDisplayOptions>

    <!-- ResultOptions: which result is plotted and how it is computed -->
    <ResultOptions>
      <LoadCase>0</LoadCase> <!-- 0-based loadcase index -->
      <Iteration>0</Iteration> <!-- 0-based iteration index -->
      <SubIteration>-1</SubIteration> <!-- 0-based sub-iteration index, -1 if none -->
      <Result>[Stress][Element-Nodal]</Result> <!-- Unique result name: [Quantity][Support] or [Quantity][Tag1]...[TagN] from the result listing -->

      <AxisymmetricResultOptions>
        <RevolveAxis>X-Axis</RevolveAxis> <!-- Allowed: "X-Axis", "Y-Axis", "Z-Axis" -->
        <ResultExtractMethod>Original 2D Model</ResultExtractMethod> <!-- Allowed: "Original 2D Model", "3D Model" -->
        <OriginalModelOption>At Revolve Angle</OriginalModelOption> <!-- Allowed: "At Revolve Angle", "Envelope Across Circumference" -->
        <!-- EnvelopeOption used when enveloping. Allowed: "Maximum", "Minimum", "Absolute Maximum", "Absolute Minimum", "Average", "Sum" -->
        <EnvelopeOption>Average</EnvelopeOption>
        <NumberOfSections>40</NumberOfSections>
        <RevolveAngle>0.0</RevolveAngle>
        <StartRevolveAngle>0.0</StartRevolveAngle>
        <EndRevolveAngle>360.0</EndRevolveAngle>
      </AxisymmetricResultOptions>

      <NumberOfCyclicStages>0</NumberOfCyclicStages>
      <Component>Von-Mises</Component> <!-- Component name string; see result listing -->

      <dBScaling>0</dBScaling> <!-- 0/1 -->
      <dBReference>1.0</dBReference> <!-- Reference value mapped to 0 dB; must be positive -->
      <convertedDBRef>1.0e-06</convertedDBRef> <!-- Internal converted reference; used in dB math, not displayed -->
      <dBScale>dB20</dBScale> <!-- Allowed: "dB10" (10*log10), "dB20" (20*log10) -->
      <SectionNumber>0</SectionNumber>

      <PlyNumber>0</PlyNumber> <!-- 1-based ply index; 0 for non-composite / default -->
      <LayerNumber>0</LayerNumber> <!-- 1-based layer index; 0 for all/default -->
      <IncludeMidnodes>1</IncludeMidnodes> <!-- 0/1 -->
      <ProjectOnNodeNormal>0</ProjectOnNodeNormal> <!-- 0/1 -->
      <PlyID>0</PlyID> <!-- Composite ply id; 0 to ignore -->
      <PlyLocation>1</PlyLocation> <!-- Through-ply location: 0=Bottom, 1=Middle, 2=Top -->

      <!-- ComputationOptions: nodal/element averaging controls -->
      <ComputationOptions>
        <!-- Allowed: "None", "Average", "Sum", "Minimum", "Maximum", "Absolute Minimum",
             "Absolute Maximum", "Arithmetic Mean", "Discontinuity",
             "Signed Absolute Minimum", "Signed Absolute Maximum" -->
        <NodalCombination>Average</NodalCombination>
        <AccrossPhysicalProperties>1</AccrossPhysicalProperties> <!-- 0/1 (spelling "Accross" is intentional) -->
        <AccrossMaterials>1</AccrossMaterials> <!-- 0/1 -->
        <AccrossElementTypes>1</AccrossElementTypes> <!-- 0/1 -->
        <AccrossFeatureAngles>1</AccrossFeatureAngles> <!-- 0/1 -->
        <FeatureAngleValue>45.0</FeatureAngleValue>
        <IncludeInternalElements>1</IncludeInternalElements> <!-- 0/1 -->
        <Scope>Entire Model</Scope> <!-- Allowed: "Entire Model", "Visible Model" -->
        <AcrossNonmanifoldEdges>1</AcrossNonmanifoldEdges> <!-- 0/1 (single "c": "Across") -->
        <ExcludeElements>0</ExcludeElements> <!-- 0/1 -->
        <DiscontinuityOption>Relative</DiscontinuityOption> <!-- Allowed: "Relative", "Weighted", "Local", "Locally Balanced" -->
      </ComputationOptions>

      <!-- CoordinateSystem: result transformation system. The "Selected" variants require an id
           in CoordinateSystemID; only set those when explicitly told to. -->
      <CoordinateSystem>Absolute Rectangular</CoordinateSystem>
      <CoordinateSystemSource>None</CoordinateSystemSource> <!-- Allowed: "None", "Model", "Result" -->
      <CoordinateSystemID>-1</CoordinateSystemID> <!-- Csys id (not a 0-based index); -1 if unused. Only set when told to. -->
      <DisplayBeamResultsInLocalCoordinateSystem>1</DisplayBeamResultsInLocalCoordinateSystem> <!-- 0/1 -->
      <!-- NOTE the real (misspelled) tag name: "Pojected", missing an "r". -->
      <DisplayShellResultsInPojectedCoordinateSystem>0</DisplayShellResultsInPojectedCoordinateSystem> <!-- 0/1 -->
      <ElementValueOptions>
        <ElementValue>0</ElementValue> <!-- 0/1 -->
        <ElementCriterion>Average</ElementCriterion>
      </ElementValueOptions>
      <ComplexComponent>Amplitude</ComplexComponent> <!-- e.g. "Real", "Imaginary", "Amplitude", "Signed Amplitude", "At Phase Angle" -->
      <ComplexPhaseAngle>0.0</ComplexPhaseAngle> <!-- Used when ComplexComponent is "At Phase Angle" -->
      <ComplexStartPhaseAngle>0.0</ComplexStartPhaseAngle>
      <ComplexEndPhaseAngle>360.0</ComplexEndPhaseAngle>
      <ComplexPhaseAngleIncrement>1.0</ComplexPhaseAngleIncrement>
      <ComplexMaxOverPhaseMethod>Analytical</ComplexMaxOverPhaseMethod> <!-- Allowed: "Sweep", "Analytical" -->
      <AbsoluteValue>0</AbsoluteValue> <!-- 0/1 -->
      <ResultScale>1.0</ResultScale>
      <Unit>StressNewtonPerSquareMilliMeter</Unit> <!-- Result unit name from the result listing -->
      <CalculateBeamStressesStrainsFromForces>0</CalculateBeamStressesStrainsFromForces> <!-- 0/1 -->
      <BeamStressesStrainsFillets>0</BeamStressesStrainsFillets> <!-- 0/1 -->
      <BeamStressesStrainsFilletRadius>0.5</BeamStressesStrainsFilletRadius>
      <AcousticWeighting>None</AcousticWeighting> <!-- Allowed: "None", "A", "B", "C", "D", "AB", "BC" -->
    </ResultOptions>

    <!-- CrossSectionOptions: result shown on cross-section / cutting views -->
    <CrossSectionOptions>
      <LockRotation>1</LockRotation> <!-- 0/1 -->
      <LoadCase>0</LoadCase>
      <Iteration>0</Iteration>
      <Quantity>Stress</Quantity>
      <Component>Von-Mises</Component>
      <ElementValueOptions>
        <ElementValue>0</ElementValue> <!-- 0/1 -->
        <ElementCriterion>Average</ElementCriterion>
      </ElementValueOptions>
      <ComplexOption>Amplitude</ComplexOption>
      <ComplexPhaseAngle>0.0</ComplexPhaseAngle>
      <AbsoluteValue>0</AbsoluteValue> <!-- 0/1 -->
      <ResultScale>1.0</ResultScale>
      <Unit>StressNewtonPerSquareMilliMeter</Unit>
      <Fillets>1</Fillets> <!-- 0/1 -->
      <FilletRadius>0.5</FilletRadius>
      <BeamElement>0</BeamElement>
      <BeamEnd>Fore</BeamEnd>
    </CrossSectionOptions>

    <!-- DeformationOptions: displaced/deformed model display -->
    <DeformationOptions>
      <ShowDeformation>1</ShowDeformation> <!-- 0/1 -->
      <SameLoadCaseIterationForColorAndDeformation>1</SameLoadCaseIterationForColorAndDeformation> <!-- 0/1 -->
      <ShowUndeformedModel>0</ShowUndeformedModel> <!-- 0/1 -->
      <DeformShellElementsByNormalComponent>0</DeformShellElementsByNormalComponent> <!-- 0/1 -->
      <!-- The deformation result record (this element is named ResultOptions, not DeformOptions) -->
      <ResultOptions>
        <LoadCase>0</LoadCase>
        <Iteration>0</Iteration>
        <SubIteration>-1</SubIteration>
        <Result>[Displacement][Nodal]</Result>
        <Component>Magnitude</Component>
        <ComplexOption>Amplitude</ComplexOption>
        <ComplexPhaseAngle>0.0</ComplexPhaseAngle>
      </ResultOptions>
      <ScaleOptions>
        <DeformationScaleType>% Model</DeformationScaleType> <!-- "% Model" (use ModelPercentScaleValue) or "Absolute" (use AbsoluteScaleValue) -->
        <AbsoluteScaleValue>1.0</AbsoluteScaleValue>
        <ModelPercentScaleValue>10.0</ModelPercentScaleValue>
      </ScaleOptions>
      <ReferenceDeformationOptions>
        <DeformWith>0</DeformWith>
      </ReferenceDeformationOptions>
    </DeformationOptions>


    <!-- DisplayOnOptions: where graphics are rendered -->
    <DisplayOnOptions>
      <DisplayOn>Free Faces</DisplayOn> <!-- Allowed: "Free Faces", "Volume", "Cutting Plane" -->
      <ClippingOptions>
        <ShowModelOutline>0</ShowModelOutline> <!-- 0/1 -->
        <ShowClippedModelGhost>0</ShowClippedModelGhost> <!-- 0/1 -->
        <ClippingValue>1.021338</ClippingValue>
        <ClippingSide>Positive</ClippingSide> <!-- Allowed: "Positive", "Negative", "Both" -->
        <CutPlane>X</CutPlane> <!-- Rectangular: "X","Y","Z" (cylindrical/spherical use other letters) -->
        <PostCoordinateSystemOptions>
          <PostCoordinateSystemType>Rectangular</PostCoordinateSystemType>
          <Orientation>
            <X_Vector>
              <i>1.0</i>
              <j>0.0</j>
              <k>0.0</k>
            </X_Vector>
            <Y_Vector>
              <i>0.0</i>
              <j>1.0</j>
              <k>0.0</k>
            </Y_Vector>
            <Z_Vector>
              <i>0.0</i>
              <j>0.0</j>
              <k>1.0</k>
            </Z_Vector>
          </Orientation>
          <Origin>
            <i>0.0</i>
            <j>0.0</j>
            <k>0.0</k>
          </Origin>
        </PostCoordinateSystemOptions>
      </ClippingOptions>
    </DisplayOnOptions>

    <!-- HeaderOptions: legend header text block -->
    <HeaderOptions>
      <ShowHeader>Automatic</ShowHeader> <!-- Allowed: "None", "Automatic", "Customized" -->
      <!-- CustomHeaders: each HeaderLineN has TokenCount and TokenN children. Token values must
           come from the legend-header token set, e.g.: "Solution", "Loadcase", "Iteration",
           "Result", "Combination", "Component", "Ply Id And Layer", "Beam Section",
           "Shell Section", "Cross Section Beam Info", "Formula", "Unit", "Scale", "CSYS",
           "Deformation", "Complex", "Absolute Value", "Model Summary", "User Text". -->
      <CustomHeaders>
        <CustomHeaderLineCount>6</CustomHeaderLineCount>
        <HeaderLine0>
          <TokenCount>1</TokenCount>
          <Token0>Solution</Token0>
        </HeaderLine0>
        <HeaderLine1>
          <TokenCount>2</TokenCount>
          <Token0>Loadcase</Token0>
          <Token1>Iteration</Token1>
        </HeaderLine1>
        <HeaderLine2>
          <TokenCount>4</TokenCount>
          <Token0>Result</Token0>
          <Token1>Combination</Token1>
          <Token2>Component</Token2>
          <Token3>Ply Id And Layer</Token3>
        </HeaderLine2>
        <HeaderLine3>
          <TokenCount>2</TokenCount>
          <Token0>Beam Section</Token0>
          <Token1>Shell Section</Token1>
        </HeaderLine3>
        <HeaderLine4>
          <TokenCount>1</TokenCount>
          <Token0>Cross Section Beam Info</Token0>
        </HeaderLine4>
        <HeaderLine5>
          <TokenCount>1</TokenCount>
          <Token0>Formula</Token0>
        </HeaderLine5>
      </CustomHeaders>
    </HeaderOptions>

    <!-- ColorbarOptions: spectrum / colorbar configuration -->
    <ColorbarOptions>
      <ShowColorbar>1</ShowColorbar> <!-- 0/1 -->
      <Spectrum>Structural</Spectrum> <!-- Allowed: "Structural", "Thermal", "Grayscale", "Stoplight" -->
      <InvertSpectrum>0</InvertSpectrum> <!-- 0/1 -->
      <SpectrumScale>Automatic</SpectrumScale> <!-- Allowed: "Automatic", "Linear", "Logarithmic" -->
      <Spacing>Equally Spaced</Spacing> <!-- Allowed: "Equally Spaced", "Round Off", "Level Increment" -->
      <NumLevels>12</NumLevels>
      <MinMaxCriterion>Displayed</MinMaxCriterion> <!-- Allowed: "Result", "Displayed", "Specified", "Combined Viewport Result", "Combined Viewport Displayed" -->
      <MinimumValue>0.041133</MinimumValue>
      <MaximumValue>13.896500</MaximumValue>
      <OverflowColor>87</OverflowColor> <!-- Color index [1..216] -->
      <UnderflowColor>173</UnderflowColor> <!-- Color index [1..216] -->
      <Position>Left</Position> <!-- Allowed: "Left", "Right", "None" -->
      <OverflowDisplayStyle>None</OverflowDisplayStyle> <!-- Allowed: "None", "Shaded", "Translucent", "Clipped" -->
      <UnderflowDisplayStyle>None</UnderflowDisplayStyle> <!-- Allowed: "None", "Shaded", "Translucent", "Clipped" -->
      <OverwriteValue>0</OverwriteValue> <!-- 0/1 -->
      <OverwriteColor>0</OverwriteColor> <!-- Color index [1..216], 0 if unused -->
      <HideColorBarUnits>0</HideColorBarUnits> <!-- 0/1 -->
    </ColorbarOptions>

    <!-- EdgefaceDisplayOptions: edge/face styling for deformed (Primary) and undeformed model -->
    <EdgefaceDisplayOptions>
      <PrimaryOptions>
        <EdgeStyle>External</EdgeStyle> <!-- Allowed: "External", "Feature", "Wireframe", "None", "Polygon Edge" -->
        <EdgeColor>130</EdgeColor> <!-- Color index [1..216] -->
        <FaceStyle>Fill</FaceStyle> <!-- Primary face style allowed: "Fill", "NoFill" -->
        <FaceColor>87</FaceColor> <!-- Color index [1..216] -->
      </PrimaryOptions>
      <UndeformedOptions>
        <EdgeStyle>Feature</EdgeStyle> <!-- Allowed: "External", "Feature", "Wireframe", "None", "Polygon Edge" -->
        <EdgeColor>130</EdgeColor> <!-- Color index [1..216] -->
        <FaceStyle>Translucent</FaceStyle> <!-- Undeformed face style allowed: "Opaque", "Translucent", "None" -->
        <FaceColor>87</FaceColor> <!-- Color index [1..216] -->
      </UndeformedOptions>
    </EdgefaceDisplayOptions>

    <!-- TextOptions: annotation text color, font sizing, numeric format -->
    <TextOptions>
      <TextColor>213</TextColor> <!-- Color index [1..216] -->
      <FontSizeOptions>
        <FontAutoSize>1</FontAutoSize> <!-- 0/1 -->
        <FontScale>1.0</FontScale>
      </FontSizeOptions>
      <NumberFormatOptions>
        <Format>Automatic</Format> <!-- Allowed: "Automatic", "Fixed Point", "Scientific" -->
        <DecimalPlaces>4</DecimalPlaces>
      </NumberFormatOptions>
    </TextOptions>

    <!-- LegendBoxDispOptions: legend box styling -->
    <LegendBoxDispOptions>
      <DisplayOptions>
        <TextAndLeaderColor>1</TextAndLeaderColor> <!-- Color index [1..216] -->
        <TextAlignment>0</TextAlignment>
        <BoxFillColor>1</BoxFillColor> <!-- Color index [1..216] -->
        <ShowBoxBorder>0</ShowBoxBorder> <!-- 0/1 -->
        <BoxFill>0</BoxFill> <!-- 0/1 -->
        <BoxTranslucency>0</BoxTranslucency> <!-- 0/1 -->
      </DisplayOptions>
    </LegendBoxDispOptions>

    <!-- MinMarkerOptions / MaxMarkerOptions: minimum/maximum value markers on the model -->
    <MinMarkerOptions>
      <ShowMarker>0</ShowMarker> <!-- 0/1 -->
      <ValueType>Result And Entity</ValueType> <!-- Allowed: "None", "Result And Entity", "Result", "Entity" -->
      <DisplayUnit>1</DisplayUnit> <!-- 0/1 -->
      <SecondaryData>1</SecondaryData> <!-- 0/1 -->
      <DisplayOptions>
        <BoxStyle>2</BoxStyle> <!-- Annotation box style index -->
        <TextAndLeaderColor>213</TextAndLeaderColor> <!-- Color index [1..216] -->
        <TextAlignment>0</TextAlignment>
        <BoxFillColor>1</BoxFillColor> <!-- Color index [1..216] -->
        <ShowBoxBorder>1</ShowBoxBorder> <!-- 0/1 -->
        <BoxFill>1</BoxFill> <!-- 0/1 -->
        <BoxTranslucency>0</BoxTranslucency> <!-- 0/1 -->
      </DisplayOptions>
    </MinMarkerOptions>
    <MaxMarkerOptions>
      <ShowMarker>0</ShowMarker> <!-- 0/1 -->
      <ValueType>Result And Entity</ValueType> <!-- Allowed: "None", "Result And Entity", "Result", "Entity" -->
      <DisplayUnit>1</DisplayUnit> <!-- 0/1 -->
      <SecondaryData>1</SecondaryData> <!-- 0/1 -->
      <DisplayOptions>
        <BoxStyle>2</BoxStyle> <!-- Annotation box style index -->
        <TextAndLeaderColor>213</TextAndLeaderColor> <!-- Color index [1..216] -->
        <TextAlignment>0</TextAlignment>
        <BoxFillColor>1</BoxFillColor> <!-- Color index [1..216] -->
        <ShowBoxBorder>1</ShowBoxBorder> <!-- 0/1 -->
        <BoxFill>1</BoxFill> <!-- 0/1 -->
        <BoxTranslucency>0</BoxTranslucency> <!-- 0/1 -->
      </DisplayOptions>
    </MaxMarkerOptions>


    <!-- AnimationOptions -->
    <AnimationOptions>
      <Color>1</Color> <!-- Animate color (0/1) -->
      <Deformation>1</Deformation> <!-- Animate deformation (0/1) -->
      <ResultAnimationOptions>
        <Style>Linear</Style> <!-- Allowed: "Linear", "Modal", "Forward Wave", "Backward Wave" -->
        <NumFrames>8</NumFrames>
        <SaveFramesInMemory>0</SaveFramesInMemory> <!-- 0/1 -->
        <StartPhaseAngle>0.0</StartPhaseAngle>
        <EndPhaseAngle>360.0</EndPhaseAngle>
      </ResultAnimationOptions>
      <IterationAnimationOptions>
        <StartLoadCase>0</StartLoadCase>
        <StartIteration>0</StartIteration>
        <StartSubIteration>-1</StartSubIteration>
        <EndLoadCase>1</EndLoadCase>
        <EndIteration>0</EndIteration>
        <SubEndIteration>-1</SubEndIteration>
        <IterationStep>1</IterationStep>
      </IterationAnimationOptions>
      <StreamlineAnimationOptions>
        <ShowGuides>1</ShowGuides> <!-- 0/1 -->
        <PulseSynchronization>At Seed Point</PulseSynchronization> <!-- Allowed: "Upstream", "Downstream", "At Seed Point" -->
        <ActiveRegionStartFactor>0.0</ActiveRegionStartFactor>
        <ActiveRegionEndFactor>1.0</ActiveRegionEndFactor>
        <NumIncrements>40</NumIncrements>
        <ContinuousPulse>1</ContinuousPulse> <!-- 0/1 -->
        <NumTimePeriods>10</NumTimePeriods>
        <NumFramesPerPulse>5.0</NumFramesPerPulse>
        <PulseDutyCycle>0.05</PulseDutyCycle>
      </StreamlineAnimationOptions>
      <FullCycle>0</FullCycle> <!-- 0/1 -->
      <Delay>200</Delay> <!-- Frame delay in milliseconds -->
      <VectorDisplaySizeControl>0</VectorDisplaySizeControl> <!-- 0/1 -->
    </AnimationOptions>

    <!-- Group visibility/translucency. Counts and space-separated 0/1 lists must match.
         Other element dimensionalities use Num0DGroups/Visibilities0DGroups, Num1DGroups,
         Num2DGroups, NumConnectorGroups, NumOtherGroups (and the matching translucency tags). -->
    <GroupVisibilities>
      <Num3DGroups>1</Num3DGroups>
      <Visibilities3DGroups>1</Visibilities3DGroups>
    </GroupVisibilities>
    <GroupTranslucency>
      <Num3DGroups>1</Num3DGroups>
      <TranslucencyFor3DGroups>0</TranslucencyFor3DGroups>
    </GroupTranslucency>
    <CsysGroup>
      <NumCsys>0</NumCsys>
    </CsysGroup>
  </PostView>
</NXPostProcessingTemplate>
```


Color are indexed colors. In the template, where a color is necessary, you
may use one of the colors below. In rare cases, a user may have customized 
their color palette. If they complain that you are not using the colors they
asked for, ask them if they have a custom CDF file. If they provide a custom
CDF file, read the colors from there. The format of a CDF file is similar, but
the color ID is not normally present in a CDF file, so you'll have to skip
over the header until you start recognizing the name r g b extra columns and
start counting.

Default 216 color table:

ID  Name                              R          G          B         Extra
  0 Background                        1.0000000  1.0000000  1.0000000
  1 White                             1.0000000  1.0000000  1.0000000
  2 Pale Lemon                        1.0000000  0.9803922  0.7490196
  3 Medium Lemon                      1.0000000  0.9607843  0.6549020 39
  4 Strong Lemon                      1.0000000  0.9490196  0.5137255
  5 Medium Yellow                     1.0000000  0.9411765  0.4941176
  6 Yellow                            1.0000000  1.0000000  0.0000000
  7 Pale Sky                          0.8823529  0.9607843  1.0000000
  8 Pale Green                        0.8431373  1.0000000  0.7803922 53
  9 Pale Lime                         0.8000000  1.0000000  0.6000000 52
 10 Medium Lime                       0.8000000  1.0000000  0.4000000
 11 Lime                              0.8000000  1.0000000  0.2000000
 12 Deep Lemon                        1.0000000  0.9098039  0.3843137
 13 Pale Cyan                         0.7411765  1.0000000  1.0000000 55
 14 Pale Emerald                      0.6000000  1.0000000  0.7921569 54
 15 Powder Gray                       0.9490196  0.9490196  0.9490196
 16 Pale Spring                       0.8666667  0.9215686  0.8392157
 17 Pale Yellow                       1.0000000  0.9411765  0.6627451 51
 18 Strong Pistachio                  0.8627451  0.8901961  0.6039216
 19 Medium Cyan                       0.6000000  1.0000000  1.0000000
 20 Medium Emerald                    0.4470588  1.0000000  0.8039216
 21 Pale Aqua                         0.8627451  0.9372549  0.9294118
 22 Pale Mint                         0.8156863  0.9098039  0.8352941
 23 Pale Khaki                        0.7568627  0.7568627  0.5647059 28
 24 Deep Pistachio                    0.8117647  0.8705882  0.4196078
 25 Strong Cyan                       0.3058824  1.0000000  1.0000000
 26 Medium Aqua                       0.7529412  0.8901961  0.8745098 43
 27 Pale Turquoise                    0.6862745  0.8588235  0.8588235 31
 28 Medium Spring                     0.7960784  0.9019608  0.7843137 41
 29 Strong Green                      0.2000000  1.0000000  0.2000000
 30 Strong Lime                       0.7372549  0.9294118  0.2039216
 31 Cyan                              0.0000000  1.0000000  1.0000000
 32 Medium Sky                        0.7647059  0.8784314  0.9450980 44
 33 Strong Aqua                       0.6235294  0.8352941  0.8235294
 34 Medium Mint                       0.7058824  0.8588235  0.7450980 42
 35 Medium Green                      0.6000000  1.0000000  0.4000000
 36 Green                             0.0000000  1.0000000  0.0000000
 37 Pale Pink                         0.9764706  0.8431373  0.9058824
 38 Pale Salmon                       1.0000000  0.8431373  0.8235294
 39 Pale Orange                       1.0000000  0.8000000  0.6000000 50
 40 Medium Peach                      0.9843137  0.7803922  0.6274510 38
 41 Medium Orange                     1.0000000  0.7529412  0.2980392
 42 Deep Yellow                       1.0000000  0.7921569  0.0000000
 43 Pale Lavender                     0.7921569  0.7803922  0.8941176
 44 Light Gray                        0.8000000  0.8000000  0.8000000
 45 Pale Brown                        0.9411765  0.8000000  0.5254902 59
 46 Strong Yellow                     1.0000000  0.8627451  0.2274510
 47 Medium Olive                      0.8000000  0.8000000  0.2000000
 48 Pale Olive                        0.9019608  0.8588235  0.2862745 15
 49 Pale Ice                          0.8117647  0.8431373  0.9098039
 50 Ash Gray                          0.8745098  0.8745098  0.8745098
 51 Pale Pistachio                    0.9098039  0.9254902  0.8470588
 52 Pale Gold                         0.8901961  0.8274510  0.6156863 27
 53 Medium Gold                       0.8823529  0.7607843  0.2823529 3
 54 Pale Leaf                         0.6196078  0.7921569  0.2392157
 55 Medium Cornflower                 0.4000000  0.8000000  1.0000000 16
 56 Deep Aqua                         0.3764706  0.8039216  0.8235294
 57 Pale Pine                         0.7647059  0.8823529  0.7450980 29
 58 Medium Pistachio                  0.8901961  0.9098039  0.5254902 40
 59 Deep Lime                         0.6627451  0.8901961  0.0000000
 60 Deep Green                        0.4000000  0.8000000  0.0000000
 61 Pale Cornflower                   0.6000000  0.8000000  1.0000000 56
 62 Deep Cyan                         0.0000000  0.8117647  0.8117647
 63 Strong Spring                     0.6705882  0.8392157  0.6274510
 64 Deep Spring                       0.6117647  0.8156863  0.4941176
 65 Medium Pine                       0.6274510  0.8313725  0.6588235 5
 66 Strong Pine                       0.5333333  0.7333333  0.4392157
 67 Strong Sky                        0.5960784  0.7882353  0.9215686
 68 Strong Mint                       0.6039216  0.8117647  0.6588235
 69 Strong Emerald                    0.0000000  0.8039216  0.5254902
 70 Pale Sea                          0.7176471  0.8117647  0.7647059 30
 71 Pale Forest                       0.3921569  0.7529412  0.3294118 17
 72 Deep Mint                         0.4705882  0.7529412  0.5490196
 73 Pale Magenta                      1.0000000  0.6627451  1.0000000 48
 74 Pale Peach                        0.9607843  0.8313725  0.7254902
 75 Strong Salmon                     1.0000000  0.6000000  0.6000000
 76 Pale Carrot                       1.0000000  0.6235294  0.2509804 14
 77 Strong Orange                     1.0000000  0.6000000  0.2000000
 78 Orange                            1.0000000  0.6000000  0.0000000
 79 Medium Ice                        0.7019608  0.7647059  0.8784314 45
 80 Pale Stone                        0.8666667  0.8549020  0.7882353 35
 81 Pale Maroon                       0.8117647  0.6039216  0.6117647 25
 82 Medium Coral                      0.7882353  0.5921569  0.3960784 2
 83 Medium Brown                      0.8000000  0.6000000  0.2000000
 84 Strong Gold                       0.6117647  0.5568627  0.3803922
 85 Pale Midnight                     0.6039216  0.7294118  0.8392157 33
 86 Strong Lavender                   0.5921569  0.5843137  0.7725490
 87 Silver Gray                       0.6000000  0.6000000  0.6000000
 88 Medium Stone                      0.7686275  0.7490196  0.6470588 11
 89 Strong Olive                      0.6078431  0.5647059  0.0000000
 90 Medium Khaki                      0.6980392  0.6941176  0.4039216 4
 91 Pale Blue                         0.5372549  0.7137255  1.0000000 57
 92 Deep Ice                          0.3333333  0.6000000  0.8666667
 93 Medium Sea                        0.5176471  0.6784314  0.6078431 6
 94 Pale Moss                         0.2156863  0.6666667  0.5333333 18
 95 Strong Khaki                      0.5529412  0.5803922  0.2039216
 96 Medium Leaf                       0.4627451  0.6235294  0.1647059
 97 Strong Cornflower                 0.2000000  0.6000000  1.0000000
 98 Medium Azure                      0.0000000  0.6156863  0.8509804
 99 Pale Teal                         0.2274510  0.5450980  0.5607843 19
100 Medium Moss                       0.0000000  0.5882353  0.4352941
101 Medium Forest                     0.2000000  0.6000000  0.2000000
102 Strong Sea                        0.2823529  0.5647059  0.4156863
103 Cornflower                        0.0000000  0.6000000  1.0000000
104 Pale Azure                        0.0000000  0.6901961  0.9411765 20
105 Medium Teal                       0.0000000  0.6000000  0.6000000
106 Deep Emerald                      0.0000000  0.6745098  0.3960784
107 Deep Pine                         0.3686275  0.5215686  0.2470588
108 Emerald                           0.0000000  0.6000000  0.0000000
109 Medium Pink                       0.9607843  0.7490196  0.8470588 36
110 Medium Salmon                     1.0000000  0.7019608  0.7058824 37
111 Pale Red                          1.0000000  0.5647059  0.5647059 49
112 Medium Red                        1.0000000  0.4000000  0.4000000
113 Deep Peach                        0.9647059  0.6274510  0.4078431
114 Deep Orange                       1.0000000  0.4000000  0.0000000
115 Pale Purple                       0.7098039  0.7098039  1.0000000 58
116 Pale Fuchsia                      0.8274510  0.6235294  0.7843137 24
117 Pale Plum                         0.7333333  0.4666667  0.6000000 12
118 Strong Peach                      0.9686275  0.6862745  0.5176471
119 Medium Carrot                     0.9019608  0.4823529  0.0705882
120 Strong Coral                      0.7254902  0.4509804  0.3176471
121 Pale Steel                        0.7529412  0.8235294  0.8823529 32
122 Medium Lavender                   0.6784314  0.6588235  0.8313725 46
123 Smoke Gray                        0.6941176  0.6941176  0.6941176
124 Medium Maroon                     0.6000000  0.4000000  0.4000000 1
125 Brown                             0.6000000  0.4000000  0.2000000
126 Deep Olive                        0.4352941  0.4078431  0.0000000
127 Medium Purple                     0.4470588  0.4156863  1.0000000
128 Pale Violet                       0.4000000  0.4000000  0.8000000 22
129 Medium Steel                      0.6117647  0.6588235  0.6705882 8
130 Granite Gray                      0.4000000  0.4000000  0.4000000
131 Deep Khaki                        0.3686275  0.3686275  0.2352941
132 Deep Leaf                         0.3058824  0.3803922  0.0000000
133 Medium Turquoise                  0.5098039  0.7137255  0.7686275 7
134 Medium Royal                      0.3019608  0.4274510  0.7019608
135 Strong Steel                      0.2705882  0.3803922  0.5137255
136 Strong Moss                       0.0000000  0.3450980  0.1568627
137 Deep Sea                          0.2000000  0.4000000  0.2000000
138 Strong Leaf                       0.2901961  0.4509804  0.1058824
139 Medium Blue                       0.2549020  0.3764706  1.0000000
140 Strong Turquoise                  0.2588235  0.4823529  0.5411765
141 Strong Azure                      0.0000000  0.4000000  0.6000000
142 Strong Teal                       0.0000000  0.4000000  0.4000000
143 Deep Forest                       0.1098039  0.2862745  0.0117647
144 Strong Forest                     0.0000000  0.4000000  0.0000000
145 Medium Magenta                    1.0000000  0.4274510  1.0000000
146 Strong Magenta                    1.0000000  0.2274510  0.8823529
147 Deep Red                          1.0000000  0.1882353  0.1882353
148 Deep Salmon                       1.0000000  0.5450980  0.5450980
149 Pale Crimson                      0.9411765  0.2627451  0.2078431 13
150 Deep Pink                         0.9176471  0.4313725  0.6470588
151 Pale Tan                          0.8274510  0.7411765  0.6705882
152 Deep Magenta                      0.8000000  0.2000000  0.8000000
153 Strong Tan                        0.7137255  0.5725490  0.4313725
154 Deep Tan                          0.7019608  0.5058824  0.3647059
155 Medium Crimson                    0.8000000  0.2000000  0.2000000
156 Deep Gold                         0.6117647  0.4549020  0.1607843
157 Pale Coral                        0.8196078  0.7019608  0.6196078 26
158 Pale Indigo                       0.6509804  0.6392157  0.7686275 34
159 Medium Gray                       0.4901961  0.4901961  0.4901961
160 Strong Plum                       0.5333333  0.2666667  0.4000000
161 Strong Maroon                     0.5333333  0.2666667  0.2666667
162 Deep Brown                        0.4000000  0.2000000  0.0000000
163 Medium Tan                        0.7764706  0.6588235  0.5529412 47
164 Purple                            0.4000000  0.2000000  0.8000000
165 Medium Indigo                     0.4627451  0.4156863  0.5882353 10
166 Medium Violet                     0.3176471  0.1215686  0.4980392
167 Deep Carrot                       0.4274510  0.1764706  0.0392157
168 Deep Stone                        0.2862745  0.2705882  0.1803922
169 Strong Blue                       0.2000000  0.2000000  1.0000000
170 Strong Ice                        0.5960784  0.6901961  0.8470588
171 Medium Midnight                   0.5215686  0.6274510  0.6862745 9
172 Deep Indigo                       0.2431373  0.2000000  0.3294118
173 Dark Gray                         0.2000000  0.2000000  0.2000000
174 Deep Umber                        0.1607843  0.1411765  0.1333333
175 Deep Cornflower                   0.0000000  0.2666667  1.0000000
176 Pale Royal                        0.3098039  0.4784314  0.6666667 21
177 Deep Turquoise                    0.1254902  0.3450980  0.4039216
178 Deep Azure                        0.0000000  0.2470588  0.3686275
179 Deep Teal                         0.0000000  0.2784314  0.2509804
180 Deep Moss                         0.0000000  0.2274510  0.0000000
181 Magenta                           1.0000000  0.0000000  1.0000000
182 Strong Red                        1.0000000  0.3176471  0.3176471
183 Medium Fuchsia                    0.6941176  0.4588235  0.5764706 0
184 Strong Fuchsia                    0.5058824  0.2549020  0.4039216
185 Strong Pink                       0.9333333  0.5843137  0.7411765
186 Red                               1.0000000  0.0000000  0.0000000
187 Pale Umber                        0.5254902  0.4509804  0.3803922 23
188 Medium Plum                       0.7529412  0.1882353  0.6431373
189 Strong Brown                      0.6431373  0.4000000  0.0000000
190 Strong Carrot                     0.5647059  0.3137255  0.0274510
191 Strong Stone                      0.5450980  0.5254902  0.4196078
192 Deep Coral                        0.6745098  0.2156863  0.0745098
193 Deep Lavender                     0.4784314  0.4509804  0.7098039
194 Strong Indigo                     0.3607843  0.2862745  0.5019608
195 Medium Umber                      0.3725490  0.3137255  0.2705882
196 Strong Umber                      0.2549020  0.2156863  0.1960784
197 Deep Crimson                      0.4941176  0.0000000  0.0000000
198 Strong Crimson                    0.6000000  0.0000000  0.0000000
199 Strong Purple                     0.4000000  0.0000000  1.0000000
200 Deep Purple                       0.4000000  0.0000000  0.8000000
201 Iron Gray                         0.2980392  0.2980392  0.2980392
202 Deep Fuchsia                      0.2588235  0.0980392  0.2588235
203 Deep Plum                         0.3960784  0.0000000  0.2666667
204 Deep Maroon                       0.4000000  0.0000000  0.0000000
205 Deep Sky                          0.3372549  0.6941176  1.0000000
206 Strong Royal                      0.0000000  0.2235294  0.6039216
207 Strong Midnight                   0.1647059  0.2862745  0.4470588
208 Strong Violet                     0.2235294  0.0666667  0.3333333
209 Deep Violet                       0.1411765  0.0000000  0.1411765
210 Charcoal Gray                     0.0470588  0.0470588  0.0470588
211 Blue                              0.0000000  0.0000000  1.0000000
212 Deep Blue                         0.0000000  0.0000000  0.7529412
213 Deep Steel                        0.1411765  0.2509804  0.3803922
214 Deep Royal                        0.0705882  0.1568627  0.4274510
215 Deep Midnight                     0.0588235  0.1411765  0.2431373
216 Black                             0.0000000  0.0000000  0.0000000
