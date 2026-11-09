# Metric-aware modal comparison

Read the method and source ledger (source: fea_expert_agent_plugin/docs/engineering/multiphysics-v3.md)
for the principal-angle literature and qualification. For SPD metric W, factor
`W=L L.T`; transform each basis by `L.T`, orthonormalize and compute the singular
values of `Qref.T Qcandidate`. Their arccosines are principal angles. This is
invariant under nonsingular changes of basis within a fixed subspace; arbitrary
individual MAC thresholds are not.

The tool first reorders candidate DOFs by the explicit string identifiers, then
checks shape, rank, metric positivity, cluster bandwidth and frequency agreement.
It rejects unknown or duplicate maps instead of truncating arrays to equal length.
The full dense metric is bounded separately from diagonal weights; preserve the
meaning of the metric rather than substituting identity solely to fit a limit.

An exact double mode may be represented by `[v1,v2]` or a 45-degree rotation of
that pair. Individual squared correlations can be 0.5 while both principal
angles are zero. Conversely, matching frequencies and equal vector norms can
hide a direction outside the reference subspace. Test both situations.

Use the executable example (source: fea_expert_agent_plugin/examples/multiphysics_v3/repeated_modal_cluster.json)
as a contract illustration, then investigate the actual imported vectors and
physical basis. Treat repeated-mode matching, mode-tracking across parameter
changes, damping identification and modal experimental validation as distinct
problems. This implementation handles the first with declared clusters; it
does not pretend that a source match supplies measured damping or rotor stability.
