# Simcenter Nastran nonlinear static input and output

Use this reference when checking a nonlinear static deck, planning result recovery or diagnosing a release-specific runtime response. Select the analysis by the physical mechanism in [nonlinear load-path verification](../../fea-multistep-nonlinear/SKILL.md).

## Select the solution formulation

Use SOL 106 for nonlinear statics covered by its available element, material and output formulations. Consider SOL 401 for supported staged preload, contact and mixed step types. Consider SOL 402 for supported nonlinear kinematics, step sequences or explicit subcase restoration. Compare capabilities against the exact release before selecting a sequence. [SOL 401 capabilities](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.multi_step_nonlinear/html/xid612413?audience=external) · [SOL 402 capabilities](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.multi_step_nonlinear/html/xid1604668?audience=external)

## Input, control and recovery

| Sequence | Resolve from the effective deck |
|---|---|
| SOL 106 | Resolve the selected `NLPARM` for each subcase. Check increments and intermediate output. Use `NLSTRESS` when nonlinear stress and accumulated plastic strain are required. Verify `MATS1` hardening input and the yield field when using bilinear hardening by `H`. [NLPARM](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.QRG/html/id508411?audience=external) · [MATS1](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.QRG/html/id508406?audience=external) |
| SOL 401 | Resolve `ANALYSIS`, `NLCNTL`, `TSTEP`, subcase dependence and any bolt preload controls. Check `LGDISP` and `LGSTRN` independently. Inspect equilibrium and the applicable contact and bolt convergence summaries. [SOL 401 subcase sequencing](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.multi_step_nonlinear/html/xid638709?audience=external) · [Contact convergence](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.multi_step_nonlinear/html/xid1201098?audience=external) |
| SOL 402 | Resolve `NLCNTL` to `NLCNTL2` and verify load interpolation, time increments and plasticity or creep controls for the step. Check `SEQDEP` and the `RSUB` predecessor for an intended nonsequential restart. State inheritance and the time coordinate are separate observables. [NLCNTL2](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.QRG/html/xid1270968?audience=external) · [Subcase dependency](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid2190520?audience=external) |

Resolve the selected control IDs for each step. Check the actual meaning of the convergence norm, bisection limit and any relaxed or best-attainable criteria. Values such as `MAXBIS=0` and the handling of a requested displacement criterion depend on the solver family. Inspect accepted increments and the equilibrium and, when applicable, contact and bolt summaries.

Read the requested result support and measure independently of the output name. For SOL 401/402, check actual step visibility of displacement, reactions, stress and `PLSTRN` during export. Preserve the total or intrinsic measurement convention and the actual time or increment of comparison.

For a SOL 401 bolt installation step, check the active `BOLTLD` and the bolt definition it selects. Check sequential dependence into service and request `BOLTRESULTS` and `BCRESULTS` for the intended entities. The F06 and the binary result reader can expose different fields. [Bolt preload](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.multi_step_nonlinear/html/xid924582?audience=external)

For a SOL 402 internal restart, resolve `SEQDEP=NO`, the selected `NLCNTL2` and the `RSUB` source, then compare the solver's restart positioning and target time grid. Check the supported combination of `LGDISP`, `LGSTRN` and `MATNL` when modeling large rotations. Use the stress measure reported by the applicable result table. [SOL 402 restart](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.multi_step_nonlinear/html/xid1602274?audience=external)

## Release-specific diagnostics

- For SOL 106, an older maintenance issue could omit `LIMIT1` from the exported plastic material definition. Inspect the active card in the current export before applying a release-specific remedy. [KB000153430](https://support.sw.siemens.com/en-US/knowledge-base/KB000153430_EN_US)
- In the observed 2612 SOL 401 run, `LGDISP=0` produced F06 fatal 9465. The small-displacement value `-1` was accepted. Resolve the intended setting using the installed solver's allowed values.
- In standalone 2612 SOL 401, requesting Solution Monitor with `sys442=2` and no connection produced F06 fatal 4551. Omit the monitor option for the observed unmonitored batch path. Check F06 diagnostics and achieved solution states even if a native setup check or launcher reports success.
- For the observed 2612 SOL 402 run, an OP2 produced with `PARAM,POST,-1` opened with an empty BatchPost catalog despite valid solved F06 output. An exported and solved `PARAM,POST,-2` deck exposed the requested states and fields. Verify the selected result format on the installed release against the attached or exported states.
