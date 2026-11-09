# Imported CAD: from original solid ownership to a defensible analysis

Use this method when the user provides STEP, ASCII BREP or IGES and wants a
real mesh, owned boundary conditions, remeshing or an open-source analysis.
Keep the native writer boundary separate from source import and computation.

Contents: [Engineering sequence](#engineering-sequence),
[Executable route](#executable-route), [Resource and evidence meaning](#resource-and-evidence-meaning),
[Strong falsifiers and completion](#strong-falsifiers-and-completion).

## Engineering sequence

1. Inspect original bytes using `inspect_cad`. Record source and topology
   hashes, metre units, placed body labels, geometric volume/center/bounds and
   original ownership. BREP requires a declared source length unit. Surface-only
   IGES is rejected; sewing or repairing it needs a separate explicit method.
2. State the idealization and the quantity of interest: component temperature,
   stress away from a singularity, reaction, mode, displacement or contact
   pressure. Assign each body a material and identify its physical support/load
   path. Unconnected touching solids have independent rigid-body modes.
3. Bind each physical region to an owning body and either an inspected face ID
   or its type/area/center invariants. Require exactly one match. Never carry a
   raw integer face tag into a remesh. `reconcile_cad_topology` reuses selections
   only for unchanged source and invariant records; a changed CAD file needs a
   new engineering selection decision.
4. Use `mesh_cad`, supplying the inspected topology hash, mesh size, per-body
   materials and physical selections. Check every body's volume discrepancy,
   adaptive Jacobian result, exterior coverage and parent-element/side mapping.
   A small component can lose most of its volume while a whole-assembly volume
   or positive-Jacobian check appears satisfactory.
5. Execute `analyze_cad` for the supported source Tet4 static/modal/steady
   conduction model, or consume the **full** solver mesh in the typed CalculiX
   path for Tet4/Tet10 and explicitly supported nonlinear workflows. Inspect
   actual solver state and original artifact hashes. Tet10 surface summaries
   use corner facets; solver parent/side surfaces carry quadratic integration.
6. Compare full fields, per-body equilibrium/energy, units, original geometry
   and independent theory. Refine geometry and the quantity of interest. A
   changed maximum element size alone does not establish refinement or
   convergence. Investigate disagreement before issuing an engineering decision.

`cad_interface_candidates` returns face-distance witnesses. Zero distance can
be an edge or corner touch. Require contact-area coverage, opposing surfaces,
orientation, signed gap, friction and attachment evidence before turning a
candidate into an interface. No candidate automatically becomes a tie.

Shared mesh nodes between bodies are rejected by default. Only declare
`shared_topology="continuous"` when the original shared CAD topology should
impose displacement or temperature continuity. This means perfect transfer of
that field; it does not model finite interface resistance, friction or slip.
Check the reported shared-node count and each owner's surface side.

## Executable route

Source MCP calls include an artifact-root-relative `path`; the server reads
the original file under artifact custody. Direct Python calls take the exact
bytes and the same request without `path`:

```python
from pathlib import Path
from fea_agent.cad_assembly import inspect_cad, mesh_cad

data = Path("assembly.step").read_bytes()
inventory = inspect_cad(data, {"format": "step"})
mesh = mesh_cad(data, {
    "format": "step",
    "topology_sha256": inventory["topology_sha256"],
    "mesh_size_m": 0.003,
    "element_order": 2,
})
```

Supply body/material and region mappings based on the returned inventory.
The default material placeholder is each body ID; it is not material data.
The executed original-CAD cases (source: fea_expert_agent_plugin/examples/cad_v4/cases.py) demonstrate
owned geometric selections, explicit two-material conduction and independent
affine load/unload physics on a real upstream STEP file.

```sh
python tools/qualify_cad_v4.py --download --ccx /absolute/path/to/ccx_2.23 --require-solver
```

Use `--ccx-library-path` only when required by the executable's loader. With no
configured executable, solver evidence is explicitly `NOT_RUN`.

## Resource and evidence meaning

Full mesh output includes nodes, elements, owned boundaries and solver surfaces.
Summary output states those omissions and cannot be used as solver input.
Larger budgets must be requested explicitly; service response/time/memory limits
remain independently enforced. `analyze_cad` requires a full Tet4 mesh and the
source continuum core's supported constitutive/analysis scope.

The research and qualification ledger (source: fea_expert_agent_plugin/docs/research/cad-v4.md)
contains original-file licensing, primary sources, formulas, full-field errors
and remaining gaps. The delivered AS1 assembly had 18 placed solids and 160
faces. A coarse mesh was rejected at 3.098% component-volume error; a refined
30,870-node mesh reduced the worst error to 1.200%. This qualifies geometric
representation at a declared tolerance, not bolt/contact service behavior.

For the original two-body STEP, refined conduction reduced cylinder heat-flow
error from 0.881% to 0.477% and maximum nodal temperature error from 0.0709 K to
0.0269 K. A curved Tet10 CalculiX run retained all original connectivity and
checked every integration stress against affine elasticity. Its exterior
conditions were manufactured and its two bodies were independent; never
describe it as a validated connected assembly.

## Strong falsifiers and completion

- Reject wrong-body selections even when the other face is geometrically
  plausible. Reject stale source/topology hashes and ambiguous matches.
- Reject positive-volume curved cells with hidden negative Jacobians. An
  executed counterexample passed all fifteen simple samples but failed the
  adaptive Jacobian assessment.
- Reject a mesh with unacceptable per-body CAD-volume discrepancy even when
  it is closed and every element has positive Jacobian.
- Reject a touching two-body static model when only one disconnected body is
  restrained. Do not invent a contact or tie to make a matrix solvable.
- Keep integration stress, recovered nodal stress, full-field temperature,
  geometry error and global balance separate in the engineering conclusion.

Return the original source identity, physical assumptions, selected owning
regions, actual analysis evidence, error trends, rejected alternatives and the
next specific engineering deficiency. Full STEP product hierarchy, controlled
healing, CAD-edit correspondence, signed contact/coverage and service model
validation remain distinct work. Native Siemens execution requires the
qualified Runtime and installed host; source capability development does not.
