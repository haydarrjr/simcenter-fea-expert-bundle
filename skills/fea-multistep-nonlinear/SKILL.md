---
name: fea-multistep-nonlinear
description: "Plan or diagnose nonlinear structural load paths, plasticity, large deformation, convergence and postbuckling."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Multistep nonlinear analysis

Identify the mechanism that changes the response, its load history and the required acceptance quantity. Use [load-path verification](references/open-solver-workflows.md) for inherited state, material behavior and accepted increments. Use [diagnostics and controls](references/engineering-method.md) for effective solver controls, convergence and recovery.

For changing contact or preload follow [connector and contact mechanics](../fea-connector-contact/SKILL.md). For loss of stability or postbuckling use [instability and path following](references/instability-and-path-following.md). For Simcenter Nastran output requests and release-specific solver behavior consult [nonlinear static input and output](../simcenter-nastran/references/nonlinear-static-io.md).
