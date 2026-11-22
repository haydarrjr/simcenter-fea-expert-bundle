# 0.1.12 candidate

- Route repeatable physical selection, local mesh control, scoped Element Quality and response convergence through the common skill tree.
- Document the observed Designcenter 2612 face-recipe binding and independent FEM readback. Add contact setup, diagnosis and recovery guidance for SOL 401 and 402.
- Add independently specified elastic contact cycles and report the measured [qualification of mesh and contact](docs/qualification/0.1.12.md).

# 0.1.11 candidate

- Verify an associative SOL 101 geometry change and check remesh, boundary transfer, equilibrium and response sensitivity.
- Qualify SOL 401 contact and bolt preload on a reference joint. Verify SOL 402 internal state restoration and large-rotation objectivity with independent comparisons.
- Extend the reusable methods for associative studies, joint history and finite kinematics. See [0.1.11 qualification](docs/qualification/0.1.11.md).

# 0.1.10 candidate

- Route elastic statics, associative updates, thermally driven response, joint behavior, staged nonlinear analysis and stability by engineering outcome. Add independent verification methods for load transfer, material history and equilibrium paths.
- Document verified 2612 solver-deck import, independent native save/reopen and solver/result checks for synthetic SOL 101, 106, 401 and 402. Confirm live reopening and attached OP2 results for the final SOL 402 POST −2 files.
- Document the standalone SOL 401 monitor and small-displacement controls and the SOL 402 OP2 output setting. See [qualification](docs/qualification/0.1.10.md) and the [linear and nonlinear implementation plan](docs/linear-nonlinear-implementation-plan.md).

# 0.1.9 candidate

- Qualify synthetic Hermes 2612 PCA, inverse Load Identification and complex TPA with separate source and result identities. Record the Testlab project workflow as `TBD`.
- Add independent checks for recovered load, held-out receiver closure, principal powers and reconstructed receiver power. See [0.1.9 qualification](docs/qualification/0.1.9.md).

# 0.1.8 candidate

- Export verified nodal displacement RMS and frequency-resolved PSD through the official BatchPost XML path, with explicit units and CSV state checks.
- Record native NXOpen Save As and Designcenter 2612 qualification for synthetic SRS generation and structural peak recovery, modal damping transfer, external superelement assembly results and NVH methods.
- Add independent solver fixtures and preserve one portable skill tree and three verified client archives. See [0.1.8 qualification](docs/qualification/0.1.8.md).

# 0.1.7 candidate

- Route dynamics by requested output across SRS, deterministic FRFs, time histories, stationary PSD/CSD, damping and NVH. Add component representations and external superelement guidance within the existing 39 skills.
- Add read-only advanced deck observation with hashed INCLUDE provenance and explicit unresolved effective sets. Keep the SOL 101/103 checker and solver admission rules.
- Document the validated Designcenter 2612 PRT/FEM/SIM save and reopen boundary. Add synthetic SOL 108 and SOL 111 harmonic and random jobs with independent numerical checks.
- Build AgentsAI, Codex and VS Code packages from the same source. See [0.1.7 qualification](docs/qualification/0.1.7.md) for observed capabilities and open checks.

# 0.1.6 candidate

- Refine triggers for all 39 skills. Replace model-specific Airframe, load-filter, margin and SOL 101 workflows with task-scoped methods. Consolidate Siemens operation guidance and shorten the seven agent recipes.
- Read SIM, FEM and AFM through the 2612 NXOpen journal. Capture AFM occurrence IDs, root collectors, active solution and per-field errors. Distinguish missing or uncomputed mesh-quality evidence from a measured result.
- Produce Agent Workspace and project archives alongside the Agent Plugins 1.0 archive and local marketplace catalogs. Validate shared skill bytes, installed resource identity and packaged links.
- Add independent SOL 101 and SOL 103 input fixtures and CAE journal regression coverage.
- Qualify creation and persistence of a synthetic tetrahedral FEM and SOL 103 SIM on Designcenter 2612.1700. Verify reopen in a fresh native process and through the two live Siemens MCP profiles.

# 0.1.5 candidate

- Add the 2612 Python CAE operation catalog and live SIM/subcase readback journal. Reuse known APIs and profile bindings; stop after a connected read times out instead of repeating status and the same query.
- Add the `simcenter-nastran` SOL 101/103 skill, text-deck coverage limits, and guarded 2612 `WriteSolverInputFile` admission. Export, solver completion and engineering acceptance remain separate.
- Tighten BatchPost state acceptance, requested-format PDF checks, and VS Code/Codex/Agent Workspace skill routing. Remove mandatory references to unbundled host skills.

# 0.1.4 candidate

- Route FEA skills through globally configured Siemens MCPs. Use scoped original Nastran text and official BatchPost exports when no live Nastran diagnostic tool is available.
- Add the free-free SOL 103 setup, native admission, eigenspace and reporting methods.
- Remove instructions to provision external FEA solvers or Python result readers during a Siemens study.
- Define offline engineering report figures and quantity-level provenance.
- Pass the existing Siemens license environment to the Codex BatchPost worker by name.

# 0.1.3 candidate

- Build Agent Workspace, Codex and VS Code Copilot packages with one source digest.
- Install or roll back project resources with package verification and ownership checks.
- Render local MCP config for Designcenter Open, Model Inspection and optional BatchPost. The launcher refreshes the initial catalog and marks sandbox execution failures or unobserved output.
- Qualify the two read profiles through a fresh Codex app-server thread and capture independent model and backend identity evidence.
- Use the packaged FEA controller for prepared execution, raw response capture and native readback.

# 0.1.2 — Integration skill hardening and canonical public repository

- Make https://github.com/haydarrjr/simcenter-fea-expert-bundle the source of truth, preserving its initial main history.
- Reference official host MCP servers (`Simcenter 3D`, `Batch Post`, `Designcenter Open`, `Product Support`, `Simcenter Nastran MCP`) via `type: ref` in agent recipes without packaging duplicate `[[mcps]]` declarations or `mcps/fea-*` launcher scripts; expose a single top-level orchestrator (`Simcenter 3D FEA Expert`) that coordinates six unified specialist subagents (`fea-model-inspector` / Simcenter 3D Assistant, `fea-journal-author` / Designcenter Open Journal, `fea-solver-diagnostics`, `fea-results-post` / BatchPost, `fea-verifier`, and `product-support-agent` / Simcenter 3D Documentation) and 38 skills (including 3 Airframe Structural Verification & Aerostructures overlay skills: `simcenter-airframe-structural-verification`, `simcenter-aerostructures-load-filtering`, and `simcenter-aerostructures-margin-of-safety`). No new MCP implementation.
- Preserve proprietary source hashes and apply deterministic safety policy to packaged skills and agent instructions; expose source/packaged digests in build evidence.
- Gate documentation by the current catalog and pagination by exact input schemas; make Product Support fallback reachable.
- Remove contradictory standard-library import from the packaged journal example; distinguish transport SUCCESS from observable test results.
- Require explicit live target authorization, owned copies and independent readback. Reconcile uncertain mutations before retries.
- Keep missing/uncomputed mesh metrics UNVERIFIED and thresholds problem-specific.
- Add pinned, read-only GitHub Actions source checks on Linux/Windows and Python 3.11/3.14. Private source and proprietary integrations remain local; no public bundle artifacts uploaded.
- Add hash-pinned local hydration and publication-boundary checks; preserve unrelated installed bundle state.

## Evidence scope

Public CI establishes SOURCE_TESTED only. Authorized local build/audit and isolated installation are separately reported in `docs/qualification/0.1.2.md`. Packaged-agent MCP handshake, live execution, licensed solve, GUI acceptance and Issue #21 P01–P07 qualification are not implied.

# Earlier local iterations

0.1.0 was a references-only local prototype. 0.1.1 added actual official MCP launchers, four official agents and all 13 official integration skills. Their earlier test/build receipts are historical and are not evidence for this PR's new policy. Existing installed 0.1.1 is not automatically replaced by publishing this repository.
