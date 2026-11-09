# Engineering from evidence to a defensible decision

## Contents

1. Evidence and physical intent
2. Coupled decision procedure
3. Executable flange investigation
4. API and Runtime boundary
5. Interpreting failures and choosing the next experiment

## Evidence and physical intent

Begin with the physical question and the quantity that could change a decision:
joint opening, bolt force range, interface moment, resonant amplification,
temperature-induced restraint or a location-specific stress. A solver sequence
and a green job status do not identify that quantity. Obtain the effective model
and selected step from artifacts or the qualified Runtime read tools. Preserve
model, revision, owner, mesh revision, frame, load state and source bytes.

The executable entry is `python -m fea_agent run-case CASE.json`. A case contains
the natural-language request, expected physical model identity and named source
artifacts with SHA-256 hashes. The runner reads each bounded file once, checks
all hashes and cross-artifact identities, then dispatches by the inspected
schema. JSON text is never executed. The runner recognizes joint models,
nonlinear evidence and mounted-assembly models. It does not ask the user to
declare whether physics or convergence has passed.

`route-expert "request text"` is an explainable triage aid. It is not native
authorization or a replacement for understanding the request. A mixed request
can activate contact, nonlinear and thermal expertise together. A CAD-only
request belongs to the NX owner; an exact API declaration belongs to Siemens
documentation. If the case's data describe a different engineering domain,
the runner rejects the mismatch instead of silently analyzing a convenient file.

## Coupled decision procedure

Construct the load path as equations and state transitions. For a preloaded
joint, the bolt and compressed members form coupled elastic paths; external
separation first unloads contact while increasing bolt force, and opening changes
the tangent stiffness. A linear `preload + applied force` estimate is therefore
not a general bolt-load law. For a mounted assembly, an off-center mass and a
force applied away from the reference origin couple translations and rotations;
matching total force alone does not preserve moment or virtual work.

Choose the cheapest model that can falsify the proposed answer. The reduced
joint model can disprove an impossible preload or contact state; it cannot
establish thread stripping capacity or local flange stress. The six-DOF assembly
reference can identify a lost interface moment or changed mount load path;
flexible casing modes require a separate correlated model. Maintain alternatives
when model-form evidence is insufficient, with a specific observation that
would discriminate them.

Compare result claims to independent invariants: external and reaction
resultants in one frame, contact complementarity, mass/inertia transformation,
energy and source-state consistency. Keep observed facts, computed quantities
and inferred root causes separately labeled. Rank a hypothesis by the evidence
it explains and prescribe a one-variable experiment; do not assert that a
residual plateau proves a unique contact-penalty problem.

## Executable flange investigation

Run `python -m fea_agent run-case examples/engineering_v2/joint_case.json`.
The manufactured eight-bolt case is an engineering reference, not a solver run.
It contains pretension, lock, differential heating, eccentric service and unload
states, plus a deliberately contradictory nonlinear evidence record.

The model derives station stiffness from E, area and grip length. Initial bolt
force is 20 kN each. Heating increases it to approximately 36.957 kN before
the eccentric service load redistributes it. Under 160 kN separation with
15 kN m and 3 kN m bending moments, B2–B5 open and the maximum bolt force is
approximately 56.048 kN. A local stick trial exceeds the Coulomb limit at some
remaining contacts, so a post-slip solution is required. Returning a universal
linear safety factor at this point would discard the changed mechanism.

The second artifact says the final increment converged, while its corresponding
contact summary does not. Independent observations show an 18 kN axial balance
defect and 120 J artificial energy against 1000 J strain energy. The case runner
returns `SOURCE_EVIDENCE_REJECTED`, identifies the offending artifact and retains
the ranked diagnostic evidence. A polished report containing the right model
name and a converged label cannot override those calculations.

The tests also compare the normal-contact solution with an independent
50-digit Decimal enumeration of all 256 contact sets. That comparison is a
source numerical oracle; it is not a substitute for flexible-flange validation.

## API and Runtime boundary

Prepare native work with `compile-api`, using exact .NET 2606 declarations in
the vendor API workflow (source: fea_expert_agent_plugin/docs/engineering/vendor-api-workflows.md).
The compiled recipe contains owner bindings, configuration, builder cleanup,
required effects and unresolved edges. It cannot create a capability by naming
one. The FEA Runtime client uses actual MCP `list_tools`/`call_tool` contracts
of a supplied session; it creates no server or endpoint.

Read Runtime compatibility (source: fea_expert_agent_plugin/docs/architecture/runtime-compatibility.md)
before native work. Current main's discovery/session interface and a separately
pinned unmerged Java-read candidate are different profiles. CAE mutation remains
a concrete upstream capability gap. Generate and test the FEA-side request,
then report that dependency; do not quietly relabel a CAE write as a CAD write.

## Interpreting failures and choosing the next experiment

A malformed identity or changed artifact stops computation. A physical
contradiction rejects the claim. Separation, local slip or a failed rigid-body
screen requests a more appropriate model. A timeout after dispatch requires
reconciliation of the existing operation, not blind replay. A source calculation
can complete while native, solver and engineering acceptance remain `NOT_RUN`.

Finish with the computed decision, supporting artifacts, the strongest
counterexample tested and the next discriminating observation. State what the
implemented model proves. Preserve unresolved physics instead of padding a
report with general checks or asking the caller to mark them complete.
