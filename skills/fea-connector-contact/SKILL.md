---
name: fea-connector-contact
description: "Assess bolt preload, connector load transfer, contact opening, or friction."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Connector Contact

Read [joint mechanics](references/engineering-method.md). Use Model Inspection and the effective deck to identify preload, interfaces, stiffness, contacts, local axes and load application. Bind BatchPost outputs to the actual nonlinear step and iteration. Compare bolt force, local opening/slip and contact work with an independently constructed compatibility and equilibrium reference, retaining pressure convention, area and lever arms.

Check bolt/thread and local pressure allowables only with applicable material and geometry evidence. Preserve the difference between preload control and locked adjustment. Report material, friction, rigidization or result gaps.

For changing contact states, use [contact convergence](references/contact-convergence.md) to verify initial gap, orientation, load history, reactions and normal force. Compare a solved opening–closure–reopening cycle or an elastic contact benchmark at matched physical states when qualifying a method. Use the [nonlinear static I/O](../simcenter-nastran/references/nonlinear-static-io.md) for solver selectors and diagnostic output.
