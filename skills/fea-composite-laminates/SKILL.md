---
name: fea-composite-laminates
description: "Analyze anisotropic composite laminates using ABD coupling, thermal gradients, mixed generalized constraints and ply-surface stress. Use for stacking/orientation errors, unsymmetric thermal warpage and composite OP2 ply interpretation; distinguish CLT from interlaminar failure."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Composite laminates

Bind actual layup order, ply IDs, orientation, thickness, reference surface, temperature/moisture condition, transformed stiffness and sign conventions. Use the effective deck and documented Simcenter model reads for laminate properties, and [BatchPost](../batchpost-actions/SKILL.md) or qualified result reads for original ply/face fields. Never infer interlaminar strength from classical laminate theory.

Read [laminate method](references/engineering-method.md). For an independent ABD check, integrate transformed ply stiffness through the declared signed thickness, retain the (B) coupling matrix, and check thermal resultants and strain/curvature signs. Compare individual ply stresses/strains in their material frame with evidenced allowables and stated failure criterion. Missing layup state, fields or allowables limits the decision.
