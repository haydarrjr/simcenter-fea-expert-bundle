---
name: fea-mesh-quality
description: "Design and assess mesh approximation, element geometry, connectivity and QoI convergence. Use for TRI3/TET4 checks, coincident nodes, refinement studies and meshing API preparation; a valid element shape does not prove solution accuracy."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Mesh Quality

Identify element family, solver convention, order, mesh revision, collector and regions critical to the QoI. Use [Model Inspection mesh info](../simcenter-3d-mesh-inspection/SKILL.md) and [quality review](../simcenter-3d-mesh-quality-review/SKILL.md). Record failed counts, actual evaluated population and element/label location. A null result or an unavailable per-element metric remains unverified.

Use [mesh method](references/engineering-method.md) and [TRI3/TET4](references/tri3-tet4.md) for applicable geometric checks. For Tet10, distinguish corner shape from curved mapping/Jacobian and integrate/check shape on the documented locations across the actual element. Apply family-specific thresholds. Record whether free edges are intentional. Inspect loads/supports and hotspot localization before refinement. Run a QoI-specific comparison through [VVUQ](../fea-vvuq-review/SKILL.md). A passed shape check alone never establishes convergence.
