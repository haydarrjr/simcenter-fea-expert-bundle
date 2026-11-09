# Geometry, physical groups and consistent surface loading

Read source meshing and MCP integration (source: fea_expert_agent_plugin/docs/engineering/source-tools-v3.md)
for dependencies, tool usage and reproducible qualification. Gmsh 4.15.2 is an
optional separately installed open-source engine; no engine binary is bundled.
The implementation adopts the published Gmsh API and geometric/entity semantics,
not a commercial native CAD SDK.

## Representation and bounds

The declared geometry uses SI metres, axis-aligned extents and an optional
centered circular through-hole along z. Qualified output is first-order tet4
with triangular exterior faces. Identify box planes through their CAD surface
type and geometric centre of mass; inflated bounding boxes are unreliable for
small parts. Retain physical groups and geometry-entity tags separately from
node and element labels. Refuse an existing active Gmsh session instead of
clearing or finalizing an independently owned model.

Orient each triangle using its sole adjacent volume: its normal must point away
from the tetrahedron interior. The complete set of exterior tetrahedral faces
must equal the reported surface set with no duplicates. For a hole wall the
outward solid normal points into the hole, the opposite of the radial direction
away from the hole axis.

## Work and loading

For constant traction t on a linear triangle, each node receives `A*t/3`.
This preserves total force `A*t` and moment `centroid × A*t` exactly for the
piecewise-planar mesh. Pressure p>0 uses `t=-p*n_outward`. Positive heat flux
means heat supplied inward; each node receives `A*q/3` watts. A pressure sign
mistake can preserve load magnitude, stiffness and strain energy while reversing
the signed response, so test the sign as well as a scalar norm.

Independent geometry checks are `sum A*n=0` and
`sum A*(centroid dot n)=3*volume` on the closed oriented boundary.
These divergence-theorem checks complement per-face adjacency. They do not
establish surface smoothness or local stress accuracy.

## Executable investigations

The uniaxial solid (source: fea_expert_agent_plugin/examples/open_meshing_v3/box_traction.json) uses
compatible symmetry constraints and uniform surface traction. Compare every
nodal displacement to the affine elasticity solution, not only tip magnitude;
check Poisson contraction, resultant, moment and strain energy.
The conductor (source: fea_expert_agent_plugin/examples/open_meshing_v3/box_conduction.json) reproduces
the linear Fourier temperature profile and both boundary heat reactions.
The perforated component (source: fea_expert_agent_plugin/examples/open_meshing_v3/perforated_pressure.json)
tests hole normals, pressure transfer, force/moment balance and a nontrivial
3D stress field. The source output remains subject to continuum model limits.

Arbitrary imported CAD healing, high-order curved-element qualification,
adaptive remeshing, contact surface pairing and proprietary geometry formats
remain separate capabilities. Do not label them as implemented by a successful
primitive-based meshing run.
