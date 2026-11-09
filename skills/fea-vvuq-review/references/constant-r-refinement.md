# Constant refinement-ratio Richardson source reference

Use only when the solver family/release, model/material/support/load case,
frame, position, result recovery/averaging, tensor or scalar component,
QoI definition, physical dimension, h-definition and singularity review are
all pinned across at least 3 mesh revisions. Mesh IDs/revisions may change.

For constant r>1, if adjacent QoI differences keep one nonzero sign
and their magnitude decays, compute:
`p=ln(|q_c-q_m|/|q_m-q_f|)/ln(r)`;
`q_inf=q_f+(q_f-q_m)/(r^p-1)`;
`GCI_abs=F_s*|q_inf-q_f|`, with **user-declared** safety factor
F_s>1, source-provenance and explicit abs/relative acceptance budget.
For 4+ levels, consecutive observed-order estimates must agree within
a separately declared maximum spread. A 3-level positive p cannot prove
the asymptotic hypothesis; independent physics is still required.

**Falsifier:** q*=10, C=3, p=2 gives q(h)=10+3h². At
h=(0.8,0.4,0.2,0.1), q=(11.92,10.48,10.12,10.03), p=2,
q_inf=10, fine error=0.03. F_s=1.25 gives GCI_abs=0.0375.
A 0.05 absolute budget passes numerically; 0.01 fails.

**Fail closed:** Unequal r, oscillatory signs, zero/roundoff-dominated
differences, increasing corrections, unstable order, singularity or
governing-location jump, altered physical identity, unavailable tolerances
or invalid h order return indeterminate/error as appropriate.
This source comparison neither validates production local stress peaks nor
runs Siemens adaptivity or a solver. See
P08 source guide (source: fea_expert_agent_plugin/docs/qualification/mesh-vvuq-source-slice.md).
