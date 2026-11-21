# NVH operational load identification

When loads are measured at the intended ports, use the measured loads with their calibration and phase reference. For an inverse estimate, bind transfer functions `H` and operational responses `y` from compatible states, mapped DOFs and calibrated channels. Use the stiffness or transfer formulation that matches what was measured, including the interface and boundary conditions.

For complex `H(f)f(f)≈y(f)`, scale channels consistently with units and noise, inspect singular values, rank and condition across frequency, and choose a regularization rule supported by the data. Multiple observations per unknown help only when they add independent information. Expose weakly observable load combinations and frequency bands. Do not hide a rank deficiency in one broadband averaged condition number.

Verify reconstruction by comparing both fit residual and at least one independent target, or explicitly qualify the inference as lacking independent target evidence. Perturb noise and rank cutoff to establish robustness. Use [TPA](nvh-transfer-paths.md) if the task after identification is attribution at a receiver. For partially correlated references and virtual sources use [PCA](nvh-principal-components.md).

For the 2612 Hermes `LoadIdentification` route, bind separate response and FRF files with a common frequency grid, coordinate convention and explicit physical quantities. The inverse route takes response over unit force. With identical response channel identities in both sources, the installed schema supports identity matching with the optional `nodemapping` omitted. Supply a validated mapping dataset for nonidentical identities. Check source and destination node and DOF coverage before choosing either route. The NXOpen `GetSubcases()` accessors report configured filters. A named mapping must exist in the bound data source before dispatch.

Require successful solver completion, the intended force dataset and full complex readback on the anticipated frequency grid. Inspect per-frequency rank and conditioning, then compare amplitude and phase against an independent load or receiver. For an external Hermes result in Simcenter 3D, use the exact SC_H5 data definition and select the node, component and subcase before querying the raw function. Convert from the active model unit system when comparing its values with solver-file data.

[Simcenter 3D Load identification](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1685198?audience=external)
