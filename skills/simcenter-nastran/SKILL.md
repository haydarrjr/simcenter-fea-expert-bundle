---
name: simcenter-nastran
description: Qualify Simcenter Nastran SOL 101/103 decks, identify effective solver inputs and diagnostics, and route authorized Windows batch jobs without rediscovering NXOpen or searching the installation.
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Simcenter Nastran

1. Establish the exact model, solution and subcase or the exact archive triplet. For native setup use the [2612 CAE operation catalog](../designcenter-open-journal-authoring/references/cae-2612.md), not generic API discovery.
2. Read [deck and solution checks](references/deck-and-solutions.md). Use the official diagnostic MCP if advertised; otherwise the local text-only [deck helper](scripts/deck.py) covers a deliberately limited SOL 101/103 profile. Unknown coverage is not a pass.
3. Use [Solution Sequence](../fea-solver-investigation/references/solution-sequence.md) for executable/translator selection, batch admission, exit reconciliation, conversion and BatchPost. Use [static verification](../fea-solver-investigation/references/engineering-method.md) or [free-free verification](../fea-dynamics/references/sol103-free-free.md) for acceptance.

Use Siemens Help `STS_SIMCENTER3D` with the installed release requested first, then 2606 if not served. Record the **resolved** documentation version; it is not runtime evidence. Prefer the [Quick Reference Guide](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.QRG?audience=external) for the exact entry and the [User's Guide](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.User?audience=external) for the solver workflow. For diagnostics include the exact message number/module. Do not query docs for already qualified operations unless the release or assumption changes.
