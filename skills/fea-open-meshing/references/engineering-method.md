# Solid mesh and boundary-transfer balance

Establish CAD/FEM scale and units before interpreting target mesh sizes. Capture solid/face ownership, geometric volume, areas, per-body material, part-to-FEM map and surface orientation. Inspect manifold connectivity, intentional seams, duplicate nodes, volume delta and any suspect midside geometry. Verify Tet10 Jacobian over the curved element with family-appropriate documented tests.

For traction t on the loaded surface, integrate F = integral(t dA) and M = integral((x-x0) cross t dA), with x0 and coordinates in a stated reference frame. For pressure use the recorded surface-normal and pressure sign. For uniform flux on a mapped surface, Q equals area times flux. For a constant load on one planar face, independently check the force and centroid moment. For curved or mapped faces integrate using the physical surface and the correct interpolation and quadrature. Compare the mapped nodal forces/reactions to these totals as appropriate.

A unit cube in consistent SI units with 1 MPa traction over 1 square metre has 1 MN resultant. A 1 kW/mÂ² uniform flux over that face has 1 kW power. These are balance checks. Different element order, material, boundary approximation and singular features require their own QoI refinement.
