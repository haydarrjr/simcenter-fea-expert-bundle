# Nastran artifacts and physical lineage

Identify the authorized file, byte size, SHA-256, timestamps and format. Bind deck and INCLUDEs to the effective solution/subcase. Resolve includes relative to their containing files and stay within approved roots. Do not derive stale status from filenames alone. Use internal deck/model identity, run records, exact paths, compatible mesh/units and timestamps together.

Prefer current Nastran MCP read-only access for deck and F06. If absent, extract only identified text sections from original approved files, with a file/line record. Inspect executive case, case control, load/SPC/MPC bindings, element/property/material mapping, solver identity, completion and warning context. Unresolved include or load references make the effective-deck inspection partial.

Use BatchPost to open the exact OP2 before catalog and exports. Preserve raw field names, label type, state, location (element, corner, node, ply or integration point), units, stress recovery and frame. Validate a cross-artifact association by explicit model/job lineage before joining. Missing reader coverage or unproven revision lineage limits claims, while authentic archival observations can still be published as such.
