# Reference Airframe Model Hierarchy, Mesh Collectors, Aero Cards & Trim Subcases

Parent skill: [simcenter-airframe-structural-verification](../SKILL.md)

## 1. Complete Part, Idealized, FEM, AFM & SIM Inventory

| File Name | Role | Parent / Child Dependencies | Key Parametrizations & Features |
|---|---|---|---|
| `AO_GFEM.prt` | Master Structural CAD Assembly | Contains `AO_GFEM_Wing.prt`, `AO_GFEM_Fuselage.prt`, `AO_GFEM_Nose.prt`, `AO_GFEM_Empennage.prt` | Assembly positioning & station coordinate references |
| `AO_GFEM_Wing.prt` | Wing CAD Part | $\rightarrow$ `AO_GFEM_Wing_shellbeam_const.i1.prt` | `Wing_Surf`, `Ailerons_Split`, `Rib_1..15`, `Fore_Spar`, `Mid_Spar`, `Aft_Spar`, `WingLug1..3` |
| `AO_GFEM_Wing_shellbeam_const.f1.fem` | Wing Component FEM | Built on `AO_GFEM_Wing_shellbeam_const.i1.prt` | 2D Shells (`Skins`, `Ribs`, `MidSpar`, `ForeAndAftSpar`, `Flaps`, `Brackets`), 1D Beams (`SparCaps`, `Stringers`), `WingLugRigid`, `EngineMountConstraint`, `FuelWingMass1..3` |
| `AO_GFEM_Fuselage.prt` | Fuselage CAD Part | $\rightarrow$ `AO_GFEM_Fuselage.i1.prt` | `Exterior_Skin`, `Floor`, `Bulkhead_1..2`, `Frame_1..12`, `Longeron_1..16`, `Floor_Beam_1..12` |
| `AO_GFEM_Fuselage_beams.f1.fem` | Fuselage Component FEM | Built on `AO_GFEM_Fuselage.i1.prt` | 2D Shells (`Shell`, `BulkHeads`), 1D Beams (`Frame`, `Longeron`, `FloorBeams`), `RadarMass`, `FuelMasses`, `RBE3_MeshMasses` |
| `AO_GFEM_Nose.prt` | Nose CAD Part | $\rightarrow$ `AO_GFEM_Nose_beams.i1.prt` | `Nose_Skin`, `Bulkhead`, `Frames`, `Stringers` |
| `AO_GFEM_Nose_beams.f1.fem` | Nose Component FEM | Built on `AO_GFEM_Nose_beams.i1.prt` | 2D Shells (`Nose_Skin`, `Bulkhead`), 1D Beams (`Frames`, `Stringers`) |
| `AO_GFEM_Empennage.prt` | Empennage CAD Part | $\rightarrow$ `AO_GFEM_Empennage.i1.prt` | `Tail_Skin`, `VTail_Surf`, `Ruddervator`, `Spars_Ribs`, `Frames`, `Stringers` |
| `AO_GFEM_Empennage_beams.f1.fem` | Empennage Component FEM | Built on `AO_GFEM_Empennage.i1.prt` | 2D Shells (`Skin`, `Spars_Ribs`, `MassSurface`), 1D Beams (`Frames`, `Stringers`), `EmpennageFuelMasses`, `RBE3_Mass` |
| `AO_GFEM.af1.afm` | Structural Global Assembly FEM | Combines the 4 component `.f1.fem` models | Assembly `RBE2` stitching (`connection_recipe_1_mesh` Fuselage-Empennage, `connection_recipe_2_mesh` Fuselage-Nose) |
| `AO_Aeroelastic.1.prt` | Aero Reference CAD Part | Interpart links from `AO_GFEM_Fuselage.i1.prt` & `AO_GFEM_Empennage.i1.prt` | Interpart distance/radius expressions (`p65..p107`, `p811`, `p2037`) driving `CAERO2` body lengths & radii |
| `AO_Aeroelastic.1.f1.fem` | Aerodynamic FEM | Built on `AO_Aeroelastic.1.prt` | `Wing_Aero_Panels`, `Tail_Aero_Panels` (`CAERO1`/`PAERO1`), `Fuselage_Collector`, `Empennage_collector` (`CAERO2`/`PAERO2`) |
| `AO_Aeroelastic.af1.afm` | Top-Level Aeroelastic Assembly FEM | Combines `AO_GFEM.af1.afm` + `AO_Aeroelastic.1.f1.fem` | 10 `SPLINE1` surface splines + 2 `SPLINE2` beam splines |
| `AO_Aeroelastic.s1.sim` | Master Simulation File | Built on `AO_Aeroelastic.af1.afm` | `Symmetric_maneuvers` (`SOL 144`), `Roll` (`SOL 144`), `49` NFRs, `Filter_14LCs` (`LoadFilteringSolution`), `MoS_14_LCs` (`MarginSolution`) |

---

## 2. Structural Collector, Property & Material Reference (`ao_aeroelastic.s1-symmetric_maneuvers.dat`)

### Materials
- **`Aluminum_2014` (`MID 1, 38, 39, 40`)**:
  - $E = 1.050566 \times 10^7\text{ psi}$, $\nu = 0.33$, $\rho = 2.61499 \times 10^{-4}\text{ lbf}\cdot\text{s}^2/\text{in}^4$, $\alpha = 1.27778 \times 10^{-5}\text{ /^\circ F}$, $F_{tu} = 60,900\text{ psi}$, $F_{ty} = 59,015\text{ psi}$.
- **`Aluminum_6061` (`MID 12` with `MATT1` `TABLEM1 13, 14, 15`)**:
  - $E = 9.986 \times 10^6\text{ psi}$, $\nu = 0.33$, $\rho = 2.5393 \times 10^{-4}\text{ lbf}\cdot\text{s}^2/\text{in}^4$, $F_{tu} = 26,106.8\text{ psi}$, $F_{ty} = 21,030.5\text{ psi}$.

### Collector & Property Table

| Component FEM | Collector Name | Element Type | Property Card | Section / Thickness | Material |
|---|---|---|---|---|---|
| **Wing** | `Skins` | `CQUAD4`/`CTRIA3` | `PSHELL 8` | $t = 0.15\text{ in}$ | `Aluminum_2014` |
| **Wing** | `Ribs` | `CQUAD4`/`CTRIA3` | `PSHELL 9` | $t = 0.20\text{ in}$ | `Aluminum_2014` |
| **Wing** | `MidSpar` | `CQUAD4` | `PSHELL 10` | $t = 0.50\text{ in}$ | `Aluminum_2014` |
| **Wing** | `ForeAndAftSpar` | `CQUAD4` | `PSHELL 11` | $t = 0.25\text{ in}$ | `Aluminum_2014` |
| **Wing** | `Flaps` | `CQUAD4` | `PSHELL 12` | $t = 0.09\text{ in}$ | `Aluminum_2014` |
| **Wing** | `Brackets` | `CQUAD4`/`CTRIA3` | `PSHELL 13` | $t = 0.75\text{ in}$ | `Aluminum_2014` |
| **Wing** | `SparCaps` | `CBEAM` | `PBEAML 14` (`L`) | $1.5 \times 1.5 \times 0.175\text{ in}$ ($A = 0.494375\text{ in}^2$) | `Aluminum_2014` |
| **Wing** | `Stringers` | `CBEAM` | `PBEAML 15` (`HAT`) | $0.5 \times 0.125 \times 1.0 \times 0.35\text{ in}$ ($A = 0.28125\text{ in}^2$) | `Aluminum_2014` |
| **Fuselage** | `Shell` | `CQUAD4`/`CTRIA3` | `PSHELL 16` | $t = 0.075\text{ in}$ | `Aluminum_2014` |
| **Fuselage** | `BulkHeads` | `CQUAD4`/`CTRIA3` | `PSHELL 17` | $t = 0.10\text{ in}$ | `Aluminum_2014` |
| **Fuselage** | `Frame` | `CBEAM` | `PBEAML 18` (`T1`) | $2.5 \times 2.0 \times 0.25 \times 0.20\text{ in}$ ($A = 0.95\text{ in}^2$) | `Aluminum_2014` |
| **Fuselage** | `Longeron` | `CBEAM` | `PBEAML 19` (`HAT`) | $1.5 \times 0.2 \times 2.0 \times 0.25\text{ in}$ ($A = 0.92\text{ in}^2$) | `Aluminum_2014` |
| **Fuselage** | `FloorBeams` | `CBEAM` | `PBEAML 20` (`I`) | $3.0 \times 1.5 \times 1.5 \times 0.15 \times 0.15 \times 0.15\text{ in}$ ($A = 0.855\text{ in}^2$) | `Aluminum_2014` |
| **Nose** | `Nose_Skin` | `CQUAD4`/`CTRIA3` | `PSHELL 21` | $t = 0.075\text{ in}$ | `Aluminum_2014` |
| **Nose** | `Bulkhead` | `CQUAD4`/`CTRIA3` | `PSHELL 22` | $t = 0.10\text{ in}$ | `Aluminum_2014` |
| **Nose** | `Frames` | `CBEAM` | `PBEAML 23` (`T1`) | $A = 0.95\text{ in}^2$ | `Aluminum_2014` |
| **Nose** | `Stringers` | `CBEAM` | `PBEAML 24` (`HAT`) | $A = 0.92\text{ in}^2$ | `Aluminum_2014` |
| **Empennage** | `Skin` | `CQUAD4`/`CTRIA3` | `PSHELL 1` | $t = 0.10\text{ in}$ | `Aluminum_6061` |
| **Empennage** | `Spars_Ribs` | `CQUAD4`/`CTRIA3` | `PSHELL 2` | $t = 0.20\text{ in}$ | `Aluminum_2014` |
| **Empennage** | `Frames` | `CBEAM` | `PBEAML 4` (`CHAN`) | $A = 0.181875\text{ in}^2$ | `Aluminum_2014` |
| **Empennage** | `Stringers` | `CBEAM` | `PBEAML 5` (`HAT`) | $A = 0.28125\text{ in}^2$ | `Aluminum_2014` |

---

## 3. Aerodynamic Reference & Trim Cards (`SOL 144`)

### Global Aerodynamic Reference (`AEROS`)
```
AEROS          0       0 69.8914421.0526 8634.52       0       0
```
- Reference chord $\bar{c} = 69.8914\text{ in}$
- Reference span $b = 421.0526\text{ in}$
- Reference area $S_{\text{ref}} = 8634.52\text{ in}^2$

### Complete 14-Load-Case Envelope Across Multi-Weight OP2 Files

| Load Case # | Subcase Name | Solution / OP2 File | Weight Config | Mach $M$ | Dynamic Pressure $q$ ($\text{psi}$) | Load Factor / Roll Input |
|---|---|---|---|---|---|---|
| **1** | `LC_01_pull_up_0.24_SL` | `Symmetric_maneuvers` (`.op2`) | DTOW (100%) | `0.24` | `0.592451` | $\text{URDD3} = +965.25\text{ in/s}^2$ ($+2.5g$) |
| **2** | `LC_02_push_over_0.24_SL` | `Symmetric_maneuvers` (`.op2`) | DTOW (100%) | `0.24` | `0.592451` | $\text{URDD3} = -386.10\text{ in/s}^2$ ($-1.0g$) |
| **3** | `LC_03_pull_up_0.17_SL` | `Symmetric_maneuvers` (`.op2`) | DTOW (100%) | `0.17` | `0.297299` | $\text{URDD3} = +965.25\text{ in/s}^2$ ($+2.5g$) |
| **4** | `LC_06_pull_up_0.5_37k` | `Symmetric_maneuvers` (`.op2`) | DTOW (100%) | `0.50` | `0.569823` | $\text{URDD3} = +965.25\text{ in/s}^2$ ($+2.5g$) |
| **5** | `LC_16_Cruise` | `Symmetric_maneuvers` (`.op2`) | DTOW (100%) | `0.50` | `0.569823` | $\text{URDD3} = +386.10\text{ in/s}^2$ ($+1.0g$) |
| **6** | `LC_15_Landing` | `Symmetric_maneuvers` (`.op2`) | DTOW (100%) | `0.17` | `0.297299` | $\text{URDD3} = +965.25\text{ in/s}^2$ ($+2.5g$) |
| **7** | `LC_04_pull_up_0.34_SL` | `Symmetric_maneuvers` (`_dtow2.op2`) | DTOW2 (92%) | `0.34` | Sea Level | $+2.5g$ Pull-Up |
| **8** | `LC_05_push_over_0.34_SL` | `Symmetric_maneuvers` (`_dtow2.op2`) | DTOW2 (92%) | `0.34` | Sea Level | $-1.0g$ Push-Over |
| **9** | `LC_07_push_over_0.5_37k` | `Symmetric_maneuvers` (`_dtow2.op2`) | DTOW2 (92%) | `0.50` | 37,000 ft | $-1.0g$ Push-Over |
| **10** | `LC_08_pull_up_0.55_37k` | `Symmetric_maneuvers` (`_dtow2.op2`) | DTOW2 (92%) | `0.55` | 37,000 ft | $+2.5g$ Pull-Up |
| **11** | `LC_09_push_over_0.55_37k` | `Symmetric_maneuvers` (`_dtow2.op2`) | DTOW2 (92%) | `0.55` | 37,000 ft | $-1.0g$ Push-Over |
| **12** | `LC_10_push_over_0.17_SL` | `Symmetric_maneuvers` (`_dtow2.op2`) | DTOW2 (92%) | `0.17` | Sea Level | $-1.0g$ Push-Over |
| **13** | `SteadyRoll` (`SUBCASE 1`) | `Roll` (`-roll.op2`) | DTOW (100%) | `0.17` | `0.297299` | $\text{ROLL} = 0.046$, $\text{URDD4} = 0.0$ |
| **14** | `AbruptRoll` (`SUBCASE 2`) | `Roll` (`-roll.op2`) | DTOW (100%) | `0.17` | `0.297299` | $\text{ROLL} = 0.0$, $\text{URDD4} = 0.523599\text{ rad/s}^2$ |
