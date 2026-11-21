---
name: fea-durability
description: "Assess fatigue from signed load or stress histories and material life data."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Durability

Use the complete signed stress/strain time history, its model revision, location and frame, and the required fatigue mechanism. Inspect space/time resolution before counting cycles. Unsigned von Mises, a single stress view and modal eigenvector amplitude are insufficient histories.

Use [history assessment](references/history-assessment.md). For a fixed-direction elastic history, verify the assumption using the tensor, the mean stress treatment using compatible Sâ€“N evidence, and the finite-record treatment of residual half cycles. For elastic-notch/FKM or multiaxial/rotating stress, qualify the actual Simcenter durability method and its inputs. Preserve roughness, gradient, surface, statistical basis and plasticity limits. Retain raw history and distinct damage/life conclusions. Missing configuration, material or temporal evidence leaves the affected assessment NOT_RUN.
