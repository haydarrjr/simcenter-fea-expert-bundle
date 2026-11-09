---
name: fea-composite-laminates
description: "Analyze anisotropic composite laminates using ABD coupling, thermal gradients, mixed generalized constraints and ply-surface stress. Use for stacking/orientation errors, unsymmetric thermal warpage and composite OP2 ply interpretation; distinguish CLT from interlaminar failure."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Composite laminates

Inspect the actual stacking sequence and material axes before using a scalar
failure number. Call `fea_analyze_laminate` for classical laminate response;
use `fea_inspect_artifact` to inspect original ply result identities. Get the
`unsymmetric_laminate` request from `fea_get_example` for the input contract.

1. Declare bottom-to-top ply order, thickness, angle, lamina E1/E2/G12/nu12 and
   thermal coefficients. Require positive-definite constitutive energy.
2. Preserve A, B and D, thermal force/moment resultants and prescribed generalized
   strain components. Do not erase B because the analyst expects membrane behavior.
3. Solve membrane strain and curvature with work-conjugate engineering shear.
   Recover top/bottom stress for every named ply in both global and material axes.
4. Reconstruct applied resultants from recovered fields and challenge ply order,
   angle sign and midplane/reference-temperature assumptions.
5. If strength is requested, require the corresponding qualified strength/failure
   model, allowables, load ratio and environmental basis. CLT stresses do not
   supply transverse shear, delamination or damage evolution.

Read [laminate method and wrong-answer tests](references/engineering-method.md).
Return signed ply fields and coupling evidence, not only an envelope. Retain
each recovery surface when joining Siemens/OP2 output to the source calculation.
