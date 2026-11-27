# Issue 22 candidate qualification

The starting source was Bundle 0.1.12 at `49a537daaabab616d04537b4f2b2516baa39d3c1`. The Windows baseline ran 55 unit tests with one Windows symlink-privilege skip. Distribution validation checked 1,159 criteria and the baseline packaged all five channels with source digest `afdc1855da8489e435e2291122f0c36a319f56f5faa1e792c80c3c2245fcb46e`. The first runtime slice reused the controller and the existing text-deck and native read methods.

## Observed Windows scope

| Gate | Status and scope |
|---|---|
| SC3D file-based model | PASS for the isolated 2612.1700 solver-backed SOL101 FEM/SIM import, exact solution and step rename, save, independent reopen, inventory and export. A separately imported SOL103 tetrahedral topology exercised the same file-based route. Native live model data and regional remesh qualification are separate. |
| Live Codex SC3D | PARTIAL. The configured profiles advertised and connected. The Simcenter Model Inspection part-info call returned successfully with an owned SIM open. The Designcenter Open role journal timed out, so paired role, process and live effect acceptance remain incomplete. |
| Nastran launch and output | PASS for scoped 2612.0000 SOL101, SOL103, SOL401 contact, SOL108 and SOL111 random-field submissions with declared evidence. Earlier long-path launches remained UNKNOWN. A relative entry path in the isolated job directory produced native outputs. Multi-step contact state history was checked in original F06. |
| BatchPost | PASS for the exact structured SOL101 nodal CSV with one accepted solver-artifact parent and real vendor catalog. The same result also recovered reaction and stress via the existing direct route. Native modal mode 7, a deterministic 5 Hz phase-zero value and 81 random PSD states plus RMS were recovered. These measurements retain distinct selection and unit evidence. |
| Engineering | PASS for the scoped static displacement and proved native lineage, modal shape/frequency and TET4 volume comparisons, four SOL401 contact states, and SISO 5–25 Hz FRF/PSD/RMS agreement. The modal metric was diagonal. The SOL401 contact history came from F06. |
| Generality and recovery | PARTIAL. The ledger supports separate scopes and checks stale identity, missing dependencies, nested schema, incorrect units and UNKNOWN after restart. Full held-out qualification, all SC3D edit families and all failure/custody tests remain open. |
| Package and clients | Local archive and source results are separate from client-native qualification. A fresh Codex client discovered all 40 skills from an attested disposable candidate project. Candidate native effect and Agent Workspace/Copilot live qualification remain open. |
| Performance | PARTIAL. Three warm exact-baseline deck-inspection pairs measured 151.2 ms versus 239.9 ms median, and 1,667 versus 788 stdout bytes. This local CLI comparison exceeded the focused overhead target. Full multi-family native comparisons and model-visible token measurements remain open. |

The structured static chain is recorded in one controller ledger with explicit parent references through owned SC3D FEM/SIM, the exported deck, the original licensed Nastran OP2 and the native BatchPost CSV. The independently prescribed static displacement was `7.375e-5 m`. BatchPost measured `7.37500086e-5 m`. Modal mode 7 compared `10881.31 Hz` in F06 to `10881.314453125 Hz` in the native catalog with 12 matching translational DOFs and MAC 1.0 in the declared metric. The independent one-sided RMS calculation gave `0.0035124204327 m` and BatchPost measured `0.00351242042 m`.

Original receipts and artifacts are under the task-local `.work/issue-22` directory. Use the source checkout’s BatchPost qualification harness, `tests/verify_shared_batchpost.py` with the approved workspace, native product, an accepted job artifact and a new evidence directory. For the read-only live check use the source checkout’s Codex qualifier, `scripts/qualify_codex_readonly.py`, with an attested project and the exact owned active SIM. Use the [runtime contract](runtime-cli.md) to submit future isolated test models and retain their scoped receipts.

## Instruction and distribution review

Keep the 40 skills and the six specialist recipes at their existing owners. Keep the engineering and API discovery routes and portable/client manifests. Narrow dispatch instructions at the runtime gate and workflow entry, and place command, provenance and qualification detail in conditional references. Generated client surfaces continue through the same release scripts. Run the source test and distribution gates before packaging. Client installs and publication are separate authorized operations.
