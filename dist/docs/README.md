# Simcenter 3D FEA Expert

Version 0.1.2 integrates the official Simcenter 3D service bundle with the FEA expert skills.

## Referenced MCP services (`type: ref`)

- **Simcenter 3D**: model inspection, mesh generation and visibility.
- **Batch Post**: result post-processing connector.
- **Designcenter Open**: API discovery, journals and model reads.
- **Product Support**: Siemens documentation search.
- **Simcenter Nastran MCP** (optional): Nastran deck and solver output diagnostics.

All MCP servers are referenced by name (`type: ref`) in the agent recipes and provided by the official Simcenter 3D / Product Support bundles or host configuration. No duplicate `[[mcps]]` launcher scripts, product executables, or new MCP implementations are shipped in this bundle.

## Included agents

- **Simcenter 3D FEA Expert** (coordinator)
- **BatchPost Agent** (official)
- **Designcenter Open Journal Agent** (official)
- **Simcenter 3D Documentation Agent** (official)
- **Simcenter 3D Assistant** (official)

Six FEA subagents remain available to the coordinator: model inspector, journal author, solver diagnostics, result post-processing, independent verifier and Product Support documentation.

## Skills

38 skills: 20 canonical FEA specialists, the Parametric SOL101, Airframe Structural Verification (`simcenter-airframe-structural-verification`), Aerostructures Load Case Filtering (`simcenter-aerostructures-load-filtering`), Aerostructures Margin of Safety (`simcenter-aerostructures-margin-of-safety`) and tool-routing overlays, plus 13 official Simcenter 3D/Designcenter Open/BatchPost skills with their references. Official bytes are hash-pinned in the source receipt.

## External integrations

MCP servers (`Simcenter 3D`, `Batch Post`, `Designcenter Open`, `Product Support`, and optional `Simcenter Nastran MCP`) are supplied by the official installed bundles or host MCP configuration and bound by name via `type: ref`. Because this bundle does not re-declare `[[mcps]]` launchers, no duplicate MCP server entries or custom `mcps/fea-*` folders are created in `productdata`.

## Safety and evidence

Read-only FEA subagents use tool allowlists. Live actions require an explicit request, an identified owned copy and independent readback. Captured official sources stay immutable; packaged agents and all 13 official skills receive a deterministic FEA safety contract that overrides conflicting legacy guidance. Documentation and pagination are current-catalog/schema gated. Sandbox SUCCESS without observable output is not proof of correct execution. Missing/uncomputed mesh metrics stay UNVERIFIED, and quality thresholds must be problem-specific. Source guidance, sandbox responses, native execution, saved files, licensed solver output and engineering acceptance are separate.

Evidence classes: SOURCE_TESTED, DOCUMENTED_2606_CANDIDATE, MCP_2612_DISCOVERED, HOST_QUALIFIED, NATIVE_EXECUTED, SOLVER_VERIFIED, ENGINEERING_ACCEPTED. Missing BC/load/solution/solve/save capability stays BLOCKED_BY_OFFICIAL_MCP_CAPABILITY. A built/installed package does not establish native engineering acceptance.

## Local distribution scope

Official service recipes and skills were captured from the installed Simcenter 3D bundle for this local custom package. Siemens notices remain unchanged. Public redistribution, signing, registry release and OSS/legal clearance are not established.
