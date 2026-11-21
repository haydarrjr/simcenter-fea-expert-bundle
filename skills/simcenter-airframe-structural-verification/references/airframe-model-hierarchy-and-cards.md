# Airframe model hierarchy and SOL 144 checks

| Layer | Evidence |
|---|---|
| Master CAD and idealized geometry | Revisions, associative sources and the topology retained for load transfer. Verify midsurface normals, offsets, connection selections and update results. |
| Component FEM and structural AFM | Instance transforms and label offsets, material/section ownership, shell/beam orientations, equivalence, connector DOFs and actual tributary mass. |
| Aero FEM and coupled assembly | Aerodynamic coordinate systems, reference geometry, panel/body discretization, structural spline attachments and consistent interpolation. |
| SIM and results | Active FEM/AFM, actual trim inputs and controls, result lineage, supported conditions and physically balanced states. |

## Deck and trim

- Match `AEROS` reference system, span, chord, area and symmetry to the intended configuration. Check `CAERO1/PAERO1` or `CAERO2/PAERO2` dependencies when present.
- For `SPLINE1` or `SPLINE2`, verify the aero box range, connected structural set and DOF/geometry assumptions. Check transfer of force and moment and search for overconstraint or disconnected components.
- For each `TRIM` case, verify Mach number, dynamic pressure, units and which degrees of freedom or controls are prescribed versus solved. Resolve `AESTAT`, `AESURF`, `AELINK` and `SUPORT` when used. Verify inertial loads, mass, center of gravity and support behavior for that case.
- Keep a manifest mapping configuration and case to deck and result state. Reconcile forces and moments in a common frame and origin before aggregating. Retain coincident vector components and original state IDs when deriving an envelope.
- Confirm that attached results use compatible geometry, mapping, units, recovery and state definitions. Use the [load filtering skill](../../simcenter-aerostructures-load-filtering/SKILL.md) for NFR and coherent case selection. Use the [margin skill](../../simcenter-aerostructures-margin-of-safety/SKILL.md) for downstream checks.

Card names describe candidate deck surfaces. Verify the exact installed solver reference and each active selector before accepting the exported deck.
