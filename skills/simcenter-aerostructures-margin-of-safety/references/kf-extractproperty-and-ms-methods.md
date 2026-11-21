# Knowledge Fusion `ExtractProperty` Reference & Margin of Safety Method Schemas

Parent skill: [simcenter-aerostructures-margin-of-safety](../SKILL.md)

## 1. Host Knowledge Fusion Library (`nx_cae_aero_structures_scalar_input.dfa`)

Located at `$UGII_BASE_DIR/SIMULATION/aerostructures/dfa/nx_cae/hostlib/nx_cae_aero_structures_scalar_input.dfa`:

```
#! NX/KF 4.0
Defun: materialProperty(string $matName; string $propName; number $temp)
@{
    CFunc("aerostructui_materialProperty", "libaerostruct");
} number;

Defun: sectionProperty(string $sectName; string $propName)
@{
    CFunc("aerostructui_sectionProperty", "libaerostruct");
} number;

Defun: ExtractProperty(string $sourceName; string $extractionType; list $extractionParams)
@{
    CFunc("aerostructui_ExtractProperty", "libaerostruct");
} number;
```

### Bind associative inputs

Use the extraction names and argument signatures from the installed authoring method. For example, a supported `BEAM_SECTION_PROP` query supplies the selected beam mesh and section-property key. A `MATERIAL_PROP` query supplies the selected entity, property key and temperature with units. A `PROJ_LENGTH` query needs the actual coordinate system and axis. Audit values against the underlying selection, section and material before accepting the calculation.

## 2. Standard Margin of Safety Method Schemas (`$UGII_BASE_DIR/SIMULATION/aerostructures/margin_solution/`)

### 2.1 `MS_Allowable_Stress.xml` (`Stress allowable`)
- **Failure Mode**: `AllowableStress` (`Stress allowable`)
- **Inputs**:
  - `SigmaAllowable` (`scalar`, `measure="Stress"`, lowerbound `0.0`)
  - `Load` (`load_extraction`, `measure="Stress"`)
- **Outputs**:
  - `AbsoluteLoad` (`scalar`, `measure="Stress"`, `indexby="lc"`)

### 2.2 `MS_PlateBuckling_CurvedCompressive.xml` (`Plate buckling curved compressive`)
- **Failure Mode**: `panel_buckling` (`Panel buckling`)
- **Inputs**:
  - `b`: Width of panel (`scalar`, `Length`, lowerbound `0.0`)
  - `a`: Length of panel (`scalar`, `Length`, lowerbound `0.0`)
  - `t`: Thickness of panel (`scalar`, `Length`, lowerbound `0.0`)
  - `r`: Radius of curvature (`scalar`, `Length`, lowerbound `0.0`)
  - `Behaviour`: `"Elastic"` or `"Elastic-Plastic"` (`string`)
  - `E`: Young's modulus in compression (`scalar`, `Stress`)
  - `nu`: Poisson's ratio (`scalar`, `Unitless`, $0 < \nu < 0.5$)
  - `n`: Ramberg-Osgood parameter (`scalar`, `Unitless`, method-specific)
  - `Fy`: Compression yield stress (`scalar`, `Stress`)
  - `sigma`: Applied compressive stress (`load_extraction`, `Stress`)
- **Outputs**:
  - `sigmaAllowable` (`scalar`, `measure="Stress"`, `indexby="fm"`)

### 2.3 `MS_PlateBuckling_FlatCompressive.xml` (`Plate buckling flat compressive`)
- **Failure Mode**: `PlateBuckling_FlatCompressive` (`Plate buckling flat compressive`)
- **Inputs**:
  - `b`: Width of loaded edge (`scalar`, `Length`)
  - `a`: Length of unloaded edge (`scalar`, `Length`)
  - `t`: Plate thickness (`scalar`, `Length`)
  - `ConstraintType`: `"Simply supported"` or `"Clamped"` (`string`)
  - `Behaviour`: `"Elastic"` or `"Elastic-Plastic"` (`string`)
  - `E`: Young's modulus (`scalar`, `Stress`)
  - `nu`: Poisson's ratio (`scalar`, `Unitless`)
  - `n`: Ramberg-Osgood parameter (`scalar`, `Unitless`)
  - `Fy`: Compression yield stress (`scalar`, `Stress`)
  - `sigma`: Applied compressive stress (`load_extraction`, `Stress`)
- **Outputs**:
  - `sigmaAllowable` (`scalar`, `measure="Stress"`, `indexby="fm"`)

### 2.4 `MS_InterRivetBuckling_Column.xml` (`Inter-Rivet Buckling Column`)
- **Failure Mode**: `InterRivetBuckling_Column` (`Inter-Rivet Buckling Column`)
- **Inputs**:
  - `FixityCoeff`: Rivet fixity coefficient $c$ (`scalar`, `Unitless`, method-specific)
  - `Pitch`: Rivet pitch $p$ (`scalar`, `Length`)
  - `Ts`: Sheet thickness $t_s$ (`scalar`, `Length`)
  - `MaterialBehaviour`: `"Elastic"` or `"Elastic-Plastic"` (`string`)
  - `E`: Young's modulus (`scalar`, `Stress`)
  - `n`: Ramberg-Osgood parameter (`scalar`, `Unitless`)
  - `Fcy`: Compressive yield stress (`scalar`, `Stress`)
  - `F07`: Secant yield stress at $0.7 E$ (`scalar`, `Stress`)
  - `Sigma`: Extracted stringer axial stress (`load_extraction`, `Stress`, scaled from 1D beam `Axial` force via `1 / Area`)
- **Outputs**:
  - `SigmaAllowable` (`scalar`, `measure="Stress"`, `indexby="fm"`)

---

## 3. Archive inspection

Read the requested archive without extracting untrusted member paths. Check supported format, entry limits, unique calculation IDs, units, sign conventions, applicable failure modes, governing states and warnings. Parse the actual column schema, preserve signed infinities, and record unparsed rows. Compare each governing entry with the evaluated calculation and source result. Preserve the exact archive identity and terminal solve evidence.
