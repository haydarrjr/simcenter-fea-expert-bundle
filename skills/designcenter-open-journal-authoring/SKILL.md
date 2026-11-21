---
name: designcenter-open-journal-authoring
description: "Author or test an NXOpen Python journal, or run a scoped operation in Designcenter."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# NXOpen Python journals

Use the [qualified CAE operations](references/cae-2612.md) for a known operation. Resolve unfamiliar members with [API discovery](../designcenter-open-api-discovery/SKILL.md). Bind `BaseWork` and `BaseDisplay` for CAE data and confirm the intended part or owning FEM.

- Use `dcopen-run-snippet-tool` for a small isolated probe or `dcopen-run-journal-tool` for a complete sandbox journal. Use the runner's entry point and check its inner status and expected output. See [execution contracts](references/execution.md) for entry points and empty stdout.
- Use `dcopen-execute-tool` for the current native session and return structured readback from `main(args)`. Admit changes through the [native runtime gate](../fea-native-runtime-gate/SKILL.md), using the exact authorized operation and an independent witness. Qualify persistence and solver submission individually.
- Use the API's builder lifecycle and clean up builders in `finally`. Keep model parameters typed and bound to the target. Use imports and language features admitted by the actual runner.
