---
name: fea-thermal
description: "Reason about heat balance, temperature mapping, stress-free references and thermo-structural restraint. Use for differential expansion, temperature-sequenced joints and mounts; imported temperature fields are not automatically validated heat-transfer solutions."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Thermal

Identify reference, absolute and applied temperatures, sinks, ambient histories, convection/radiation and contact conductance from live or original artifacts. Establish thermal state and material applicability before stress recovery. Check steady heat balance and transient storage/flux, and compare with independent conduction or thermal mass bounds where applicable.

Use [engineering method](references/engineering-method.md) and [continuum thermomechanics](../fea-continuum-thermomechanics/SKILL.md). Separate thermal, elastic and total strain; retain the previous thermal state and actual load history. Check constrained versus free expansion and preload/contact sensitivity. Use qualified Simcenter/Nastran operations where advertised and [BatchPost](../batchpost-actions/SKILL.md) for exact temperature, flux and stress states. Treat unextracted detail as unavailable.
