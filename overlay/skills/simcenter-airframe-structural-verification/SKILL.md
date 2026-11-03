---
name: simcenter-airframe-structural-verification
description: Orchestrate the end-to-end Simcenter 3D Airframe Structural Verification workflow from associative CAD, Idealized parts, Component FEMs, Structural Assembly GFEM, and Aeroelastic Assembly FEM through SOL 144 static aeroelastic trim (multi-weight OP2 envelope), 49-station Nodal Force Reports, Load Case Filtering, associative Knowledge Fusion Margin of Safety, and automated Word report generation.
---

# Simcenter 3D Airframe Structural Verification Workflow

Use this skill when building, inspecting, diagnosing, or automating an end-to-end **Airframe Structural Verification** pipeline in Simcenter 3D and Simcenter Nastran (`SOL 144` Static Aeroelasticity $\rightarrow$ Nodal Force Reports $\rightarrow$ Load Case Filtering $\rightarrow$ Margin of Safety $\rightarrow$ Certification Report).

Related specialist skills:
- Tool routing & host capabilities: [fea-sc3d-tool-routing](../fea-sc3d-tool-routing/SKILL.md)
- Nodal Force Reports & Load Case Filtering (`NXOpen.CAE.AeroStructures.LoadFilteringSolution`): [simcenter-aerostructures-load-filtering](../simcenter-aerostructures-load-filtering/SKILL.md)
- Margin of Safety & associative Knowledge Fusion `ExtractProperty` rules (`NXOpen.CAE.AeroStructures.MarginSolution`): [simcenter-aerostructures-margin-of-safety](../simcenter-aerostructures-margin-of-safety/SKILL.md)
- Detailed reference model hierarchy, collectors, aero cards, and trim cases: [airframe model hierarchy and cards](references/airframe-model-hierarchy-and-cards.md)

---

## 1. End-to-End 5-Stage Airframe Verification Pipeline

The canonical Simcenter 3D airframe certification workflow consists of five associative stages:

| Subscene | Stage | Primary Artifacts | Key Simcenter 3D / Nastran Entities |
|---|---|---|---|
| **1** | **Integrated Design & SOL 144 Aeroelastic Trim** | `.prt` $\rightarrow$ `.i1.prt` $\rightarrow$ `.f1.fem` $\rightarrow$ `AO_GFEM.af1.afm` $\rightarrow$ `AO_Aeroelastic.af1.afm` $\rightarrow$ `AO_Aeroelastic.s1.sim` | `CAERO1`/`PAERO1`, `CAERO2`/`PAERO2`, `SPLINE1`/`SPLINE2`, `AEROS`, `AESTAT`, `AESURF`, `AELINK`, `TRIM`, `SUPORT`, multi-weight `.op2` attachments |
| **2** | **Nodal Force Reports (NFR) & Free-Body Extraction** | `AO_Aeroelastic.s1.sim` (`49` NFR objects) | `NFR_Wing_curve_Grid Point_1..12`, `NFR_Tail_curve_Grid Point_1..11`, `NFR_Fuselage_curve_Grid Point_1..26`, `NXOpen.CAE.AeroStructures.FreeBodyLoadExtraction` |
| **3** | **Load Case Filtering (LCF)** | `Filter_14LCs` solution, `CustomLoadCaseFiltering/` (`.xmd`, `.xml`, `.py`), `LoadCaseSets/*.xlsx` | `LoadFilteringSolution`, `LoadFilteringCalculation`, `ABB.Lcf1dMinMax`, `ABB.LcfConvexHull`, `LCset_Fuselage`, `LCset_Wing`, `LC_set_Tail` |
| **4** | **Associative Margin of Safety (MoS)** | `MoS_14_LCs` solution (`1,100` calculations across `19` component families), `.msz` archive | `MarginSolution`, `MarginCalculation`, `ExtractProperty(...)` Knowledge Fusion rules, `MS_Allowable_Stress`, `MS_PlateBuckling_CurvedCompressive`, `MS_PlateBuckling_FlatCompressive`, `MS_InterRivetBuckling_Column` |
| **5** | **Automated Certification Report Generation** | `Company_MarginOfSafety_Template_01_Full.docx` | Simcenter 3D Report Writer bookmarks (`BM_TEXT_*`, `BM_IMAGE_*`, `BM_TABLE_*`, `BM_LOOP_*`) |

---

## 2. Multi-Level Associative Model Hierarchy (Subscene 1)

Airframe verification separates **structural airframe meshing** from **aerodynamic lifting-surface/slender-body meshing** using a two-tier Assembly FEM (`AFM`) architecture:

```
AO_Aeroelastic.s1.sim  (SOL 144 Static Aeroelasticity + LCF Filter_14LCs + MoS MoS_14_LCs)
 └── AO_Aeroelastic.af1.afm  (Top-Level Aeroelastic Assembly FEM)
      ├── AO_Aeroelastic.1.f1.fem  (Aerodynamic Panel/Body & Spline FEM)
      │    └── AO_Aeroelastic.1.prt  (Aero reference geometry with interpart links to Fuselage.i1 & Empennage.i1)
      └── AO_GFEM.af1.afm  (Structural Global Finite Element Model - Assembly FEM)
           └── AO_GFEM.prt  (Structural Master CAD Assembly)
                ├── Wing:      AO_GFEM_Wing.prt -> AO_GFEM_Wing_shellbeam_const.i1.prt -> AO_GFEM_Wing_shellbeam_const.f1.fem
                ├── Fuselage:  AO_GFEM_Fuselage.prt -> AO_GFEM_Fuselage.i1.prt -> AO_GFEM_Fuselage_beams.f1.fem
                ├── Nose:      AO_GFEM_Nose.prt -> AO_GFEM_Nose_beams.i1.prt -> AO_GFEM_Nose_beams.f1.fem
                └── Empennage: AO_GFEM_Empennage.prt -> AO_GFEM_Empennage.i1.prt -> AO_GFEM_Empennage_beams.f1.fem
```

### Structural Connections & Mass Distribution Rules
1. **Inter-Component Assembly Stitching (`AO_GFEM.af1.afm`)**:
   - Component FEMs are stitched at bulkheads/rings using assembly-level coincident-node `RBE2` recipes (`connection_recipe_1_mesh::AO_GFEM.af1` for Fuselage-to-Empennage, `connection_recipe_2_mesh::AO_GFEM.af1` for Fuselage-to-Nose).
2. **Wing-to-Fuselage Attachment (`WingLugRigid`)**:
   - Modeled with 6 pin-jointed `RBE2` elements at the wing root bracket lugs (nodes `12242..12253`) transferring shear and bending into the fuselage carry-through frames.
3. **Non-Structural Lumped Masses (`CONM2` + `RBE3`)**:
   - Never attach concentrated masses (`CONM2`) to single shell nodes or rigid `RBE2` spiders (which artificially stiffen the airframe). Distribute all lumped masses via interpolation `RBE3` spiders:
     - **Engine Mount**: `Engine Lumped Mass` (`CONM2` $= 0.662377\text{ lbf}\cdot\text{s}^2/\text{in}$) distributed via `EngineMountConstraint` (`RBE3` on node `12241`).
     - **Wing Fuel**: `FuelWingMass1..3` (`3 CONM2`s $= 0.258999\text{ lbf}\cdot\text{s}^2/\text{in}$ each) via `RBE3_MassCollector`.
     - **Fuselage Fuel & Radar**: `FuelMasses` (`5 CONM2`s $= 0.517997\text{ lbf}\cdot\text{s}^2/\text{in}$ each) and `RadarMass` (`CONM2` $= 0.032375\text{ lbf}\cdot\text{s}^2/\text{in}$) via `RBE3_MeshMasses`.
     - **Empennage Fuel**: `EmpennageFuelMasses` (`5 CONM2`s $= 0.258999\text{ lbf}\cdot\text{s}^2/\text{in}$ each) via `RBE3_Mass`.

---

## 3. Interpart Aerodynamic Parametrization & Splines (`AO_Aeroelastic.1.f1.fem`)

To ensure CAD/Idealized geometry updates propagate automatically to the aerodynamic model without manual card editing:

1. **Interpart Expressions (`AO_Aeroelastic.1.prt` $\leftarrow$ `AO_GFEM_Fuselage.i1.prt` & `AO_GFEM_Empennage.i1.prt`)**:
   - Minimum-distance and face-radius measurements in `AO_Aeroelastic.1.prt` link to the idealized fuselage and empennage parts.
   - These expressions (`p65..p107`, `p811`, `p2037`) drive the axial station locations `X(i)` and half-widths `R(i)` of the `CAERO2` slender-body interference elements (`Aero Body 1` `EID 4545` for Fuselage; `Aero Body 2` `EID 5153` for Empennage).
2. **Lifting Surfaces (`CAERO1` / `PAERO1`)**:
   - `Wing_Aero_Panels` (`PAERO1 4`, associated to slender body `4545`): Inboard Wing (`Aero Panel 1`, `EID 1`), Mid/Outboard Wing (`Aero Panel 2`, `EID 513`), Aileron Control Surface (`Aero Panel 4`, `EID 2049`), plus XZ-symmetric reflections (`EID 1025, 1537, 2561`).
   - `Tail_Aero_Panels` (`PAERO1 5`, associated to slender body `5153`): V-Tail Stabilizer (`Aero Panel 5`, `EID 3073`), Ruddervator Control Surface (`Aero Panel 6`, `EID 3905`), plus XZ-symmetric reflections (`EID 3489, 4225`).
3. **Aero-Structure Coupling (`SPLINE1` & `SPLINE2`)**:
   - Lifting panels use Infinite Plate Splines (`SPLINE1`, `METH=IPS`, `USAGE=BOTH`): `RWing_1`, `RWing_2`, `RWing_4`, `LWing_1`, `LWing_2`, `LWing_4`, `RTail_1`, `RTail_2`, `LTail_1`, `LTail_2`.
   - Slender bodies use Beam Splines (`SPLINE2`): `Fuselage_spline` (`EID 4607`, `CAERO 4545`, `SETG 4607`, `CID 10`) and `Empennage_spline` (`EID 5215`, `CAERO 5153`, `SETG 5215`, `CID 12`).

---

## 4. SOL 144 Static Aeroelastic Trim & Multi-Weight Flight Envelope

Static aeroelasticity (`SOL 144`) solves for trim equilibrium and structural deformation simultaneously. Symmetric maneuvers and antisymmetric roll maneuvers require distinct free-body relief (`SUPORT`), boundary conditions (`SPC1`), rigid-body aero variables (`AESTAT`), and control-surface links (`AESURF` / `AELINK`):

| Parameter | Solution 1: `Symmetric_maneuvers` | Solution 2: `Roll` |
|---|---|---|
| **CG Trim Node** | `GRID 144480` | `GRID 144480` |
| **`SUPORT` (Free Trim DOFs)** | `SUPORT 144480 35` (Plunge $T_z$, Pitch $R_y$) | `SUPORT 144480 4` (Roll $R_x$) |
| **`SPC1` (Constrained DOFs)** | `SPC1 15 1246 144480` ($T_x, T_y, R_x, R_z$) | `SPC1 15 12356 144480` ($T_x, T_y, T_z, R_y, R_z$) |
| **`AESTAT` Trim Variables** | `ANGLEA` (free), `PITCH` ($0$), `URDD3` ($n_z \cdot g$), `URDD5` ($0$) | `ROLL` (fixed rate or $0$), `URDD4` ($0$ or roll accel $\ddot{\phi}$) |
| **Control Surfaces (`AESURF`)** | `SURF0001` (`R_Rudder_Elevator`, free), `SURF0004` (`L_Rudder_Elevator`) | `SURF0002` (`R_Aileron`, free), `SURF0003` (`L_Aileron`) |
| **Control Link (`AELINK`)** | `SURF0004 = +1.0 * SURF0001` (symmetric pitch) | `SURF0003 = -1.0 * SURF0002` (antisymmetric roll) |

### Multi-Weight Flight Envelope via Companion OP2 Attachments (`14` Load Cases)
Instead of duplicating the entire `.sim` file for every fuel state, multi-weight configurations are combined into a single post-processing and Aerostructures envelope inside `AO_Aeroelastic.s1.sim` by attaching companion `.op2` result files:
1. **DTOW (100% Design Takeoff Weight)**:
   - `ao_aeroelastic.s1-symmetric_maneuvers.op2` (6 subcases: `LC_01_pull_up_0.24_SL`, `LC_02_push_over_0.24_SL`, `LC_03_pull_up_0.17_SL`, `LC_06_pull_up_0.5_37k`, `LC_16_Cruise`, `LC_15_Landing`).
   - `ao_aeroelastic.s1-roll.op2` (2 subcases: `SteadyRoll`, `AbruptRoll`).
2. **DTOW2 (92% DTOW right after ascent)**:
   - `ao_aeroelastic.s1-symmetric_maneuvers_dtow2.op2` attached to `Symmetric_maneuvers`, adding 6 subcases (`LC_04_pull_up_0.34_SL`, `LC_05_push_over_0.34_SL`, `LC_07_push_over_0.5_37k`, `LC_08_pull_up_0.55_37k`, `LC_09_push_over_0.55_37k`, `LC_10_push_over_0.17_SL`).
3. **ZFW (Zero Fuel Weight)**:
   - `ao_aeroelastic.s1-symmetric_maneuvers_zfw.op2` (available for fuel-burn sensitivity comparison).

---

## 5. Downstream Verification Stages (Subscenes 2, 3, 4, 5)

1. **Subscene 2 — Nodal Force Reports (`NFR`)**:
   - 49 station cuts (`12` Wing, `11` Tail, `26` Fuselage) integrate grid point forces (`GPFORCE`) across cross-sections.
   - Detailed workflow: [simcenter-aerostructures-load-filtering](../simcenter-aerostructures-load-filtering/SKILL.md).
2. **Subscene 3 — Load Case Filtering (`Filter_14LCs`)**:
   - Evaluates 2D Force-vs-Moment Convex Hull (`NFRCompat_FvF_ConvexHull`, `Tolerance = 0.02`) across all 49 stations and 14 load cases.
   - Reduces the envelope to component-specific Load Case Sets: `LCset_Fuselage` (`14` LCs), `LCset_Wing` (`12` LCs), `LC_set_Tail` (`11` LCs).
   - Detailed workflow: [simcenter-aerostructures-load-filtering](../simcenter-aerostructures-load-filtering/SKILL.md).
3. **Subscene 4 — Associative Margin of Safety (`MoS_14_LCs`)**:
   - Evaluates `1,100` calculations across `19` structural families using 4 standard methods (`MS_Allowable_Stress`, `MS_PlateBuckling_CurvedCompressive`, `MS_PlateBuckling_FlatCompressive`, `MS_InterRivetBuckling_Column`) parameterized via Knowledge Fusion `ExtractProperty(...)` rules.
   - Identifies critical negative margins (e.g., `Wing_Spar_Plate_Buckling 16` with $\text{MS} = -0.7875$ under `LC_01_pull_up_0.24_SL` and `LC_06_pull_up_0.5_37k`, driving spar web redesign).
   - Detailed workflow: [simcenter-aerostructures-margin-of-safety](../simcenter-aerostructures-margin-of-safety/SKILL.md).
4. **Subscene 5 — Automated Word Report Generation**:
   - Populates `Company_MarginOfSafety_Template_01_Full.docx` via Simcenter 3D Report Writer bookmarks.
   - Detailed workflow: [simcenter-aerostructures-margin-of-safety](../simcenter-aerostructures-margin-of-safety/SKILL.md).

---

## 6. Evidence Classes & Host Execution Policy

Follow [fea-sc3d-tool-routing](../fea-sc3d-tool-routing/SKILL.md) for all tool calls and Issue #21 evidence classifications:
- **Read-Only Inventory & Diagnostics**: Use `Simcenter 3D` model inspection tools (`part-info-tool`, `mesh-info-tool`, `material-info-tool`, `boundary-condition-tool`) via `fea-model-inspector`, and `Simcenter Nastran MCP` (`list_deck_cards`, `read_deck_cards`, `parse_f06_file`, `search_file`, `read_file_excerpt`) via `fea-solver-diagnostics` (`HOST_QUALIFIED` / `SOLVER_VERIFIED`).
- **NXOpen Journal Discovery & Sandbox Drafts**: Use `Designcenter Open` discovery tools (`dcopen-class-info`, `dcopen-member-info`, `dcopen-keyword-search-tool`) and sandbox tools (`dcopen-run-snippet-tool`, `dcopen-run-journal-tool`) via `fea-journal-author` (`MCP_2612_DISCOVERED`, sandbox, not live).
- **Live Mutation Gate**: Any live execution (`dcopen-execute-tool`, `surface-mesh-generation-tool`, `solid-mesh-generation-tool`) is performed **only by the main agent** on an owned working copy after an explicit user request (`NATIVE_EXECUTED`). If a license seat is held by an interactive session when spawning a second batch process, inspect the exported `.dat`, `.f06`, `.op2`, and `.msz` artifacts directly or run inside the connected session.
