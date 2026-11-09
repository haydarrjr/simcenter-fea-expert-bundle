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

### Complete Set of 17 `ExtractProperty` Rules Used in `AO_Aeroelastic.s1.sim`
```
ExtractProperty("1D Mesh", "BEAM_SECTION_PROP", {"Area"})
ExtractProperty("1D Mesh", "BEAM_SECTION_PROP", {"h"})
ExtractProperty("1D Mesh", "MATERIAL_PROP", {"Yield", "71.330000[F]"})
ExtractProperty("1D Mesh", "MATERIAL_PROP", {"YoungsModulusConstant", "71.330000[F]"})
ExtractProperty("Loaded_Edge", "AVG_CURVRAD", {})
ExtractProperty("Loaded_Edge", "TOTAL_LENGTH", {})
ExtractProperty("Panel", "MATERIAL_PROP", {"Yield", "71.330000[F]"})
ExtractProperty("Polygon Edge", "BEAM_SECTION_PROP", {"Area"})
ExtractProperty("Polygon Face", "MATERIAL_PROP", {"PoissonsRatioConstant", "71.330000[F]"})
ExtractProperty("Polygon Face", "MATERIAL_PROP", {"Yield", "71.330000[F]"})
ExtractProperty("Polygon Face", "MATERIAL_PROP", {"YoungsModulusConstant", "71.330000[F]"})
ExtractProperty("Polygon Face", "MIN_THICKNESS", {})
ExtractProperty("Polygon Face", "PROJ_LENGTH", {"171115 - csys", "X"})
ExtractProperty("Polygon Face", "PROJ_LENGTH", {"171116 - csys", "Y"})
ExtractProperty("Polygon Face", "PROJ_LENGTH", {"171117 - csys", "X"})
ExtractProperty("Polygon Face", "PROJ_LENGTH", {"171118 - csys", "Y"})
ExtractProperty("Unloaded_Edge", "TOTAL_LENGTH", {})
```

---

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
  - `n`: Ramberg-Osgood parameter (`scalar`, `Unitless`, default `10`)
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
  - `FixityCoeff`: Rivet fixity coefficient $c$ (`scalar`, `Unitless`, e.g. `1.0` flat head, `2.0` countersunk/spotweld)
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

## 3. Python Forensic Parser for `.msz` Margin Archives

Use this standalone read-only script pattern to audit any `<sim>_<solution>.msz` archive and rank all calculations by minimum Margin of Safety:

```python
import re
import zipfile


def audit_msz_archive(msz_path: str):
    rank1_pattern = re.compile(
        r"1\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([-+0-9.eEINF]+)"
    )
    results = []
    with zipfile.ZipFile(msz_path, "r") as zf:
        for entry in zf.namelist():
            if not entry.endswith(".mslog"):
                continue
            text = zf.read(entry).decode("utf-8", errors="replace")
            m = rank1_pattern.search(text)
            if m:
                fm, lc, ms_str = (
                    m.group(1).strip(),
                    m.group(2).strip(),
                    m.group(3).strip(),
                )
                ms_val = (
                    float("inf")
                    if "INF" in ms_str.upper()
                    else float(ms_str)
                )
                results.append((ms_val, entry[:-6], fm, lc))
    results.sort(key=lambda x: x[0])
    return results
```
