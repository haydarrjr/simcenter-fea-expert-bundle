# Structural instability and equilibrium paths

Define whether the decision concerns a linearized critical load, onset of instability along a nonlinear equilibrium path, or postcritical response. For a linearized eigenvalue check use [buckling interpretation](../../fea-results-interpretation/references/sol103-sol105-quant.md) with the actual preload state and reference load. The computed factor applies to that reference load pattern and tangent. Review the mode shape and separation from competing modes.

For a nonlinear stability problem:

- Identify the equilibrium path, potential limit point or bifurcation, and the controlling load and displacement measures. Screen for rigid-body mechanisms and contact opening before interpreting a negative pivot or near-zero tangent as physical instability.
- Choose control that can follow the intended branch. Load control can fail at a limit point. Use a suitable displacement control when its coordinate remains monotone on the relevant branch. Use a documented path-following method when both driving force and displacement reverse. Check the installed solver's supported load patterns, step types and restrictions. [SOL 401 nonlinear buckling](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.multi_step_nonlinear/html/xid1396931?audience=external)
- For an imperfection-sensitive structure, justify imperfection shape, signed amplitude and model uncertainty. Compare credible alternatives and check mesh and step sensitivity around the critical region. Keep critical-load and postbuckling claims tied to the actual boundary conditions, preload and material law.
- Record the attained load and displacement path, reaction balance and deformation modes. A stabilized or dynamic run may follow a different path. Verify the artificial or kinetic contribution and its effect on the proposed design quantity before interpreting a result as quasistatic.
