---
name: fea-open-meshing
description: "Generate and analyze bounded open-source solid geometry without NX: Gmsh physical groups, tetrahedral meshes, consistent traction/pressure/heat-flux transfer and continuum checks. Use for source meshing experiments, small-part scale failures and geometry-to-solution verification."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Open meshing and boundary transfer

Use `fea_generate_volume_mesh` for an explicitly declared SI box or centered
through-hole box; use `fea_analyze_meshed_part` to apply physical boundary-group
loads and solve static, unstressed modal or steady conduction problems. This
executes optional Gmsh and the source continuum core without touching a native
CAD/FEM model. Read [the method](references/engineering-method.md) first.

1. Inspect engine availability and version with `fea_capabilities`. Require
   dimensions, mesh size and geometric applicability; no arbitrary scripts or
   hidden CAD files are accepted.
2. Inspect physical group names, source entity tags, node/element labels and
   triangle-to-volume adjacency. Confirm the complete exterior boundary is
   represented exactly once before assigning loads.
3. Apply traction in global Pa, compressive positive pressure against the outward
   normal, or positive inward heat flux in W/m². Integrate each triangle and
   check total force, moment or heat against an independent physical calculation.
4. Choose compatible constraints; keep modal inputs free of static-load keys.
   Solve and inspect residual, energy/heat balance, field and applicability limits.
5. Refine the actual QoI. Curved-boundary volume error is geometric evidence,
   not a stress-convergence estimate. Transfer a larger CAD scope to the owning
   CAD or qualified meshing integration without inventing support.

Get `meshed_traction`, `meshed_conduction` or `perforated_pressure` using
`fea_get_example`, then replace the declared physics with the user's actual
problem. Preserve original model protection; do not equate an in-memory Gmsh
result with an NX mesh, vendor solver execution or design acceptance.
