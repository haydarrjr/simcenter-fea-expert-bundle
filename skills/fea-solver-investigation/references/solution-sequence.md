# Solution Sequence

Use the global Siemens MCPs for live SIM/FEM setup, deck export and
post-processing. Submit the verified deck directly to Simcenter Nastran in
batch. Qualify solver submission and SIM/FEM persistence independently.

1. **Bind the live target.** Check release, exact SIM/FEM paths, work and display
   roles, and original solutions. Adopt an authorized working copy. For CAE
   journals use `Session.Parts.BaseWork`. Confirm both model identities before
   making changes. Keep existing solutions and their artifacts.
2. **Configure the requested solution.** Use the actual sequence family and
   effective subcase selections. For SOL 103, use the
   [free-free method](../../fea-dynamics/references/sol103-free-free.md). Bind a
   deliberate result output request and verify the new live solution.
3. **Export and qualify the exact deck.** For the qualified Siemens NXOpen
   route, `SolveOption.WriteSolverInputFile` exports the solver deck. Check the
   exporter diagnostics, [effective Case Control](../../simcenter-nastran/SKILL.md), selected loads/constraints,
   units, referenced dependencies and output requests. Copy the verified deck
   to a new task-owned batch directory and verify its hash. If it references
   INCLUDEs or other files, preserve the authorized dependency paths and
   verify the entire closure before running. Keep raw and verified files.
4. **Run the installed Siemens batch solver.** On the observed Windows 2612
   Desktop Bundle installation the executable is
   `NXNASTRAN\bin\nastranw.exe` under the product root. Launch with the
   isolated job directory as the working directory. For the verified
   standalone SOL 103 desktop bundle deck the observed invocation is:

   ```powershell
   & (Join-Path $productRoot 'NXNASTRAN\bin\nastranw.exe') 'solution.dat' 'prog=bundle' 'old=no' 'scratch=yes' 'sys442=2'
   ```

   Confirm applicable runtime and license options for other installations.
   Resolve the authorized product root first, then test only the known
   `NXNASTRAN\bin\nastranw.exe` and `NXBIN\scd5_convert.exe` paths. If absent,
   request that installation's exact path; do not search vendor trees.
   The Windows launcher can return before Nastran finishes. Use new job files
   and the solver's log, exit status and F06 completion to qualify the result.
   Reconcile a pending launch before retry. Preserve the input, invocation and
   output hashes in the evidence record.
5. **Prefer SCD5 for compatible results.** Use documented solver-native SCD5
   output where supported by the release and solution. For SOL 101 and SOL 103,
   the Siemens `NXBIN\scd5_convert.exe` officially converts the completed OP2.
   Supply explicit input and output paths, disable SOL 101-only performance
   mode for SOL 103 and validate the conversion log. The observed command uses
   `scd5_convert.exe -c=2 input.op2 output.scd5`. Keep the original OP2 and
   verify SCD5's state inventory and field coverage with BatchPost. When a
   required quantity is absent from SCD5, use the genuine OP2 via BatchPost for
   that quantity and record the format coverage. [SCD5 conversion guide](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1968781?audience=external)
6. **Post-process using BatchPost.** Open the exact job's preferred result
   first. Use `list`, `contour` CSV/PNG or `graphi` only with the current
   schema and actual states. Use BatchPost for available numerical result
   data and figures. For F06 diagnostics, completion, or any information
   outside its catalog, use the official Nastran diagnostic MCP when available
   or scoped original F06/log text. Preserve F06 and OP2 custody. Do not
   install alternate solvers or binary readers.
7. **Close out.** Verify the solution and affected engineering quantities. Record the native model state, solver and post results, and report artifact. If the workflow requires persistence, confirm an admitted save and independent reopen or obtain operator save evidence. A dirty model may still have a completed solver run with qualified deck lineage.
