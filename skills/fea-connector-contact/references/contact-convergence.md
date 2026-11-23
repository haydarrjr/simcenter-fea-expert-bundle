# Contact convergence and physical verification

## Establish the interface and load history

Resolve the source and target faces through their physical roles. Check orientation, occurrence transform, separation or interference, search distance, friction, glue and duplicate constraints. Establish how each body is restrained while the pair is open. Predict starting contact and the effects of any gap correction from the effective deck. Preserve the intended load or displacement history through preload, service and unloading. For enforced displacement, check that each component has a defined value on both sides of a sequential subcase transition and that the solver uses the intended interpolation.

At each needed state read the last accepted increment and its actual load or displacement. Cross-check solver diagnostics with contact pressure, normal gap, status and force in the paired result file. Compare forces on one side of the interface with the reaction and applied load under a stated sign convention. Treat a missing contact row as missing until the field's sparse-output convention and independent gap, displacement or reaction establish the open state.

## Diagnose and isolate changes

- If the initial response shifts or penetration is unexpected, check initial gap treatment, surface normals, contact activation and the actual displacement before changing iteration controls.
- If the iteration reports show contact switching or cutbacks, track the active region and accepted equilibrium states. Refine the increment across the anticipated switch and keep the contact and mesh definitions fixed for that comparison.
- Change local mesh resolution, increment size and normal enforcement in separate runs. Capture the realized solver stiffness where automatic enforcement depends on geometry or discretization. Evaluate penetration against the physical gap or approach and local facet size.
- Check the realized mesh spacing along each contact face and through the depth of both bodies. Inspect the first layers and the transition to the far field on each side. A fine surface mesh can still overstate contact stiffness if coarse elements sit directly beneath it.
- Where a diagnostic run uses contact damping, document its effect on the result and energy or work. Inspect the final physical state even if the solver reports completion.

For a controlled two-body elastic closure test, predict contact onset from initial clearance and closed force from two compressive compliances in series. Bracket the first contact with accepted increments and verify the return to positive separation with near-zero reaction and contact force. For a frictionless elastic spherical contact test, independently calculate reduced modulus, contact radius, peak pressure and approach. Compare the resolved and partially active area, pressure along fixed radial positions, integrated force and boundaries at several mesh levels. Preserve full-model scaling if the model uses symmetry.

[SOL 401 contact convergence](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.multi_step_nonlinear/html/xid1201098?audience=external) · [SOL 402 contact diagnostics](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid2016266?audience=external)
