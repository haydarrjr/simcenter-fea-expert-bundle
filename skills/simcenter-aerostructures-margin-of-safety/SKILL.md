---
name: simcenter-aerostructures-margin-of-safety
description: Configure, parameterize, solve, and audit Simcenter 3D Aerostructures Margin of Safety (MarginSolution and MarginCalculation) using associative Knowledge Fusion ExtractProperty rules, standard panel/column buckling and stress allowable methods, .msz/.mslog forensic analysis, and automated Word Report Writer templates.
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Simcenter 3D Aerostructures: Margin of Safety & Associative Knowledge Fusion (`ExtractProperty`)

Use this skill when creating, parameterizing, diagnosing, or reporting **Margin of Safety (`MoS`)** solutions (`NXOpen.CAE.AeroStructures.MarginSolution`) in Simcenter 3D Aerostructures.

Related skills:
- Master airframe workflow: [simcenter-airframe-structural-verification](../simcenter-airframe-structural-verification/SKILL.md)
- Nodal Force Reports & Load Case Filtering: [simcenter-aerostructures-load-filtering](../simcenter-aerostructures-load-filtering/SKILL.md)
- Host tool routing & evidence policy: [fea-sc3d-tool-routing](../fea-sc3d-tool-routing/SKILL.md)
- Complete KF `ExtractProperty` syntax, XML method schemas & `.msz` forensic parser: [KF ExtractProperty and MS methods reference](references/kf-extractproperty-and-ms-methods.md)

---

## 1. Associative Knowledge Fusion (`ExtractProperty`) Parametrization

Simcenter 3D Aerostructures provides a dedicated Knowledge Fusion (KF) host library (`$UGII_BASE_DIR/SIMULATION/aerostructures/dfa/nx_cae/hostlib/nx_cae_aero_structures_scalar_input.dfa`) so that scalar calculation inputs ($t, b, a, r, E, \nu, F_y, A, h$) are **associatively extracted from the FE mesh, polygon geometry, beam cross-sections, and materials** instead of being hardcoded numbers.

### Host Library Functions (`nx_cae_aero_structures_scalar_input.dfa`)
```
Defun: materialProperty(string $matName; string $propName; number $temp)
Defun: sectionProperty(string $sectName; string $propName)
Defun: ExtractProperty(string $sourceName; string $extractionType; list $extractionParams)
```

### Canonical `ExtractProperty` Expressions by Physical Quantity

| Physical Quantity | Named Source (`$sourceName`) | Extraction Type (`$extractionType`) | Parameters (`$extractionParams`) | Exact KF Expression Formula |
|---|---|---|---|---|
| **Panel Thickness $t$** | `"Polygon Face"` | `"MIN_THICKNESS"` | `{}` | `ExtractProperty("Polygon Face", "MIN_THICKNESS", {})` |
| **Loaded Edge Width $b$** | `"Loaded_Edge"` | `"TOTAL_LENGTH"` | `{}` | `ExtractProperty("Loaded_Edge", "TOTAL_LENGTH", {})` |
| **Unloaded Edge Length $a$** | `"Unloaded_Edge"` | `"TOTAL_LENGTH"` | `{}` | `ExtractProperty("Unloaded_Edge", "TOTAL_LENGTH", {})` |
| **Projected Length ($X$ or $Y$)** | `"Polygon Face"` | `"PROJ_LENGTH"` | `{"<csys_id> - csys", "X"}` | `ExtractProperty("Polygon Face", "PROJ_LENGTH", {"171115 - csys", "X"})` |
| **Curvature Radius $r$** | `"Loaded_Edge"` | `"AVG_CURVRAD"` | `{}` | `ExtractProperty("Loaded_Edge", "AVG_CURVRAD", {})` |
| **Young's Modulus $E(T)$** | `"Polygon Face"` or `"1D Mesh"` | `"MATERIAL_PROP"` | `{"YoungsModulusConstant", "71.330000[F]"}` | `ExtractProperty("Polygon Face", "MATERIAL_PROP", {"YoungsModulusConstant", "71.330000[F]"})` |
| **Poisson's Ratio $\nu(T)$** | `"Polygon Face"` | `"MATERIAL_PROP"` | `{"PoissonsRatioConstant", "71.330000[F]"}` | `ExtractProperty("Polygon Face", "MATERIAL_PROP", {"PoissonsRatioConstant", "71.330000[F]"})` |
| **Yield Strength $F_y(T)$** | `"Polygon Face"`, `"Panel"`, `"1D Mesh"` | `"MATERIAL_PROP"` | `{"Yield", "71.330000[F]"}` | `ExtractProperty("Polygon Face", "MATERIAL_PROP", {"Yield", "71.330000[F]"})` |
| **1D Beam Area $A$** | `"1D Mesh"` or `"Polygon Edge"` | `"BEAM_SECTION_PROP"` | `{"Area"}` | `ExtractProperty("1D Mesh", "BEAM_SECTION_PROP", {"Area"})` |
| **1D Beam Section Height $h$** | `"1D Mesh"` | `"BEAM_SECTION_PROP"` | `{"h"}` | `ExtractProperty("1D Mesh", "BEAM_SECTION_PROP", {"h"})` |

### Why Associative `ExtractProperty` Matters
When a designer modifies a shell thickness (`PSHELL`), beam section (`PBEAML`), material assignment, or CAD surface dimension:
1. The Named Sources (`Polygon Face`, `Loaded_Edge`, `Unloaded_Edge`, `1D Mesh`) bound to each `MarginCalculation` automatically re-evaluate their `ExtractProperty(...)` KF expressions.
2. In 1D stringer/longeron/frame calculations (`MS_InterRivetBuckling_Column` or `MS_Allowable_Stress`), `ExtractProperty("1D Mesh", "BEAM_SECTION_PROP", {"Area"})` can also be used as the scaling divisor in `MatrixManip` to convert extracted 1D element `Axial` force (`lbf`) into axial stress (`psi` or `ksi`).

---

## 2. Standard Margin of Safety Methods & Airframe Component Mapping

In the reference airframe solution `MoS_14_LCs` (`1,100` calculations across `19` component families), four standard Simcenter 3D Aerostructures methods (`$UGII_BASE_DIR/SIMULATION/aerostructures/margin_solution/`) are used:

| Method ID | UI Name | Failure Mode ID | Formula | Airframe Component Families (`1,100` Calcs) |
|---|---|---|---|---|
| `MS_Allowable_Stress` | Stress allowable | `AllowableStress` | $$\text{MS} = \frac{\sigma_{\text{allow}}}{\lvert \sigma \rvert} - 1$$ | `Fuselage_Frames` (`264`), `Fuselage_Longerons` (`176`), `Fuselage_Floor` (`88`), `Nose_Frames` (`48`), `Nose_Stringers` (`16`), `Empennage_Frames` (`60`), `Empennage_Stringers` (`20`), `Wing_Spar_Caps` (`12`), `Wing_Stringer_Tension` (`55`), `Tail_Stringer_Tension` (`55`) |
| `MS_PlateBuckling_CurvedCompressive` | Plate buckling curved compressive | `panel_buckling` | $$\text{MS} = \frac{\sigma_{\text{cr,curved}}(a,b,t,r,E,\nu,n,F_y)}{-\sigma} - 1$$ | `Fuselage_Skins_Curved_Compressive` (`189`), `Nose_Panel_Curved_Compressive` (`28`) |
| `MS_PlateBuckling_FlatCompressive` | Plate buckling flat compressive | `PlateBuckling_FlatCompressive` | $$\text{MS} = \frac{\sigma_{\text{cr,flat}}(a,b,t,\text{BC},E,\nu,n,F_y)}{-\sigma} - 1$$ | `Wing_Skin_Buckling` (`16`), `Wing_Spar_Plate_Buckling` (`36`), `Tail_Skin_Buckling` (`18`) |
| `MS_InterRivetBuckling_Column` | Inter-Rivet Buckling Column | `InterRivetBuckling_Column` | $$\text{MS} = \frac{\sigma_{\text{ir}}(c,p,t_s,E,n,F_{cy},F_{07})}{-\sigma} - 1$$ | `Wing_Stringer_Buckling` (`9`), `Tail_Stringer_Buckling` (`10`) |

---

## 3. Forensic Diagnostics of `.msz` / `.mslog` Margin Archives

Solving a `MarginSolution` produces `<sim_name>_<solution_name>.msz` (a standard ZIP archive containing one `<CalculationName>.mslog` text file per calculation).

### Interpreting Common Solver Warnings in `.mslog`
1. **`WARNING METHOD panel_buckling: Input stresses must be negative (sigma=19.8666)`**:
   - **Root Cause**: Compressive buckling methods (`MS_PlateBuckling_FlatCompressive`, `MS_PlateBuckling_CurvedCompressive`, `MS_InterRivetBuckling_Column`) require compressive stress ($\sigma < 0$). When evaluated across a multi-maneuver `LoadCaseSet` (containing both $+2.5g$ pull-up and $-1.0g$ push-over), load cases that place the panel or stringer in **tension** ($\sigma > 0$) trigger this informational warning.
   - **Solver Behavior**: The method assigns $\text{MS} = +\infty$ (`INF`) for tensile load cases and ranks only the compressive load cases. This is physically correct and not a setup error.
2. **`WARNING METHOD panel_buckling: The (Z) value (0.911893) is out of bounds, hence the result has been thresholded (kc=3.95)`**:
   - **Root Cause**: Bruhn curved-panel compressive buckling computes the Batdorf curvature parameter:
     ```math
     Z = \frac{b^2}{r \cdot t}\sqrt{1 - \nu^2}
     ```
     When a narrow curved skin panel has small width $b$ relative to radius $r$ and thickness $t$ such that $Z < 1.0$, the empirical curved-panel chart reaches its lower flat-plate asymptote.
   - **Solver Behavior**: The method thresholds the buckling coefficient to $k_c = 3.95$ (conservative flat-plate limit).
3. **Critical Negative Margin Identification (`MS < 0`)**:
   - In `AO_Aeroelastic.s1_MoS_14_LCs.msz`, the global minimum margin occurs on **`Wing_Spar_Plate_Buckling 16`** (`MS = -0.78747`, Rank 1) under `Symmetric_maneuvers::LC_01_pull_up_0.24_SL` and `LC_06_pull_up_0.5_37k` ($\sigma = -46.85\text{ ksi}$ vs. $\sigma_{\text{allow}} = 9.96\text{ ksi}$ for $a = 20.68\text{ in}, b = 4.92\text{ in}, t = 0.25\text{ in}$).
   - **Engineering Action**: Increase spar web thickness $t$ or subdivide the spar web bay with vertical stiffeners (`a` reduction) and re-run the associative `MarginSolution`.

---

## 4. Automated Word Report Generation (`Company_MarginOfSafety_Template_01_Full.docx`)

Simcenter 3D Aerostructures generates certification reports directly from `.docx` templates containing structured Word bookmarks:
- **Document Metadata Bookmarks**: `BM_TEXT_Document_Title`, `BM_TEXT_Document_Author`, `BM_TEXT_Document_Date`, `BM_TEXT_SIM_Part_Name`, `BM_TEXT_FEM_Part_Name`.
- **Solution & Global Summary Bookmarks**: `BM_TEXT_Margin_Solution_Name`, `BM_TEXT_Margin_Solution_Description`, `BM_TEXT_Margin_Solution_Critical_MS`, `BM_TABLE_Global_Summary`, `BM_IMAGE_Global_Graphical_Report`.
- **Iterative Calculation Loop Bookmarks (`BM_LOOP_*`)**:
  - `BM_LOOP_Calculations` iterates over each `MarginCalculation` (filtered by threshold MS or Rank), populating `BM_TEXT_Calc_Name`, `BM_TEXT_Calc_Method`, `BM_TEXT_Calc_Min_MS`, `BM_IMAGE_Calc_Snapshot`, `BM_TABLE_Calc_Inputs`, and `BM_TABLE_Calc_Results_By_FM_And_LC`.
