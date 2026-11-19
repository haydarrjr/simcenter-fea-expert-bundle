# Simcenter 3D FEA Expert

Canonical top-level orchestrator, six specialist roles and **38 FEA and Simcenter 3D skills**. One source candidate produces Simcenter Agent Workspace, Codex and VS Code GitHub Copilot distributions.

Repository: <https://github.com/haydarrjr/simcenter-fea-expert-bundle>

## Repository Layout (Unified Single-Source Architecture)

Matching the clean, self-contained layout of `simcenter_nx_expert`, all recipes and skills live in a single canonical top-level hierarchy with zero split `overlay/`, `.agents/`, or external submodule dependencies:

```text
simcenter-fea-expert-bundle/
├── .sim-ai-agents.toml                  # Bundle sidecar manifest (id = "simcenter-fea-expert", version = "0.1.2")
├── recipes/
│   ├── fea-expert-agent.yaml            # Single top-level orchestrator agent
│   └── subrecipes/                      # 6 specialist subagents
│       ├── fea-model-inspector.yaml     # Simcenter 3D Assistant (read-only FE/CAD inventory)
│       ├── fea-journal-author.yaml      # Designcenter Open Journal Author (8-step API discovery & sandbox)
│       ├── fea-solver-diagnostics.yaml  # Simcenter Nastran deck/F06/contact/trim diagnostics
│       ├── fea-results-post.yaml        # BatchPost result post-processing (.op2, contours, XY graphs)
│       ├── fea-verifier.yaml            # Independent analytical falsification & VVUQ verifier
│       └── product-support-agent.yaml   # Cited Siemens documentation retrieval
├── skills/                              # All 38 canonical skills in one place (skills/<name>/SKILL.md)
├── docs/
│   ├── skill-catalog.md                 # Complete catalog of all 38 skills
│   └── qualification/0.1.2.md           # Qualification scope and evidence classes
├── scripts/
│   ├── package_bundle.py                # Builds dist/simcenter-fea-expert/0.1.2/agents-artefact-windows.zip
│   ├── validate_distribution.py         # Validates all 38 skills, 7 recipes, ADR-086 metadata, and links
│   ├── build_distribution.py            # Builds portable source archive
│   └── install_release_local.py         # Packages, installs, enables, and hydrates the bundle in Agent Workspace
└── tests/
    ├── test_bundle_layout.py            # Verifies unified recipes/ and skills/ layout and archive determinism
    └── test_distribution.py             # Verifies offline source contract
```

See the complete [Skill Catalog (38 skills)](docs/skill-catalog.md) and [Release Notes](RELEASE_NOTES.md).

## Referenced MCP Servers (`type: ref`)

`simcenter-fea-expert` does **not** ship duplicate MCP binaries or launchers. It binds by name (`type: ref`) to the host-managed MCP servers already provided by Simcenter Agent Workspace:
- `Simcenter 3D` (Model Inspection)
- `Designcenter Open` (NXOpen API Discovery, Sandbox & Live Execution)
- `Product Support` (Siemens Technical Documentation)
- `Simcenter Nastran MCP` (Deck, `.f06`, and `_contact.log` Forensics)
- `Batch Post` (`sc3d_batchpost_mcpconnector.exe` and separate `sc3d_batchpost.exe --mcp` worker)

## Build and install the project channels

Run the tests, then build a versioned candidate. The build prints its output directory and creates a distribution manifest and SHA-256 list.

```powershell
python -B -m unittest discover -s tests -v
python -B scripts/package_release.py
```

Set `$candidate` to the printed output directory. Each target must already exist. Use new backup directories outside the project being installed.

```powershell
python -B scripts/sync_project_runtime.py --project $codexProject --archive "$candidate/codex-project-windows.zip" --backup $codexBackup
python -B scripts/install_copilot.py --project $copilotProject --archive "$candidate/vscode-copilot-windows.zip" --backup $copilotBackup
```

Use `--verify` in place of `--archive` to verify installed files. Use `--rollback --backup <backup>` to restore the backed-up version when current bytes still match the installation. Codex uses a marked section of `AGENTS.md` and an installed `.agents/skills` tree. VS Code discovers `simcenter-fea-expert` in `.github/agents` and its skills in `.github/skills`. Open a fresh chat after installation.

Project installation preserves existing MCP settings and task files. Use global, official MCP definitions by default in Codex and VS Code. Keep one active definition of each Siemens profile in the selected client. Preserve host settings for unrelated tools. If a profile needs configuration, render a fragment for the selected local Siemens installation and review it against the host's existing settings. The default fragment allows read-only tools. `--engineering` adds sandbox and action candidates, and `--batchpost` adds the connector for the separate Siemens worker. The packaged launcher starts the worker and hands its private pipe to the official connector.

```powershell
python -B scripts/render_mcp_config.py --project $codexProject --product $productRoot
python -B scripts/render_mcp_config.py --host copilot --project $copilotProject --product $productRoot
```

Place reviewed Codex fragments in the user's `~/.codex/config.toml`. Install shared connector scripts to a stable integration directory if the global definition uses them. For Copilot native configuration, use the Copilot user `~/.copilot/mcp-config.json` or the VS Code user MCP configuration, according to which client loads the tools. Existing editor-managed definitions can be forwarded when eligible. Select the FEA custom agent in a new chat and verify the current tool namespaces. [VS Code MCP configuration reference](https://code.visualstudio.com/docs/agents/reference/mcp-configuration)

The Siemens 2612 Copilot launcher uses `--legacy-discovery` for Designcenter Open and Model Inspection. A controlled probe reproduced a status-only catalog and `DCMCP-E002` after the VS Code Copilot host's `server/discover` negotiation. Standard MCP `initialize` on a fresh child connected to the same open Model Inspection session. The launcher returns the standard method-not-found response for `server/discover` so the host can negotiate `initialize`. All tool catalogs and results continue to come from Siemens.

On installations with global Copilot MCP definitions, configure each profile once in the native harness. The optional Copilot BatchPost launcher starts `sc3d_batchpost.exe --mcp` on a private pipe. It attaches `sc3d_batchpost_mcpconnector.exe` after the worker announces readiness and reports this interval on stderr. A fresh session can incur worker initialization time. List the available tools for a startup check. Use `open` with the intended absolute results path before requesting result inventory via `list`.

Use `python -B scripts/render_mcp_config.py --audit <config> [<config> ...]` to inventory selected config scopes and detect repeated Siemens profiles. This audit does not start a server.

With Designcenter and Model Inspection enabled in the same open Simcenter 3D Pre/Post session, qualify the installed Codex channel through a fresh Codex app-server thread. The command records skill discovery, the two tool catalogs, part and mesh reads, and the trusted backend PID from each official connector log. It opens only read-only tools. Use a new output directory outside the project and keep raw evidence local.

```powershell
python -B scripts/qualify_codex_readonly.py --project $codexProject --product $productRoot --out $evidenceDir
```

## Validate, Package, and Install into Simcenter Agent Workspace

### 1. Validate & Build Bundle Archive
```powershell
python -m unittest discover -s tests -v
python scripts/validate_distribution.py
python scripts/package_bundle.py
```
This produces the Agent Workspace archive and sidecar under `dist/simcenter-fea-expert/<version>/`. Use the unified candidate command above to build all channels together.

### 2. One-Command Local Install into Simcenter Agent Workspace
```powershell
python scripts/install_release_local.py `
  --productdata $productData `
  --cli $agentWorkspaceCli `
  --candidate $candidate `
  --receipt-directory $agentsAiReceipt
```

Use isolated productdata for qualification. Installation receipts describe bytes and activation. A fresh Agent Workspace chat and its available MCP tools must be checked separately.
