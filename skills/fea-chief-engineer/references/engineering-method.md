# Engineering from evidence to a defensible decision

## Contents

1. Evidence and physical intent
2. Coupled decision procedure
3. Independent joint verification
4. API and Runtime boundary
5. Interpreting failures and choosing the next experiment

## Evidence and physical intent

Begin with the physical question and the quantity that could change a decision:
joint opening, bolt force range, interface moment, resonant amplification,
temperature-induced restraint or a location-specific stress. A solver sequence
and a green job status do not identify that quantity. Obtain the effective model
and selected step from artifacts or the qualified Runtime read tools. Preserve
model, revision, owner, mesh revision, frame, load state and source bytes.

Create an evidence record for the question, exact source files, model identity, checks, tolerances and status. Use the current catalog and scoped evidence to trace each quantity.

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

## Independent joint verification

For a preload-controlled joint, compare installation, lock and service states. Assess residual clamp force, contact opening, slip and load redistribution with an independent compatibility model. Rank sensitivity to preload, temperature and friction before choosing a discriminating native rerun.

## API and Runtime boundary

Prepare native work using current Siemens Help Server documentation, installed
API discovery and the actual MCP catalog. Record owner bindings, configuration,
builder cleanup, required effects and independent readback for the exact release.

Read the [runtime gate](../../fea-native-runtime-gate/SKILL.md) for qualified scope and independent observation.

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
