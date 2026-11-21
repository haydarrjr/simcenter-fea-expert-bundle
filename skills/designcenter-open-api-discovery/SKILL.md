---
name: designcenter-open-api-discovery
description: "Resolve an unfamiliar NXOpen class, member, signature, or execution pattern."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# NXOpen API discovery

Start with the [qualified CAE operations](../designcenter-open-journal-authoring/references/cae-2612.md) when they match. For an unfamiliar member, use the current Designcenter Open catalog: an exact class and member query for known names, or one targeted keyword, semantic or pattern query for an unknown name. Read the signature and declaring type, including inherited interfaces and enum types.

Treat missing or incomplete index results as limits of the index. Use the matching Siemens NXOpen Python reference and a narrow read-only probe on the installed build when the class, overload or binding remains uncertain. Record the exact build, language, member, and observed behavior. Use [journal authoring](../designcenter-open-journal-authoring/SKILL.md) to validate executable behavior.
