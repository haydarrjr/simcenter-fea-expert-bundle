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
