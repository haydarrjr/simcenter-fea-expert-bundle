# SOL101 engineering evidence contract

Resolve documented APIs with the Designcenter Open discovery tools (`dcopen-pattern-lookup-tool`, `dcopen-keyword-search-tool`, `dcopen-semantic-search-tool`, `dcopen-list-classes`, `dcopen-class-info`, `dcopen-member-info`) and release-specific documentation via the Product Support `search` tool (`documentation-search-tool` only if advertised in the current Designcenter Open catalog). Never invent tool or symbol names; discover the catalog each session. Preserve product, documentation set, release/SKU, document ID, provenance and source/content status. Record reaction, displacement, units and benchmark checks separately.

Include a public URL only when externally resolvable. Never expose internal or synthetic locators, `*.invalid`, localhost or snapshot locators as public links; those belong only in requested debug diagnostics. Local engineering artifacts may be linked separately as files.

Preserve distinct failure classes: invalid argument, backend failure, license failure, solver fatal, timeout, not connected (`dc_connection_status`). For documentation-search punctuation parser errors, retry once replacing raw ASCII apostrophes and backticks without changing release/product.

Analytical reference or source tests establish PARTIAL evidence. Full PASS requires FEM/SIM, exported deck, licensed solve (parsed with `parse_f06_file`), reaction/displacement/convergence checks, associative updates and separate GUI acceptance. Missing steps are NOT_RUN; unknown outcomes UNVERIFIED. Tag every claim with an evidence class: SOURCE_TESTED, DOCUMENTED_2606_CANDIDATE, MCP_2612_DISCOVERED, HOST_QUALIFIED, NATIVE_EXECUTED, SOLVER_VERIFIED, ENGINEERING_ACCEPTED.
