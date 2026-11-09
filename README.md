# Simcenter 3D FEA Expert

Canonical top-level orchestrator agent, 6 specialist subagents, and **38 self-contained FEA & Simcenter 3D skills** packaged for direct installation into **Simcenter Agent Workspace**.

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
- `Batch Post` (`sc3d_batchpost.exe --mcp` Result Post-Processing)

## Validate, Package, and Install into Simcenter Agent Workspace

### 1. Validate & Build Bundle Archive
```powershell
python -m unittest discover -s tests -v
python scripts/validate_distribution.py
python scripts/package_bundle.py
```
This produces the ready-to-install bundle archive and sidecar:
- `dist/simcenter-fea-expert/0.1.2/agents-artefact-windows.zip`
- `dist/simcenter-fea-expert/0.1.2/.sim-ai-agents.toml`

### 2. One-Command Local Install into Simcenter Agent Workspace
```powershell
python scripts/install_release_local.py `
  --productdata "D:\_DATA\Software\SC3D\simcenter-ai-agents-windows-x86_64\productdata" `
  --cli "D:\_DATA\Software\SC3D\simcenter-ai-agents-windows-x86_64\app\resources\bin\sc-agents.exe"
```
