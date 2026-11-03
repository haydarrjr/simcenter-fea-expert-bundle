---
name: simcenter-aerostructures-load-filtering
description: Define Nodal Force Reports (NFR), configure FreeBodyLoadExtraction, author custom Python/XML/XMD Load Case Filtering modules using NXOpen.CAE.AeroStructures.Author.ABB (Lcf1dMinMax and LcfConvexHull), and solve LoadFilteringSolution to generate critical Load Case Sets in Simcenter 3D Aerostructures.
---

# Simcenter 3D Aerostructures: Nodal Force Reports & Load Case Filtering

Use this skill when extracting cross-sectional free-body loads via **Nodal Force Reports (`NFR`)**, authoring custom **Load Case Filtering (`LCF`)** modules (`.xmd`, `.xml`, `.py`), or running `NXOpen.CAE.AeroStructures.LoadFilteringSolution` to reduce large flight envelopes (e.g., multi-weight `SOL 144` subcases) into critical component-specific Load Case Sets.

Related skills:
- Master airframe workflow: [simcenter-airframe-structural-verification](../simcenter-airframe-structural-verification/SKILL.md)
- Margin of Safety & Knowledge Fusion `ExtractProperty`: [simcenter-aerostructures-margin-of-safety](../simcenter-aerostructures-margin-of-safety/SKILL.md)
- Host tool routing & evidence policy: [fea-sc3d-tool-routing](../fea-sc3d-tool-routing/SKILL.md)
- Production templates for `.xmd`, `.xml`, and `.py` LCF methods: [custom LCF templates](references/custom-lcf-templates.md)

---

## 1. Nodal Force Reports (NFR) & `FreeBodyLoadExtraction`

### Station-Curve Free-Body Architecture
To monitor internal section loads (Shear, Bending Moment, Torque, Axial Force) along primary airframe load paths, **Nodal Force Reports (`NXOpen.CAE.CaeFreeBody`)** are created at stations along structural guide curves (`GPFORCE` output must be enabled in the Nastran solution):
- **Wing Stations (`12` NFRs)**: `NFR_Wing_curve_Grid Point_1` .. `NFR_Wing_curve_Grid Point_12` (root-to-tip spanwise cuts).
- **Tail / Empennage Stations (`11` NFRs)**: `NFR_Tail_curve_Grid Point_1` .. `NFR_Tail_curve_Grid Point_11`.
- **Fuselage Stations (`26` NFRs)**: `NFR_Fuselage_curve_Grid Point_1` .. `NFR_Fuselage_curve_Grid Point_26` (nose-to-tail longitudinal cuts).

Each NFR defines:
- **Target Elements**: Elements on one side of the station cut plane.
- **Interface Nodes**: Grid points lying on the station cut boundary.
- **Reference Point & Coordinate System**: The station centroid and local axis system about which forces and moments are summed.

### `NXOpen.CAE.AeroStructures.FreeBodyLoadExtraction` API
In Simcenter 3D Aerostructures, NFR loads are extracted into Load Case Filtering or Margin of Safety calculations via `NXOpen.CAE.AeroStructures.FreeBodyLoadExtraction` (inherits from `LoadExtractionValue`):
- `GetFreeBody()` / `SetFreeBody(freeBody)`: Binds the extraction parameter to a specific `NXOpen.CAE.CaeFreeBody` (`NFR`) object in the `.sim`.
- `GetResult()` / `SetResult(result)`:
  - `FreeBodyLoadExtraction.Result.Force`
  - `FreeBodyLoadExtraction.Result.Moment`
  - `FreeBodyLoadExtraction.Result.None`
- `GetComponent()` / `SetComponent(component)`:
  - `Component.X`, `Component.Y`, `Component.Z`
  - `Component.PlanarMagnitudeXY`, `Component.PlanarMagnitudeXZ`, `Component.PlanarMagnitudeZY`
  - `Component.Magnitude`, `Component.None`
- `GetMatrixManip()` / `SetMatrixManip(manip)`: Applies coordinate transformation (`SetCoordinateSystem`), scaling (`SetFactor`), or filtering (`SetFilterConversion`).

### Critical Coordinate System Rule for NFR Extraction
When extracting `free_body_load_extraction` parameters in custom LCF methods:
- Keep the extraction coordinate system set to **`NONE` (Global CSYS)** in the `FreeBodyLoadExtraction` parameter definition if NFR local orientation rotation exhibits an offset, and either extract consistent global components (e.g., `Z` vertical shear force vs. `X` bending moment for a wing, or `Y` vs. `Z` for fuselage stations) or perform the local 3D vector projection inside the Python evaluation script using the station local triad (`X_local`, `Y_local`, `Z_local`).

---

## 2. Custom Load Case Filtering Module Architecture (`.xmd` / `.xml` / `.py`)

Simcenter 3D Aerostructures loads custom Load Case Filtering and Margin of Safety modules at startup from directories listed in the environment variable:
```
UGII_AEROSTRUCTURES_MODULE_PATH=<path_to_CustomLoadCaseFiltering_folder>
```
Multiple directories can be separated by `;` on Windows.

### How Simcenter 3D Invokes Custom Python Methods
The host callback script `$UGII_BASE_DIR/SIMULATION/aerostructures/scripts/CaeSim_AeroStruct_PyScriptCallback.py` (`# nx: threaded`) registers each Python method with `NXOpen.CAE.AeroStructures.Author.MethodLibrary`:
- `RegisterEvaluateScript(theClassName, 1)` $\rightarrow$ calls `module.evaluate(context)` where `context` is `NXOpen.CAE.AeroStructures.Author.CalculationContext`.
- `RegisterMultiEvaluateScript(theClassName, 1)` $\rightarrow$ calls `module.evaluate(context)` where `context` is `MultiCalculationContext`.
- `RegisterPostProcessingScript(theClassName, 1)` $\rightarrow$ calls `module.post_process(marginCalculation)`.

### Required 3-File Module Structure
1. **Module Descriptor (`<ModuleName>.xmd`)**:
   - Declares `<module id="..." path=".">` and maps each `<method id="..." path="<MethodFile>.xml"/>`.
2. **Method Descriptor (`<MethodId>.xml`)**:
   - Root element `<method id="..." version="1" uiname="..." type="loadfiltering" category="..." script="python"author="..." description="...">`.
   - `<input>`: Declares `<parameter id="F1" type="free_body_load_extraction" measure="Force" .../>`, `<parameter id="F2" type="free_body_load_extraction" measure="Moment" .../>`, and scalar/boolean/integer filter controls (e.g., `Tolerance`, `positiveOnly`, `nbOfLoadCases`).
   - `<output>`: For `type="loadfiltering"`, must declare `<parameter id="B" uiname="Selected" type="boolean" description="Output list of boolean" indexby="lc"/>`.
3. **Python Script (`<MethodId>.py`)**:
   - Must start with `# nx: threaded` on line 1.
   - Defines `def evaluate(context):`.
   - Reads inputs via `context.GetInputTable()`, extracts load vectors across all subcases via `F1_table.GetLoadArrayPropertyValue("F1").GetValues()`, invokes `NXOpen.CAE.AeroStructures.Author.ABB`, and writes the boolean selection array `B` via `output_table.GetBooleanArrayPropertyValue("B").SetValues(B_values)`.

See [custom LCF templates](references/custom-lcf-templates.md) for the complete, verified `.xmd`, `.xml`, and `.py` implementations of `NFRCompat_1DMinMax` and `NFRCompat_FvF_ConvexHull`.

---

## 3. Standard Building Blocks (`NXOpen.CAE.AeroStructures.Author.ABB`)

Simcenter 3D provides compiled C++ Aerostructures Building Blocks (`NXOpen.CAE.AeroStructures.Author.ABB`) for Load Case Filtering:

1. **1D Min/Max Filtering (`ABB.Lcf1dMinMax`)**:
   ```python
   status = NXOpen.CAE.AeroStructures.Author.ABB.Lcf1dMinMax(
       F_values,       # list[float]: extracted load values across N load cases
       positiveOnly,   # bool: True = rank by positive maxima only; False = keep extremes on both ends
       nbOfLoadCases,  # int: target number of load cases to retain
       B_values        # list[bool]: pre-allocated [False] * N output list
   )
   ```
2. **2D Convex Hull Filtering (`ABB.LcfConvexHull`)**:
   ```python
   status = NXOpen.CAE.AeroStructures.Author.ABB.LcfConvexHull(
       F1_values,      # list[float]: primary load vector (e.g. Shear Force F) across N load cases
       F2_values,      # list[float]: secondary load vector (e.g. Bending Moment M) across N load cases
       Tolerance,      # float: relative proximity tolerance (e.g. 0.02 = 2%) to include near-boundary LCs
       B_values        # list[bool]: pre-allocated [False] * N output list
   )
   ```
   - **Physical meaning of `Tolerance`**: A load case lying slightly inside the exact geometric 2D convex hull polygon (within `Tolerance`, typically `0.02`) is also marked `True` (`Selected`) so combined multiaxial or secondary stiffness effects are not unconservatively dropped.

---

## 4. Reference Airframe Load Case Filtering Solution (`Filter_14LCs`)

In `AO_Aeroelastic.s1.sim`, the Load Case Filtering solution `Filter_14LCs` evaluates **49 calculations** (`NFRCompat_FvF_ConvexHull`, `Tolerance = 0.02 [in]`) across all **14 multi-weight subcases**:
- **Wing (`12` calculations)**: `Wing_Force_vs_Moment_Point1` .. `Wing_Force_vs_Moment_Point12` (`F1 = NFR_Wing_curve_Grid Point_i, Force, Z`; `F2 = NFR_Wing_curve_Grid Point_i, Moment, X`) $\rightarrow$ exports **`LCset_Wing.xlsx` (`12` critical LCs retained; drops `LC_04_pull_up_0.34_SL` and `LC_16_Cruise`)**.
- **Tail (`11` calculations)**: `Tail_Force_vs_Moment_Point1` .. `Tail_Force_vs_Moment_Point11` (`F1 = NFR_Tail_curve_Grid Point_i, Force, Z`; `F2 = NFR_Tail_curve_Grid Point_i, Moment, X`) $\rightarrow$ exports **`LC_set_Tail.xlsx` (`11` critical LCs retained; drops `LC_03_pull_up_0.17_SL`, `LC_04_pull_up_0.34_SL`, and `LC_16_Cruise`)**.
- **Fuselage (`26` calculations)**: `Fuselage_Force_vs_Moment_Point1` .. `Fuselage_Force_vs_Moment_Point26` (`F1 = NFR_Fuselage_curve_Grid Point_i, Force, Y/Z`; `F2 = NFR_Fuselage_curve_Grid Point_i, Moment, X`) $\rightarrow$ exports **`LCset_Fuselage.xlsx` (`14` critical LCs retained)**.

### NXOpen API for Managing Load Case Filtering Solutions
- Collection: `workSimPart.AeroStructManager.LoadFilteringSolutionCollection`
- Classes:
  - `NXOpen.CAE.AeroStructures.LoadFilteringSolution` (`CreateLoadFilteringCalculationBuilder`, `Solve`, `CreateLoadCaseSetBuilder`)
  - `NXOpen.CAE.AeroStructures.LoadFilteringSolutionBuilder` (`ReferenceSolution`, `Name`, `Description`)
  - `NXOpen.CAE.AeroStructures.LoadFilteringCalculation` (`GetInputTable`, `GetResultParameters`)
- Archive Forensics: Solving `Filter_14LCs` writes `<sim_name>_<solution_name>_o_pf.msz` (a standard ZIP archive containing `<CalculationName>.mslog` files with exact extracted `F1`/`F2` values per load case and `Selected = TRUE/FALSE` outputs).
