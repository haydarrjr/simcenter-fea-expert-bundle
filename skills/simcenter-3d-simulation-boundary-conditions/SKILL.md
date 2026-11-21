---
name: simcenter-3d-simulation-boundary-conditions
description: "Inventory active SIM loads, constraints and simulation objects, and trace their effective solution or step membership."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Boundary condition inspection

Bind the SIM and use `boundary-condition-tool` for the advertised inventory. Record solution, scope, selected region, coordinate frame, units, and available applied values. The inventory alone does not establish membership in each solution or subcase. Use [CAE solution readback](../designcenter-open-journal-authoring/references/cae-2612.md) for solution and step BCs. Confirm effective control and set IDs in the associated solver deck when needed.

An empty field may reflect scope or a missing reader. Keep undefined, unassigned, unavailable and confirmed zero distinct.
