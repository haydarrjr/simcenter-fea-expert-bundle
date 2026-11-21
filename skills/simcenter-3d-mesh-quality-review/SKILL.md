---
name: simcenter-3d-mesh-quality-review
description: "Read native Simcenter mesh quality metrics, failure counts and the checked element population."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Native mesh quality

Use `mesh-quality-tool` for the bound part and requested mesh or collector. Report element type and order, total elements and the checked population with each available statistic. `qualityCheckedElements=0` gives no evidence of acceptable quality even when min, max, average and failed count are zero. Missing or inapplicable metrics stay unverified.

Apply thresholds only for the actual formulation and engineering quantity. Use [mesh quality](../fea-mesh-quality/SKILL.md) for geometry checks or convergence independent of the tool summary.
