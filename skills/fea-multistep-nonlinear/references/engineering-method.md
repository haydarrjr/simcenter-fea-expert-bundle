# Diagnose the effective nonlinear problem

## Contents

- [Reconstruct the problem](#reconstruct-what-the-solver-actually-attempted)
- [Levels of conclusion](#separate-three-levels-of-conclusion)
- [Worked investigation](#worked-apparently-converged-case)
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

Read the exact 2606 declaration before prescribing a card/value. In particular,
MAXBIS=0 has a different meaning and validity across these families. Increasing
an iteration limit cannot repair wrong region membership, absent preload,
incompatible DOFs or a missing physical restraint.

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

Check signed physical resultants in one frame. The trace requires a
`force_projection` with matching `frame_id`, three finite unit-axis components
and convention `SIGNED_DOT_PRODUCTS_IN_NEWTONS`. A norm is not a signed
component; a nonunit axis is rejected rather than normalized. For the implemented projection audit,
`|F_external+R_support|` must fit the declared absolute-plus-relative budget.
For a transient or whole assembly, include inertia and every external interface;
do not double-count internal contact forces. Compare artificial stabilization
energy with the declared strain-energy fraction budget. A residual reduced by
unphysical stiffness/damping may represent a different model. The output records
the declared axis and explicitly leaves full 3D force and moment equilibrium
unassessed. A balanced projection cannot establish transverse equilibrium.

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
