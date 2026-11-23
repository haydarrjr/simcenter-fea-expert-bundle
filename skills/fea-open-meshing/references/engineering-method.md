# Solid mesh and boundary-transfer balance

Establish CAD/FEM scale and units before interpreting target mesh sizes. Capture solid/face ownership, geometric volume, areas, per-body material, part-to-FEM map and surface orientation. Inspect manifold connectivity, intentional seams, duplicate nodes, volume delta and any suspect midside geometry. Verify Tet10 Jacobian over the curved element with family-appropriate documented tests.

For traction t on the loaded surface, integrate F = integral(t dA) and M = integral((x-x0) cross t dA), with x0 and coordinates in a stated reference frame. For pressure use the recorded surface-normal and pressure sign. For uniform flux on a mapped surface, Q equals area times flux. For a constant load on one planar face, independently check the force and centroid moment. For curved or mapped faces integrate using the physical surface and the correct interpolation and quadrature. Compare the mapped nodal forces/reactions to these totals as appropriate.

Evaluate the effect of element order, geometry approximation and singular features on the quantity of interest through a separate refinement study.
