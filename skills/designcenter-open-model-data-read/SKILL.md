---
name: designcenter-open-model-data-read
description: "Read CAD features, parts, expressions, attributes, or relationships from the live model."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Live CAD model data

Use Designcenter Open `explore-model-structure` for the relevant application domain, then `read-model-data` with the minimum extraction schema. Use only returned entity, property, relation and comparator names. Add an entity filter for a narrowed request. Reuse the observed schema while its context matches.

Use PAGE or CURSOR only when the tool advertises the relevant parameter. Preserve the same filters and request scope across continuation calls. Missing continuation leaves a partial result. Inspect the native status and bind the result to the expected work or display part. [Capture verification](scripts/verify_read.py) checks raw ordered replies and part identity.

Use [CAE readback](../designcenter-open-journal-authoring/references/cae-2612.md) for SIM solutions, AFM linkage and subcases.
