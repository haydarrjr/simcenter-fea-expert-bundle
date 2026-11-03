# Simcenter 3D FEA Expert

Version 0.1.2 integrates the official Simcenter 3D service bundle with the FEA expert skills.

## Included MCP services

- **Simcenter 3D**: model inspection, mesh generation and visibility.
- **Batch Post**: result post-processing connector.
- **Designcenter Open**: API discovery, journals and model reads.

The three launchers invoke the existing Simcenter 3D 2612 installation. No product executable or new MCP implementation is shipped. Configure `UGII_BASE_DIR` for the actual product installation. The local manifest default mirrors the corrected installed official connector configuration.

## Included agents

- **Simcenter 3D FEA Expert** (coordinator)
- **BatchPost Agent** (official)
- **Designcenter Open Journal Agent** (official)
- **Simcenter 3D Documentation Agent** (official)
- **Simcenter 3D Assistant** (official)

Six FEA subagents remain available to the coordinator: model inspector, journal author, solver diagnostics, result post-processing, independent verifier and Product Support documentation.

## Skills

35 skills: 20 canonical FEA specialists, the Parametric SOL101 and tool-routing overlays, plus 13 official Simcenter 3D/Designcenter Open/BatchPost skills with their references. Official bytes are hash-pinned in the source receipt.

## External integrations

Product Support is still supplied by the Product Support bundle. Simcenter Nastran MCP remains an optional external solver-diagnostic integration. The official Simcenter 3D bundle is no longer required to supply the three MCP configurations or the four agents listed above.

The official Simcenter 3D bundle and this package expose the same MCP display names and official agent/skill names. If both remain enabled, do not assume which definition takes precedence. The FEA launcher folders are namespaced to avoid file overwrite, but that does not eliminate name-resolution ambiguity. Review enabled bundles before starting a new session; do not delete the shared MCP folders manually.

## Safety and evidence

Read-only FEA subagents use tool allowlists. Live actions require an explicit request, an identified owned copy and independent readback. Captured official sources stay immutable; packaged agents and all 13 official skills receive a deterministic FEA safety contract that overrides conflicting legacy guidance. Documentation and pagination are current-catalog/schema gated. Sandbox SUCCESS without observable output is not proof of correct execution. Missing/uncomputed mesh metrics stay UNVERIFIED, and quality thresholds must be problem-specific. Source guidance, sandbox responses, native execution, saved files, licensed solver output and engineering acceptance are separate.

Evidence classes: SOURCE_TESTED, DOCUMENTED_2606_CANDIDATE, MCP_2612_DISCOVERED, HOST_QUALIFIED, NATIVE_EXECUTED, SOLVER_VERIFIED, ENGINEERING_ACCEPTED. Missing BC/load/solution/solve/save capability stays BLOCKED_BY_OFFICIAL_MCP_CAPABILITY. A built/installed package does not establish native engineering acceptance.

## Local distribution scope

Official service recipes, skills and launcher scripts were captured from the installed Simcenter 3D bundle for this local custom package. Siemens notices remain unchanged. Public redistribution, signing, registry release and OSS/legal clearance are not established.
