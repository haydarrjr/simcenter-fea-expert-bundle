# Nastran external superelements

Bind two jobs and the interface. For generation establish the reduction basis and retained boundary translations/rotations, fixed-interface or static reduction choices, residual vectors where relevant, and retained recovery. For assembly verify interface coordinates and DOFs, attachment mapping, units, file IDs, and that the reduced matrices belong to that exact generation revision.

Inspect the effective generation `EXTSEOUT` options, format and output unit. Resolve assembly `ASSIGN` and file-unit mappings, `SEBULK`, `SECONCT` and their dependencies through [artifact forensics](../../fea-artifact-forensics/SKILL.md). The matrix file and a field-result file may have the same extension. A file opening in a field viewer gives no coverage for matrices or recovery. Resolve missing, stale or out-of-scope dependencies before submission.

Use an independent full assembly comparison at the target ports and recovery locations. Check interface force balance, eigenfrequencies and matched modes/subspaces, plus FRFs in the band of interest. Verify requested internal recovery with an actual export. Report each generation, assembly and post-processing outcome. Use [Solution Sequence](../../fea-solver-investigation/references/solution-sequence.md) only for a qualified solver route.

[EXTSEOUT](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.QRG/html/id509506?audience=external) · [External Superelement Examples](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.super/html/id790054?audience=external)
