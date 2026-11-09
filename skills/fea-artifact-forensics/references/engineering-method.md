# Authentic artifact investigation

## Tools and reproducible methods

Use the full reader contract (source: fea_expert_agent_plugin/docs/engineering/artifacts-v3.md) for
qualified variants, selection keys, original licenses and immutable examples.
The external artifact manifest (source: fea_expert_agent_plugin/examples/artifacts_v3/upstream-artifacts.json)
contains source commits and hashes; independent qualification downloads those
exact public bytes. No private source model or native solver binary is included.

The MCP request to `fea_inspect_artifact` has `path`, and optional `format`,
`units` and `options`. For example, select `nastran-op2` and result names such
as `displacements` or `stress.ctetra_stress`, then a subcase, row range and
state range. The reader report declares selected/omitted data; inspect that
declaration before interpreting a missing record as a physical zero.

For assembled decks, `fea_inspect_bdf_bundle` takes `files` (relative path to
original text), `entry`, optional `units` and `options`. The include graph,
per-file hashes, expansion order and derived deck identity remain separate.
An empty/missing include or conflicting effective case must fail explicitly.

## Physical keys

A result is indexed by model/revision, solver subcase, analysis kind, time or
frequency or mode, quantity/component, frame/units, element/node and recovery
location. A shell centroid is not a shell corner; ply number is not a thickness
coordinate; a beam station is not a GRID; node label is not an array index.
Check element-node recovery membership against actual element connectivity.
Only documented centroid markers may omit a physical grid membership check.

OP4 matrix dimensions do not encode the associated DOF map. Preserve matrix
form, dense/sparse layout and complex parts. Require independent row/column
mapping, units and constraint context before treating a matrix as physical
stiffness/mass. Symmetry alone does not establish positive energy or completeness.

For a real symmetric stress tensor, independently compute
`sqrt(((sx-sy)^2+(sy-sz)^2+(sz-sx)^2)/2 + 3*(txy^2+tyz^2+txz^2))`.
This checks an imported von Mises field, while retaining the signed tensor for
comparison. Flipping every shear sign preserves that invariant but changes
physical directions. For complex response, compare real and imaginary
components at the same frequency; amplitude-only equality loses phase.

## Wrong-answer investigations

- Move a recovery row to an existing GRID outside its element: reject the
  mapping even if all global label sets and values still look plausible.
- Reverse a composite ply order: compare physical ply identity and surfaces,
  not only the maximum scalar value. Use ABD/thermal recovery to test coupling.
- Replace a complex response by its conjugate: amplitude may agree while the
  source phase and correlated response differ. Preserve and compare both parts.
- Change a subcase/time without changing values: reject the physical-state join.
- Supply a native `.fem` file as though it were BDF: reject ambiguity; obtain an
  actual exported source representation through the separately qualified owner.

The parser can establish format compatibility and contradictory identities. It
cannot prove that an imported file came from the claimed solver or that the
constitutive law represents the real part. Carry these gaps into the decision.
