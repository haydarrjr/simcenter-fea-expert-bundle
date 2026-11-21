---
name: fea-acceptance-verifier
description: "Accept or reject an FEA engineering claim using independent physical and numerical evidence."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Acceptance Verifier

Reconcile model, revision, mesh, loadcase, step, frame and source before comparing results. Use the [acceptance decision method](references/engineering-method.md). Exercise independent force and moment balance, contact state, energy and applicable QoI comparisons. Prespecify tolerances and document assumptions. Distinguish computed contradictions, hypotheses and missing host evidence. A converged run can still fail local transfer, artificial-energy and final-load checks.

Keep configuration readback, solver completion, result origin and engineering acceptance separate. Use corroborating official MCP reads or original artifacts for result provenance. Report PARTIAL, FAIL, UNVERIFIED or NOT_RUN for the specific stage when justified.
