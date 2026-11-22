# Diagnose the effective nonlinear problem

## Contents

- [Reconstruct the problem](#reconstruct-what-the-solver-actually-attempted)
- [Levels of conclusion](#separate-three-levels-of-conclusion)
- [Convergence checks](#diagnose-an-apparently-converged-increment)
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

Select the formulation by the active physics, load path and supported element,
material and step combinations. Check the meaning of each control in the exact
solver family and release. For Simcenter Nastran use
[nonlinear static input and output](../../simcenter-nastran/references/nonlinear-static-io.md).
An iteration limit cannot repair wrong region membership, absent preload,
incompatible degrees of freedom or a missing physical restraint.

## Separate three levels of conclusion

An **observed defect** is directly supported by the effective input or a parsed
diagnostic, such as an absent active control, an invalid bolt cut or an incorrect
restored-state predecessor.
A **computed inconsistency** is an independent invariant failure: force balance,
energy budget or an explicit active convergence tolerance.
A **root-cause hypothesis** explains a trend but remains falsifiable: contact
chatter could arise from excessive penalty, a large increment, bad geometry or
lost load path. Rank these separately so a plausible cause is not advertised
as a proven one.

Inspect all applicable equilibrium, contact compatibility and preload criteria
for the attained state. Retain the normalization and tolerance for each criterion.
When the solver accepts an increment using relaxed criteria, record the original
and relaxed thresholds together with the state being accepted. Compare that state
with the requested load and the intended predecessor. Check unstable pivots using
[instability and path following](instability-and-path-following.md).

Check signed physical resultants in one frame. For a component check, project external and reaction forces onto a declared unit axis and compare their signed sum with the dimensional absolute-plus-relative budget.
For a transient or whole assembly, include inertia and every external interface;
do not double-count internal contact forces. Compare artificial stabilization
energy with the declared strain-energy fraction budget. A residual reduced by
unphysical stiffness/damping may represent a different model. Record the axis and check the other force components and moments when the claim requires full equilibrium.

## Diagnose an apparently converged increment

Compare consecutive accepted increments using a consistent signed convention and the same support and contact scopes. Check that the preload state and step dependency reached the intended step and that residuals, equilibrium and histories agree. Refine the increment while holding the formulation and physical inputs fixed.
When a limit point is plausible, compare attained load and displacement with an
admissible path-following or displacement-controlled run. For contact-driven
oscillations, perturb enforcement separately and track penetration and traction.
Compare the same physical state before judging the effect of either change.

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
