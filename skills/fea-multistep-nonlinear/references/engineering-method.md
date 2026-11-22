# Diagnose the effective nonlinear problem

## Contents

- [Reconstruct the problem](#reconstruct-what-the-solver-actually-attempted)
- [Levels of conclusion](#separate-three-levels-of-conclusion)
- [Worked investigation](#diagnose-an-apparently-converged-increment)
- [Recovery](#recovery-and-outcome)

Use the exact-release Siemens Help API and the current global catalog to
qualify native operations. Ground diagnosis in the actual submitted deck, job
and achieved result state. Use the [multistep load-path checks](open-solver-workflows.md)
to evaluate plastic, contact and thermal histories recovered from the result.

## Reconstruct what the solver actually attempted

Obtain the effective deck, run log and result-step identity. Bind model revision,
mesh revision, owner, coordinate frame, case, solver release and artifact hashes. Resolve the
global and local Case Control scopes. State inheritance and load selection
inheritance are different: a later static subcase can retain a deformed state
while removing an earlier service load that is no longer selected.

Use an advertised Nastran deck reader or scoped original text. Preserve line
provenance and the applicable continuation and numeric conventions. Report
unresolved INCLUDEs or unsupported executive options.

Choose controls by actual solver family:

| Family | Effective control path | Important distinction |
|---|---|---|
| SOL106 | NLPARM Case Control → NLPARM bulk ID | Full Newton can replace requested U convergence with work convergence; nonconverged best-attainable continuation is possible under documented settings |
| SOL401 | NLCNTL Case Control → NLCNTL bulk ID | Default contact criteria and EQU/CON/BLT summaries have their own semantics |
| SOL402 | NLCNTL Case Control → NLCNTL2 bulk ID | Relaxed criteria, time-step controls and RSUB restoration are not SOL401 options copied under another name |

Select SOL 106 when its supported nonlinear static formulation and output cover the intended load/displacement path. Consider SOL 401 for a multistep study whose contact, preload and static or other step combinations fit its formulation. Consider SOL 402 when supported nonlinear kinematics, step sequences or explicit restoration drive the model. Check the exact release's supported elements, materials and requested results before choosing. [SOL 401 capabilities](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.multi_step_nonlinear/html/xid612413?audience=external) · [SOL 402 capabilities](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.multi_step_nonlinear/html/xid1604668?audience=external)

Read the declaration for the installed solver release before prescribing a card or value. In particular,
MAXBIS=0 has a different meaning and validity across these families. Increasing
an iteration limit cannot repair wrong region membership, absent preload,
incompatible DOFs or a missing physical restraint.

In 2612 SOL 401, `PARAM,LGDISP,0` produced F06 user fatal 9465 even though native setup check and the batch log reported successful completion. Use the SOL 401-specific `LGDISP` values and check `LGSTRN` independently. Resolve actual `ANALYSIS`, `TSTEP`, `NLCNTL` and the subcase dependency in the newly exported deck. [SOL 401 subcase sequencing](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.multi_step_nonlinear/html/xid638709?audience=external)

## Separate three levels of conclusion

An **observed defect** is directly supported by the effective input or a parsed
diagnostic: for example, SOL401 BOLTLD selected in an ordinary service subcase,
an absent selected nonlinear control, an invalid bolt cut or a wrong RSUB.
A **computed inconsistency** is an independent invariant failure: force balance,
energy budget or an explicit active convergence tolerance.
A **root-cause hypothesis** explains a trend but remains falsifiable: contact
chatter could arise from excessive penalty, a large increment, bad geometry or
lost load path. Rank these separately so a plausible cause is not advertised
as a proven one.

For SOL401, equilibrium status alone is insufficient. Inspect the final
applicable contact and preload summaries. Contact relative-displacement checks
can fail even when selected contact norm columns appear satisfactory. For
SOL402, preserve original and relaxed force/energy criteria separately. The
bounded source pages do not justify inventing a universal logical combination
of every convergence branch.

For SOL 402, resolve `NLCNTL` to its actual `NLCNTL2` record. Check the load interpolation choice, increment controls, and subcase-level material settings. For sequentially dependent steps, compare the previous accepted state with the start of the next step. For nonsequential branches, validate any `RSUB` predecessor explicitly. The restored state and the time coordinate require separate checks. A negative pivot is a diagnostic that can reflect instability. Check constraints, contact and the expected equilibrium path before changing the method or stabilization. [NLCNTL2](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.QRG/html/xid1270968?audience=external) · [Subcase dependency](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid2190520?audience=external) · [Siemens KB on negative pivots](https://support.sw.siemens.com/en-US/knowledge-base/KB000179582_EN_US)

Check signed physical resultants in one frame. For a component check, project external and reaction forces onto a declared unit axis and compare their signed sum with the dimensional absolute-plus-relative budget.
For a transient or whole assembly, include inertia and every external interface;
do not double-count internal contact forces. Compare artificial stabilization
energy with the declared strain-energy fraction budget. A residual reduced by
unphysical stiffness/damping may represent a different model. Record the axis and check the other force components and moments when the claim requires full equilibrium.

## Diagnose an apparently converged increment

Compare consecutive accepted increments using a consistent signed convention and the same support and contact scopes. Check that the preload state and step dependency reached the intended step and that residuals, equilibrium and histories agree. Use a smaller increment or targeted contact change to discriminate between numerical difficulty and loss of load path.

## Recovery and outcome

For preload loss, prove the predecessor or restored-state identity and compare
zero-service bolt strain/force and contact state. For a bolt-cut diagnostic,
verify the cut separates the intended physical region and the axis is defined.
For penetration with falling residual, isolate contact enforcement and normal
orientation. For excessive artificial energy, reduce stabilization while
preserving a physical constraint path, then compare engineering QoIs.

Create native steps, loads or jobs only through verified API owners and current
Runtime capability/admission. An uncertain operation outcome requires readback
and reconciliation before retry, especially for solving or persistent builders.
Report source findings, documented behavior, source-mocked integration and
actual host execution separately. No parsed control excerpt, invented step
integer or successful source test establishes a valid nonlinear engineering
solution.
