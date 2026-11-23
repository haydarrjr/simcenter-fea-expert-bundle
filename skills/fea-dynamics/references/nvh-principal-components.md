# NVH principal components

For partially correlated spectral references, estimate the cross-spectral matrix on a common, calibrated frequency grid. Check stationarity within the analysis window, Hermitian symmetry and positive semidefiniteness using the [spectral checks](../../fea-random-response/references/engineering-method.md).

At each frequency decompose `Sxx = UΛUᴴ`. Eigenvalues represent component spectral power in the chosen normalization. Inspect rank, noise floor, discarded power and reconstruction error. Align component subspaces when nearly repeated eigenvalues make individual vectors unstable. Compare the reconstructed receiver spectrum to measured or independent data before explaining a residual. Interpret the components as virtual references unless separate physical evidence supports a source assignment.

For forward structural response from an input PSD/CSD use [random response](../../fea-random-response/SKILL.md). For individual physical paths use [TPA](nvh-transfer-paths.md).

For supported 2612 installations, use Hermes `PrincipalComponentAnalysis` with typed SC_H5 acceleration auto-power and complex cross-power data. Supply the reference diagonal through auto-power and off-diagonal pairs through cross-power. Use a common frequency grid and one consistent pair ordering. Supply response-to-reference cross-power terms for each requested receiver. Verify the assembled Hermitian reference matrix together with admitted reference and receiver DOFs, the singular-value spectrum and rank. Reconstruct the receiver power from the sum of squared magnitudes of its virtual spectra and compare it with independent `h Sxx hᴴ`.

Use the resulting physical definitions for virtual-reference auto-power and virtual referenced spectra when reading the SC_H5 in Simcenter 3D. Query the exact principal-component subcase for each virtual spectrum. The Testlab project workflow is `TBD`. [PCA workflow](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1929446?audience=external)

[Simcenter 3D Principal component analysis](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1929445?audience=external)
