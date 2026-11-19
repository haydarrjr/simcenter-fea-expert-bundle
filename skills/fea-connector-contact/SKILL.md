---
name: fea-connector-contact
description: "Analyze preloaded bolted joints, connector stiffness, unilateral contact, friction, separation and pressure/load introduction. Use for pretension-lock-thermal-service histories and thread-load interpretation; post-slip redistribution and local capacity need separate models."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Connector Contact

Read [joint mechanics](references/engineering-method.md). Use Model Inspection and the effective deck to identify preload, interfaces, stiffness, contacts, local axes and load application. Bind BatchPost outputs to the actual nonlinear step and iteration. Compare bolt force, local opening/slip and contact work with an independently constructed compatibility and equilibrium reference, retaining pressure convention, area and lever arms.

Check bolt/thread and local pressure allowables only with applicable material and geometry evidence. Preserve the difference between preload control and locked adjustment. Report material, friction, rigidization or result gaps.
