# Simcenter 3D FEA Expert Bundle

**Source of truth:** <https://github.com/haydarrjr/simcenter-fea-expert-bundle>

Version **0.1.2** packages a Simcenter Agent Workspace FEA coordinator, six specialist subagents, 38 skills, and the existing Siemens integrations. It does **not** implement a new MCP server, solver, or resident bridge.

## Integrated local bundle

| Contribution | Contents |
|---|---|
| Referenced MCP servers (`type: ref`) | Simcenter 3D, Batch Post, Designcenter Open, Product Support, Simcenter Nastran MCP (provided by official/host bundles; no duplicate `[[mcps]]` launchers shipped) |
| Top-level agents | Simcenter 3D FEA Expert; BatchPost Agent; Designcenter Open Journal Agent; Simcenter 3D Documentation Agent; Simcenter 3D Assistant |
| Six specialist subagents | Model inspection; journal authoring; solver diagnostics; results/post; independent verification; product support |
| 38 skills | 20 canonical FEA + adapted parametric SOL101 + 3 Airframe/Aerostructures overlays + SC3D routing + 13 official integration skills |

All MCP servers (`Simcenter 3D`, `Batch Post`, `Designcenter Open`, `Product Support`, and optional `Simcenter Nastran MCP`) are referenced by name via `type: ref` in the agent recipes and supplied by the official installed bundles or host configuration; no duplicate `[[mcps]]` launcher scripts, product executables, or DLLs are shipped in this bundle. This is a **local custom bundle**, not an officially cleared public Siemens distribution.

## Public source versus authorized local inputs

The two canonical skill repositories are private. Git records only their pinned submodule commits in `source.lock.json` and `.gitmodules`; public CI does not fetch them. Siemens recipes, skills, BatchPost assets and launchers are proprietary. Only their paths and hashes in `integration/simcenter-3d/source.json` are published. The public repository's LICENSE does not relicense those external inputs.

An authorized maintainer initializes the private submodules with their own access, then hydrates the integration directory from their own installed, receipt-matching official archive:

```sh
git submodule update --init --recursive
python scripts/hydrate_integrated_sc3d.py <authorized-official.bundle>
```

Hydration verifies the complete archive hash and every selected file before writing, preserves the receipt, and refuses differing existing data. Missing/private inputs block a full build; they are never replaced by fixtures. Do not add tokens, product files or captured source to Git. `scripts/check_publication.py` rejects tracked payload in the excluded trees. `prepare_integrated_sc3d.py` is for a new reviewed capture into a separate directory, not for silently changing the approved receipt.

## Hardening in 0.1.2

`harden_integration.py` adds a deterministic precedence contract to all 13 official skill entry points and all four integrated agent instructions, without editing captured source bytes. The journal skill's contradictory `import sys` is removed from the packaged example. Original notices and frontmatter remain intact. Build reports contain the policy version, source SHA256 and packaged SHA256 for each integration input.

- Documentation tools are selected from the current catalog; Product Support is an explicit reachable fallback on the documentation/journal agents.
- PAGE/CURSOR are sent only if the actual input schema supports them. Incomplete continuation is PARTIAL, not an invented complete inventory.
- Sandbox SUCCESS/no stdout is transport status, not proof of statements, assertions, error paths or model effects.
- Live edits need an explicit target and authorization, an owned copy, and independent native readback. Timeout effects are reconciled before any retry.
- Zero, null and uncomputed quality metrics remain UNVERIFIED without their definition/computation evidence. Thresholds are problem-, solver- and element-specific; shape quality does not prove mesh convergence.

## Verification lanes

**Public GitHub Actions:** Python 3.11/3.14 on Linux/Windows, stdlib tests, synthetic Git/archive fixtures, manifest/recipe source checks and publication-boundary checks. No secrets, private submodule checkout, product binaries, proprietary uploads or release artifact publication. Capture-dependent tests explicitly skip with reasons. Green CI means **SOURCE_TESTED**, not a complete bundle build or native qualification.

**Authorized local release:** Python 3.11+, Git, authorized inputs and the documented installed `sc-agents` CLI are required. After staging reviewed overlay files (release collection reads the Git index), run:

```sh
python -m unittest discover -s tests -v
python scripts/bundle.py precheck --cli <sc-agents.exe>
python scripts/bundle.py build
python scripts/bundle.py postcheck --cli <sc-agents.exe>
python scripts/bundle.py local-test --cli <sc-agents.exe>
```

Build output is `dist/simcenter-fea-expert/0.1.2/agents-artefact-windows.zip` with its `.sim-ai-agents.toml` sidecar. Archives use sorted entries/fixed timestamps and audits bind every staged skill digest and non-skill payload. `local-test` materializes the bundle in isolated productdata, not the active installation. It does not start a licensed native session or establish MCP handshake/engineering acceptance.

## Installation and coexistence safety

The optional local release installer backs up enabled state, uses the supported bundle CLI, and verifies every unrelated enabled ID/version is preserved. It never restores an old `enabled-bundles.json` wholesale after an app update. Existing same-version differing archives are refused. This release does not silently change the user's installed bundles, including NX Expert 0.1.2.

Because MCP servers are referenced via `type: ref` rather than re-declared in `.sim-ai-agents.toml`, enabling this bundle alongside the official Simcenter 3D bundle creates no duplicate MCP server configurations or custom `productdata/mcps/fea-*` folders. Resolve duplicate agent/skill names explicitly in a new session; never silently disable another bundle.

## Engineering evidence boundary

Use SOURCE_TESTED, DOCUMENTED_2606_CANDIDATE, MCP_2612_DISCOVERED, HOST_QUALIFIED, NATIVE_EXECUTED, SOLVER_VERIFIED and ENGINEERING_ACCEPTED separately. Stage status is PASS / FAIL / PARTIAL / NOT_RUN / UNVERIFIED. Packaging does not close upstream Issue #21 P01–P07, establish associative CAD–FEM–SIM updates, validate a licensed solve, or certify engineering correctness.

See [release notes](RELEASE_NOTES.md), [local qualification scope](docs/qualification/0.1.2.md), and [packaged user documentation](dist/docs/README.md).
