# Metric-aware modal comparison

For symmetric positive definite metric W, factor
`W=L L.T`; transform each basis by `L.T`, orthonormalize and compute the singular
values of `Qref.T Qcandidate`. Their arccosines are principal angles. This is
invariant under nonsingular changes of basis within a fixed subspace; arbitrary
individual MAC thresholds are not.

Align candidate and reference DOFs by explicit identifiers and check map uniqueness, matrix dimensions, rank, metric positivity and frequency coverage. Use diagonal observation weights or a full mass metric according to the physical comparison and available data.

An exact double mode may be represented by `[v1,v2]` or a 45-degree rotation of
that pair. Individual squared correlations can be 0.5 while both principal
angles are zero. Conversely, matching frequencies and equal vector norms can
hide a direction outside the reference subspace. Test both situations.

Use the actual exported mode vectors and verify their physical basis. Treat repeated-mode matching, mode-tracking across parameter
changes, damping identification and modal experimental validation as distinct
problems. Declare the compared clusters and limit conclusions to the state, modes and observation coordinates actually compared.
