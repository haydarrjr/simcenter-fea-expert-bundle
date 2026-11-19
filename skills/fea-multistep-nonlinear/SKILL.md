---
name: fea-multistep-nonlinear
description: "Investigate Simcenter Nastran multistep nonlinear histories. Use for SOL 106/401/402, preload locking, contact, friction, plasticity, thermal transfer and false convergence."
metadata:
  copyright: "Unpublished work. Copyright 2026 Siemens"
---

# Multistep Nonlinear

Bind the effective SOL 106, 401 or 402 deck, solution/subcase and original solver log. Inspect step ordering, solver control, nonlinear material, contact and preload history. Use [Solver investigation](../fea-solver-investigation/SKILL.md) for custody and solver messages and [BatchPost](../batchpost-actions/SKILL.md) for the actual converged states.

Read [diagnostics and checks](references/engineering-method.md) and [multistep load-path verification](references/open-solver-workflows.md). Check the lock-up or transfer of preload, separation, pressure/contact area, stick/slip, incremental plastic strain and absolute temperature as applicable. Compare local and global balances with independent evidence. A converged flag alone cannot validate load transfer. Keep unexecuted sequences or missing fields NOT_RUN. Use exact-release Siemens Help for solution-specific cards and continuation rules.
