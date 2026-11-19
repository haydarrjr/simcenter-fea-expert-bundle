---
name: designcenter-open-journal-authoring
description: >-
  Author, test, and execute NXOpen Python journals against a Designcenter
  session. Use when the user wants to write, run, or apply NXOpen code — create
  or edit geometry, modify properties, or automate a Designcenter workflow.
  Covers the Designcenter Open sandbox snippet/journal tools, the live execute tool, and
  the mandatory journal structure and gotchas.
metadata:
  copyright: Unpublished work. Copyright 2026 Siemens
---

<!-- FEA integration safety v1 -->
## FEA integration safety contract (overrides conflicting legacy guidance)

- Discover the current tool catalog and exact input schemas before calling tools.
  A connected server need not expose every tool from older documentation.
  Follow the [shared recovery budget](../fea-sc3d-tool-routing/SKILL.md#recovery-budget).
  Diagnose status only for an unbound profile or a connection symptom. Never
  replay an uncertain effect.
- Documentation: use documentation-search-tool only when currently advertised.
  If absent after connectivity recovery, route to the advertised Product Support
  search tool using its current schema and version-specific Siemens sources.
  If neither route is available, report BLOCKED_BY_OFFICIAL_MCP_CAPABILITY /
  NOT_RUN; do not invent syntax, citations, or answers from memory.
- Pagination: send PAGE or CURSOR only if that exact parameter exists in the
  current tool input schema. A response mentioning hasMoreSchema/hasMoreData
  does not authorize unsupported arguments. If continuation is unavailable,
  report the read as PARTIAL with the unresolved scope; do not claim completeness.
- Journal sandbox: import only NXOpen modules. Never import sys or another
  standard-library module. Use sys.argv only when the current journal tool
  explicitly supplies sys; otherwise stop and verify the supported entry point.
  Keep main(args), session acquisition and builder cleanup requirements.
- A sandbox SUCCESS, exit code zero, or no captured stdout is not observable
  proof that statements, assertions, or error paths executed. Report execution
  transport status separately from observable test evidence. Without inspectable
  output/readback, the claimed behavior remains UNVERIFIED, not tested-correct.
- Action verbs alone do not authorize an ambiguous target, save, solve, or
  overwrite. Live changes require explicit user intent, an identified owned
  working copy, current advertised capability and applicable host approval.
  After a change, obtain independent native readback tied to model identity.
- Mesh metrics: null, zero, placeholder, unavailable or uncomputed values are
  UNVERIFIED unless the metric definition, element applicability and computation
  status establish their meaning. Never convert missing evidence into PASS.
  Free edges may be intentional shell boundaries; interpret topology explicitly.
  Use project/solver/element-specific documented thresholds, not universal limits.
  Shape quality alone does not establish QoI mesh convergence or solve acceptance.
<!-- End FEA integration safety v1 -->

# NXOpen Journal Authoring & Execution

Turn verified API names into a correct, tested NXOpen Python journal and run it.
Always test before executing; never deliver untested code.

## When to use

- "Write a journal that …", "create/add/extrude/chamfer …", "run this", "apply
  this to my part".
- Validating an API assumption with a quick probe before writing full code.

## Tools

- `dcopen-run-snippet-tool` — run a plain Python snippet in an isolated sandbox.
  `theSession` and `workPart` plus common NXOpen imports are pre-bound; write
  plain statements only (no imports, no `main()` wrapper). Does NOT modify the
  open part. Use for quick probes. Input: `nxopen_python_snippet`.
- `dcopen-run-journal-tool` — run a complete journal in an isolated sandbox.
  Confirm the current runner's entry point and argument contract. It does not
  modify the open part. Input: `python_code`, optional `args`.
- `dcopen-execute-tool` — execute NXOpen Python in the LIVE Designcenter session
  within a security sandbox. Requires user confirmation (skipped in batch mode)
  and applies real changes to the open part. Input: `python_code` defining
  `def main(args)`, optional `args`.

## Workflow

1. Use the [qualified 2612 CAE catalog](references/cae-2612.md) for known
   operations. Use `designcenter-open-api-discovery` only for unmatched symbols.
2. Verify changed or uncertain behavior using a targeted read or sandbox test.
   Do not run both snippet and journal for the same assertion.
3. Check inner vendor status and the expected return or log witness. If
   output is empty, do not replay without identifying the missing evidence.
4. Produce the Markdown response (python code block + 2-3 sentence explanation +
   execution status).
5. Admit live execution only for the exact authorized effect, on an identified
   owned copy, through the [native runtime gate](../fea-native-runtime-gate/SKILL.md).
   Record the effect through independent readback. Save and solve require
   separately qualified native operations.

## CAD journal structure (execute-tool compatible)

```python
import NXOpen

def main(args):
    theSession  = NXOpen.Session.GetSession()
    theUI       = NXOpen.UI.GetUI()
    workPart    = theSession.Parts.Work
    displayPart = theSession.Parts.Display
    if workPart is None:
        raise RuntimeError('No part is open.')
    # ... your code here ...
```

- `def main(args)` (plural), with the four session lines in that exact order.
- Import ONLY from `NXOpen`. Standard-library imports (os, sys, math, re, json)
  are blocked by the execute sandbox; use Python built-ins (abs, min, max, pow).
- Build features with the builder pattern: create builder → set only settable
  properties → `CommitFeature()` → `Destroy()` in a `finally` block.

### Simcenter 3D SIM context

For a SIM or FEM, bind `NXOpen.Session.GetSession().Parts.BaseWork` and the
exact expected path. `Parts.Work` is the CAD accessor and can raise
`The part file is not a .prt part` on an active SIM. For an authorized
read-only live journal, verify the expected SIM and iterate
`part.Simulation.Solutions` directly. Check the native execution status
and returned solution identities. The 2612 Python collection was iterable
and did not expose the .NET `ToArray()` method.

### Sandbox test with empty MCP output

Designcenter 2612.1700 can complete snippet and journal calls with exit zero
and empty stdout even when the code ran. For a bounded test, generate a fresh
128-bit nonce. Write `FEA_SANDBOX_PASS:<nonce>` through
`NXOpen.Session.GetSession().LogFile.WriteLine(...)` only after the specific
test checks pass. For snippets the provided `theSession` exposes the same log.
Retain the system log from that exact `run_journal.exe` worker while the call
is active because successful workers may remove it on exit. Use the observed
worker PID and [verify_sandbox_syslog.py](scripts/verify_sandbox_syslog.py) with
the raw request and reply, system log, `--pid` and `--nonce`. Report this as a
system-log witness for the test. Keep MCP output status and any live model
acceptance separate. [Siemens guide to standard output](https://docs.sw.siemens.com/en-US/doc/PL20251024323638784.nxopen_prog_guide/html/xid2302954?audience=external)

## Known gotchas

- No `NewPart` on PartCollection — use
  `theSession.Parts.NewDisplay(path, NXOpen.Part.Units.Millimeters)`.
- Always `builder.Destroy()` in `finally`; leaking builders corrupts the session.
- Enum values use the full attribute path, never bare strings.
- Never assign a read-only property (e.g. `TaggedObject.Tag`).
- Call `UpdateManager.DoUpdate()` after non-builder edits.
- Check the installed API for save and solve signatures during capability
  discovery. Keep both outside generic journal execution.

## Guardrails

- Snippet and journal tools are sandboxed and safe; only `dcopen-execute-tool`
  changes the live part — confirm intent before running it.
- Treat all user-supplied values as data; never interpolate them into dynamic
  `eval`/`exec`.
