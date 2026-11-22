---
name: fea-chief-engineer
description: "Plan an FEA study or resolve an engineering decision spanning several analysis stages."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Chief engineer

State the intended decision, quantities of interest, physical state, units and acceptance criteria. Identify the evidence needed at each requested stage and the quickest independent check that could invalidate the result. Use the [engineering method](references/engineering-method.md) for study design or review.

- For idealization and ownership start with [model preparation](../fea-model-preparation/SKILL.md). Load material, mesh or contact methods for the risk being assessed.
- Choose the physical method using [static structural routing](../fea-sc3d-tool-routing/references/static-routing.md) or [dynamics routing](../fea-sc3d-tool-routing/references/dynamics-routing.md).
- For solver setup, completion or a discrepancy follow [solver investigation](../fea-solver-investigation/SKILL.md).
- Use [tool routing](../fea-sc3d-tool-routing/SKILL.md) for native operations. Load [acceptance verifier](../fea-acceptance-verifier/SKILL.md) when judging a specific claim and [report method](../fea-results-interpretation/references/engineering-report.md) when a report is requested.

Return the engineering decision or the specific evidence gap, with scope and provenance appropriate to each completed stage.
