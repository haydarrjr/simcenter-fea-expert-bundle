# Simcenter 3D FEA Expert

An agent plugin for preparing, running and reviewing finite element studies in Simcenter 3D and Simcenter Nastran. Simcenter Agent Workspace (AgentsAI), Codex and VS Code GitHub Copilot share the same engineering skills and [workflow router](fea-workflow.md).

## Engineering workflows

- Prepare CAD, FEM and SIM models. Resolve selections, configure mesh controls and evaluate mesh quality against the quantity of interest.
- Set up and diagnose linear static, nonlinear contact, modal, frequency response, transient, random vibration and NVH studies.
- Trace solver input and result files, recover quantities with the correct case and units, and check results against independent mechanics.

Start a complete study with the [FEA Chief Engineer](skills/fea-chief-engineer/SKILL.md). For a focused task, choose the entry point in the [workflow router](fea-workflow.md).

## Build the packages

Use Python 3.12. Source validation and packaging run on Windows and Linux. Native engineering operations require a compatible Siemens installation and licenses. The Agent Workspace manifest targets Simcenter 3D 2612 on Windows.

```powershell
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python scripts/validate_distribution.py
$candidate = (python scripts/package_release.py | ConvertFrom-Json).output_directory
```

The build writes a content-addressed candidate under `dist/simcenter-fea-expert/` with a distribution manifest and SHA-256 checksums. [GitHub Actions](https://github.com/haydarrjr/simcenter-fea-expert-bundle/actions/workflows/validate.yml) builds the same channels on Windows and Linux. CI verifies the source and archive contracts. Live verification runs against the installed Siemens host with the intended model and tool profiles.

## Install a client

Set the PowerShell variables below to your local paths. Use existing target project directories and new backup directories outside those projects.

| Client | Package | Discovery |
| --- | --- | --- |
| Simcenter Agent Workspace | `agents-artefact-windows.zip` and `.sim-ai-agents.toml` | Agent Workspace bundle catalog |
| Codex | `codex-project-windows.zip` | Project `AGENTS.md` and `.agents/skills/` |
| VS Code GitHub Copilot | `vscode-copilot-windows.zip` | Project `.github/agents/` and `.github/skills/` |

```powershell
python scripts/install_release_local.py --productdata $productData --cli $agentWorkspaceCli --candidate $candidate
python scripts/sync_project_runtime.py --project $codexProject --archive "$candidate/codex-project-windows.zip" --backup $codexBackup
python scripts/install_copilot.py --project $copilotProject --archive "$candidate/vscode-copilot-windows.zip" --backup $copilotBackup
```

The project installers support `--verify` and `--rollback`. On hosts that support native plugin discovery, the build also provides `simcenter-fea-expert-plugin.zip`. Extract it and register the directory through the client’s plugin settings. Use one discovery method per workspace and open a fresh chat after installation. [Codex plugin guide](https://developers.openai.com/plugins/build/plugins) · [VS Code plugin reference](https://code.visualstudio.com/docs/agents/reference/agent-plugin-reference)

## Connect Siemens tools

Agent Workspace binds to host-managed Siemens MCP profiles by reference. In Codex and VS Code, configure the official profiles through the client. The workflow uses Model Inspection for CAE reads, Designcenter Open for CAD reads and journals, Product Support for Siemens documentation, Simcenter Nastran for job diagnostics, and BatchPost for result recovery. The [tool matrix](skills/fea-sc3d-tool-routing/references/tool-matrix.md) identifies the profile for each operation.

The verified Designcenter Open 2612.1700 catalog has 12 application tools. The local VS Code profile exposes `dc_connection_status` separately at `designcenter://connection-status`.

Use `python scripts/render_mcp_config.py --help` to render or audit a configuration for an installed Siemens product. Define each profile once in the client and verify the tool catalog in a fresh chat. For a Codex read-only smoke check against a connected session, see `python scripts/qualify_codex_readonly.py --help`.

## Repository layout

| Path | Purpose |
| --- | --- |
| [`skills/`](skills/) | Canonical engineering and Siemens operation skills |
| [`fea-workflow.md`](fea-workflow.md) | Shared routing by requested outcome |
| [`recipes/`](recipes/) | Agent Workspace orchestrator and specialist recipes |
| [`com.github.copilot/`](com.github.copilot/) and [`integrations/`](integrations/) | Client adapters and project instructions |
| [`scripts/`](scripts/) and [`tests/`](tests/) | Packaging, installation and offline regression checks |

Licensed under the [MIT License](LICENSE).
