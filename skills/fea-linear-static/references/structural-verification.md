# Verify a linear static structural model

## Establish applicability

Define the intended decision, load range, affected regions and result recovery. Check that material response remains in the assumed linear regime, geometric changes have negligible effects on equilibrium and stiffness, and every credited interface can sustain the assumed load path. Where the response is sensitive to stiffness, compare plausible support, joint or section representations before refining the mesh.

Treat a load combination as linear only when its constituent cases share the relevant stiffness, supports and active interfaces. Combine corresponding signed response components before applying nonlinear measures such as von Mises, principal values or maxima. Multi-case envelopes preserve the governing case and entity selection for each reported extremum.

## Verify loads and constraints

- Transform applied forces, moments and reactions to a common frame and datum. Integrate distributed tractions over the loaded area and verify resultant and moment. Include body forces, applied couples and prescribed-motion reactions as applicable. For inertia relief include the balancing inertia in the free-body budget.
- Check the constrained and coupled DOFs, including offset and rotational paths. A redistribution constraint or rigid region can transfer moments or add restraint. Examine near mechanisms, automatic constraint elimination and sensitivity to realistic support stiffness.
- Compare regions across CAD, mesh and the effective deck. Remeshing can change numeric labels and preserve a stale selector. Trace the physical region, coordinate frame, ownership and applied resultants.

## Test the solution

Use signed free-body balance as a necessary check. A wrong stiffness or redundant support can still balance the external loads. Choose an independent check that responds to the suspected error. Compare axial compliance, bending curvature, spring force or thermal expansion with a reference valid for the boundary conditions. In a zero-start elastic force ramp with fixed homogeneous constraints, `U = ½ fᵀu` is a useful energy check. Include prescribed-motion and initial-strain terms when they contribute work.

Bind displacements, reactions and stresses to the same load case and frame. Check whether the stress is recovered at the centroid, corners, integration points, or averaged nodes, and at the correct shell or ply location. Use refinement to verify the quantity at its physical scale. For a singular idealization, use a justified structural stress, path quantity or physically regularized local model.

Use [thermal stress](../../fea-thermal/SKILL.md) for temperature transfer, thermal reference and restraint. Use [eigenvalue buckling interpretation](../../fea-results-interpretation/references/sol103-sol105-quant.md) for a load factor about a specified reference state.
