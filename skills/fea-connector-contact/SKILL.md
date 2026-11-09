---
name: fea-connector-contact
description: "Analyze preloaded bolted joints, connector stiffness, unilateral contact, friction, separation and pressure/load introduction. Use for pretension-lock-thermal-service histories and thread-load interpretation; post-slip redistribution and local capacity need separate models."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Connector Contact

Derive bolt/member stiffness from physical inputs and solve compatibility with active contact. Preserve pretension state and exact step inheritance. Evaluate per-contact friction, force/moment balance and energy before interpreting bolt stress or proposing a fix.

## Engineering method and resources

- [Joint engineering method](references/engineering-method.md).
- Complete equations and worked history (source: fea_expert_agent_plugin/docs/engineering/bolted-joint-workflow.md).
- Pressure API and region audit (source: fea_expert_agent_plugin/docs/engineering/vendor-api-workflows.md).

## Executable starting point

```sh
python -m fea_agent assess-joint examples/engineering_v2/joint_flange8_thermal_service.json
```

Eccentric service opens B2–B5 and reaches 56.048 kN maximum bolt force. Local slip can begin even when global shear and torque capacity bounds appear adequate.

## Completion boundary

Return the calculated or evidence-backed decision, its physical assumptions, the strongest falsifier exercised, and the specific unresolved dependency. Use qualified Engineering Desktop Runtime capabilities for native effects; this skill and source calculations do not create host authority. Preserve separate source, native, solver and engineering outcomes.
