---
name: fea-continuum-thermomechanics
description: "Verify Simcenter structural solids, conduction, heat balance, thermal stress, temperature histories and model applicability."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Continuum thermomechanics

Choose the physical QoI and a justified Simcenter/Nastran solid formulation. Use [solver investigation](../fea-solver-investigation/SKILL.md) for the actual MAT/property/element definitions, MPC/SPC and solution sequence. Obtain stiffness, density, conductivity, heat capacity, expansion and reference temperature from the assigned material evidence. Respect element order, stress recovery and model limits.

Read [equations and independent checks](references/engineering-method.md). Separate small-strain elastic, conduction, thermal history and sequential thermoelastic response. Verify force/moment/work and heat/storage/flux balance, Kelvin and maximum-principle bounds when applicable, and spatial/time-step refinement. Use [BatchPost](../batchpost-actions/SKILL.md) for signed stress/flux and actual temperatures, preserving position, time, labels and frame. Unsupported operations or unreturned result positions remain unverified.
