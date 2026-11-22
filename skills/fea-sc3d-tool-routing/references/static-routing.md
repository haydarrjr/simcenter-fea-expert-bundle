# Static structural routing by engineering decision

Identify the quantity to be accepted, the physical mechanism that controls it and the model state at which it is evaluated. For a request spanning several rows, verify the controlling physical state before interpreting a downstream result.

| Engineering decision | Start with | Evidence to bind |
|---|---|---|
| Elastic stiffness, support reaction or stress under fixed supports and interfaces | [Linear statics](../../fea-linear-static/SKILL.md) | Applicability of constant stiffness, effective loads and restraints, signed equilibrium, field recovery and mesh sensitivity |
| Update associated geometry or dimensions while retaining load and support intent | [Parametric SOL 101](../../simcenter-parametric-sol101/SKILL.md) | CAD/FEM/SIM relationship, remeshed regions, equivalent selections and new effective input |
| Thermal expansion, restraint or temperature-dependent structural response | [Thermal analysis](../../fea-thermal/SKILL.md) | Temperature transfer, reference state, thermal expansion convention and mechanical restraints |
| Response governed by yielding or evolving load history | [Nonlinear load path](../../fea-multistep-nonlinear/SKILL.md) | Constitutive law, load and control history, state inheritance and accepted increments |
| Restore a solver state or judge response under finite rotations or strains | [Restart and finite kinematics](../../fea-multistep-nonlinear/references/restart-and-finite-kinematics.md) | Restoration source, target time grid, discriminating continuation or defined kinematics, and result measures |
| Joint compliance, interface opening/slip, bolt preload or load transfer | [Connector/contact](../../fea-connector-contact/SKILL.md) | Resolved interface, gap, traction, preload/lock state and signed force and moment transfer |
| Buckling factor and mode about a specified reference state | [Eigenvalue buckling](../../fea-results-interpretation/references/sol103-sol105-quant.md) | Actual reference subcase and loading pattern, tangent and eigenpair interpretation |
| Critical point, loss of equilibrium or postbuckling along a nonlinear path | [Instability and path following](../../fea-multistep-nonlinear/references/instability-and-path-following.md) | Initial state, imperfections, governing equilibrium branch and attained load and displacement |
| Failed or apparently complete job with a suspect result | [Solver investigation](../../fea-solver-investigation/SKILL.md) and, where applicable, [nonlinear diagnostics](../../fea-multistep-nonlinear/references/engineering-method.md) | Exact run, effective controls, terminal diagnostics and achieved result state |

Use [Siemens tool routing](../SKILL.md) once the native operation or file action is known. Use the [acceptance verifier](../../fea-acceptance-verifier/SKILL.md) when the requested deliverable is an engineering verdict.
