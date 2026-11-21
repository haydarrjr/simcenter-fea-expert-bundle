# NVH operational load identification

When loads are measured at the intended ports, use the measured loads with their calibration and phase reference. For an inverse estimate, bind transfer functions `H` and operational responses `y` from compatible states, mapped DOFs and calibrated channels. Use the stiffness or transfer formulation that matches what was measured, including the interface and boundary conditions.

For complex `H(f)f(f)≈y(f)`, scale channels consistently with units and noise, inspect singular values, rank and condition across frequency, and choose a regularization rule supported by the data. Multiple observations per unknown help only when they add independent information. Expose weakly observable load combinations and frequency bands. Do not hide a rank deficiency in one broadband averaged condition number.

Verify reconstruction by comparing both fit residual and at least one independent target, or explicitly qualify the inference as lacking independent target evidence. Perturb noise and rank cutoff to establish robustness. Use [TPA](nvh-transfer-paths.md) if the task after identification is attribution at a receiver. For partially correlated references and virtual sources use [PCA](nvh-principal-components.md).

For the native 2612 Vibro-Acoustic route, bind the separate response and FRF files, the correct FRF formulation, the quantity and sorting, and the mapped measured and model DOFs before solving. The `GetSubcases()` accessors read configured filters. Verify available cases from the actual source and confirm that mapping completed. Check the Hermes log and recovered complex amplitudes and phases. A successful builder commit and a results container can accompany a failed solve when the configuration lacks `InverseStiffnessNodeMapping`.

[Simcenter 3D Load identification](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1685198?audience=external)
