# Verify a nonlinear load path

## Define the physical history

Describe the mechanism that evolves through the load sequence. Track changing geometry and load direction, constitutive history, contact state and any support or coupling change. Record which variables pass to the next step and which loads, restraints or initial conditions are newly selected. Check the difference between sequential dependence, restart from a prescribed state and an independent analysis.

Use a step record with the intended driving load or displacement, inherited state, active regions, expected transition and observable outputs. For prestress or settling, inspect the equilibrium state at the end of the preload stage before applying service loading. For geometric nonlinearity check the load convention, such as a load fixed in space or a pressure following the deformed surface. Use deformed lever arms for moment balance when appropriate. Use [contact mechanics](../../fea-connector-contact/references/engineering-method.md) for interface direction, switching and bolt force recovery.

## Verify material history

Check the elastic stiffness, yield criterion, hardening or internal state law and the stress/strain measures expected by the material and the result request. For monotonic uniaxial tension with linear isotropic work hardening, use `ε = σ/E + εp` and `σ = σy + Hεp` after initial yield. Here `H` is the stress slope versus plastic strain. In elastic unloading before reverse yield the accumulated plastic strain stays fixed and stiffness returns to the elastic slope. Assess whether the support conditions allow lateral contraction before using a uniaxial stress reference. Constrained lateral strain, rate dependence or different reversal behavior needs a reference consistent with that mechanism.

Distinguish total strain, the plastic strain tensor and the accumulated equivalent plastic strain. Choose a comparison in the physical frame and at the same recovery position. For large strains compare material curves and results using consistent measures.

## Verify each accepted state

Match the requested time or progression coordinate to the attained load, accepted increment and result state. A cumulative load-factor label can increase during unloading. Use actual load selection and signed reactions to resolve the physical state. Compare displacement, resultant forces and moments, contact or material variables and an appropriate work or energy balance. Account for damping, stabilization and plastic dissipation when they affect the chosen comparison.

At a transition, refine increments without changing the physical load path, and test mesh sensitivity where localization or contact governs. A residual reduction alone does not establish invariant work, equilibrium, state transfer or an adequate model. Use the smallest independent change that separates plausible explanations.
