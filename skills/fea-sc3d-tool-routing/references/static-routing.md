# Static structural routing by requested outcome

| Request | Start with | Evidence to bind |
|---|---|---|
| Linear static setup or result acceptance | [Linear static](../../fea-linear-static/SKILL.md) | Effective load case and restrictions, applied and reaction resultants, displacement and stress scope |
| Parameter or geometry change in an associative SOL 101 | [Parametric SOL 101](../../simcenter-parametric-sol101/SKILL.md) | CAD/FEM/SIM chain, unchanged physical intent, re-resolved regions and new effective deck |
| Nonlinear material, large displacement or sequential loads | [Multistep nonlinear](../../fea-multistep-nonlinear/SKILL.md) | Actual solution family, step controls, constitutive model and inherited state |
| Contact opening, friction, connector transfer or bolt preload | [Connector/contact](../../fea-connector-contact/SKILL.md) | Paired regions, frame, preload/lock sequence, load path, contact and bolt witnesses |
| Failed or apparently converged nonlinear job | [Multistep nonlinear](../../fea-multistep-nonlinear/SKILL.md) | Final accepted increment, active control and related residual/diagnostic summaries |
| Eigenvalue buckling or preload buckling factor | [SOL 105 interpretation](../../fea-results-interpretation/references/sol103-sol105-quant.md) | The actual static reference and buckling subcase, eigenpairs and validity of the linearized interpretation |
| Read or export a native SIM, inspect an effective deck, or recover results | [Siemens tool routing](../SKILL.md) | Exact operation, native binding or immutable run artifact |

Classify by the physical behavior and requested decision. Preserve the distinction between preload loading, locked preload and service history. Resolve any ambiguous use of “static” from the actual model, load sequence and decision.
