---
name: fea-model-preparation
description: "Choose and verify FEA idealizations, model hierarchy, persistent regions, coordinate transforms and conservative load paths. Use for CAD-to-FEM preparation, owned revisions, associativity and global-to-detail transfer; CAD design belongs to NX."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Model Preparation

Use actual geometry, sections, material and support evidence. Preserve owner/revision, occurrence transforms and physical region membership. Assess reduction error at each requested QoI; global agreement cannot certify omitted local features.

## Engineering method and resources

- [Hierarchy, idealization and transfer](references/engineering-method.md).
- [Section mechanics](references/mechanics.md).
- [Quantitative support-arm case](references/worked-case.md).
- [Original CAD import, owned meshing and independent analysis](references/imported-cad-v4.md).
- Siemens API path (source: fea_expert_agent_plugin/docs/engineering/vendor-api-workflows.md).

## Executable starting point

```sh
python -m fea_agent assess-assembly examples/engineering_v2/mounted_assembly_model.json
```

A 118 kg hierarchical assembly must retain its off-center inertia. A transfer with correct 2000 N force but missing -2000 N m moment is rejected.

## Completion boundary

Return the calculated or evidence-backed decision, its physical assumptions, the strongest falsifier exercised, and the specific unresolved dependency. Use qualified Engineering Desktop Runtime capabilities for native effects; this skill and source calculations do not create host authority. Preserve separate source, native, solver and engineering outcomes.
