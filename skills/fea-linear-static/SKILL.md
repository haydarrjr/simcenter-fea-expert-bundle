---
name: fea-linear-static
description: "Set up or verify a linear static structural load case, its effective constraints and loads, and recovered displacements, reactions or stresses."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Linear static structural analysis

Bind the intended static load path, quantities, units and acceptance criteria. Establish small-motion and material-linear assumptions and decide whether the interfaces can be represented with fixed linear constraints. When load history, plasticity, changing contact or geometric stiffness govern the decision, use [nonlinear statics](../fea-multistep-nonlinear/SKILL.md).

1. Select idealization, material, section and mesh by the response of interest. Verify element/property/material assignments, support DOFs, independent load cases and load transfer in the intended frame.
2. For SOL 101, follow the [linear static method](references/sol101.md) and check [effective deck sets](../simcenter-nastran/references/deck-and-solutions.md). Use the [parametric SOL 101 skill](../simcenter-parametric-sol101/SKILL.md) when changing associative geometry or semantic regions.
3. Verify signed displacement, reaction and moment balance, and stress at the requested support and recovery location. Use an independent mechanics reference and refinement where the decision depends on local gradients. Match exports and comparisons to the exact solved state.
