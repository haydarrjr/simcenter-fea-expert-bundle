# NVH principal components

For partially correlated spectral references, estimate the cross-spectral matrix on a common, calibrated frequency grid. Check stationarity within the analysis window, Hermitian symmetry and positive semidefiniteness using the [spectral checks](../../fea-random-response/references/engineering-method.md).

At each frequency decompose `Sxx = UΛUᴴ`. Eigenvalues represent component spectral power in the chosen normalization. Inspect rank, noise floor, discarded power and reconstruction error. Align component subspaces when nearly repeated eigenvalues make individual vectors unstable. Compare the reconstructed receiver spectrum to measured or independent data before explaining a residual. Interpret the components as virtual references unless separate physical evidence supports a source assignment.

For forward structural response from an input PSD/CSD use [random response](../../fea-random-response/SKILL.md). For individual physical paths use [TPA](nvh-transfer-paths.md).

The native 2612 PCA solution uses a Vibro-Acoustic SIM and the Acoustics and Vibration manager. Treat creation and reopen of the solution as native object evidence. The documented native PCA workflow requires a Testlab project supplying matching auto-power and cross-power functions. Preserve that source and independently compare the eigenvalue and response reconstruction. A matrix calculation alone can verify the mathematics on supplied data. [PCA workflow](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1929446?audience=external)

[Simcenter 3D Principal component analysis](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1929445?audience=external)
