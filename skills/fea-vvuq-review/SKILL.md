---
name: fea-vvuq-review
description: "Verify numerical methods and solution convergence, distinguish input uncertainty from model-form error, and design discriminating validation studies. Use for GCI, sensitivity, robust comparisons and optimization credibility; do not infer reliability from arbitrary ranges."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Vvuq Review

Bind each comparison to the same physical quantity and state. Use independent or high-precision oracles and meaningful invariance tests. Treat active-set changes separately from smooth sensitivity; a converged reaction cannot certify local contact or peak stress.

## Engineering method and resources

- [VVUQ and sensitivity method](references/engineering-method.md).
- [Richardson/GCI implementation](references/constant-r-refinement.md).
- Joint reference model (source: fea_expert_agent_plugin/docs/engineering/bolted-joint-workflow.md).

## Executable starting point

```sh
python -m fea_agent assess-convergence examples/convergence_4_levels_v1.json
```

A ±10% preload scenario changes service maximum bolt force nonlinearly and reduces the open sector at +10%. Matching total force alone misses a 2000 N m transfer error.

## Independent fields and applicability

The source solids are compared with separately assembled scikit-fem matrices
and solutions, original archived Nastran fields, exact thermal decay and NASA
laminate coefficients. Shared NumPy/SciPy backends are an explicit independence
limit. Low-order bending may balance loads while missing refined displacement
by 9%. Temperature bounds and total/elastic/thermal strain are useful
applicability screens, not strength data. Compare mapped physical fields with
prescribed tolerances before inspecting results. The
physics method (source: fea_expert_agent_plugin/docs/engineering/multiphysics-v3.md) records original
sources, access depth and exact numerical outcomes. Keep material/boundary and
model-form uncertainty separate from roundoff and discretization error.

## Completion boundary

Return the calculated or evidence-backed decision, its physical assumptions, the strongest falsifier exercised, and the specific unresolved dependency. Use qualified Engineering Desktop Runtime capabilities for native effects; this skill and source calculations do not create host authority. Preserve separate source, native, solver and engineering outcomes.
