---
name: simcenter-aerostructures-margin-of-safety
description: "Set up or audit Aerostructures margin calculations, allowables and governing load cases."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Aerostructures margin of safety

Bind each failure mode to the appropriate shell, beam or region and the exact load case, recovery location, units and sign convention. Validate geometry and material allowables for the observed thickness, stability assumptions, temperature and loading direction. For a linear scalar reserve factor evaluate allowable over applicable demand and subtract one. Use each interaction method's failure equation to obtain its reserve factor.

Read [Knowledge Fusion and method schemas](references/kf-extractproperty-and-ms-methods.md) for associative inputs. Resolve property names from the installed method and confirm evaluated values. Audit `.msz` and `.mslog` against the calculation, load case, source evidence, warnings, and minimum margin. Any requested Word report uses the applicable supplied template and artifact readback.
