# Regional mesh verification

## Define and read the physical region

Bind the FEM, CAD revision and occurrence transform. Define each role by measurable support, load or interface geometry. Combine attributes with owner scope and geometric checks. Resolve the selection recipe and check entity type, owner, area or length, orientation and coverage. For repeated occurrences or adjacent surfaces, compare the resolved members with the excluded population. An empty or overly broad selection blocks the dependent change.

On a geometry revision, read the recipe again before applying a control. A split can produce several child faces representing the same region. Check their total area, physical union and normal orientation against the new CAD revision. A bounding volume has its own reference frame and dimensions. Test how its members change when the underlying geometry or coordinate system moves.

## Apply the mesh control

Choose size on face or an equivalent local control for contact and load transfer. Use edge divisions or bias for thickness and transition, and choose curvature or chordal control where geometric approximation is a source of error. Consider a swept mesh when the topology and required through-thickness resolution favor it. Check the control target, units, nominal size and overlaps with other controls before regeneration.

Measure the resulting size distribution, element count or degrees of freedom, and element family and order on each side of a pair. For a contact footprint, record the facet count across the expected contact width and inspect opposing surface normals. For a curved quadratic mesh, inspect midside placement and mapped-element quality. Compare the transition region and the critical region on the same mesh revision.

Use [regional Element Quality](../../simcenter-3d-mesh-quality-review/SKILL.md) for the selected elements and [mesh convergence](../../fea-mesh-quality/SKILL.md) for sensitivity of the engineering result.
