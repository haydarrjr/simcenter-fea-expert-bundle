# Real tensor mechanics, case identity and negative evidence

Trigger only when all six **real** components, explicit stress/strain
dimension and unit, frame/proper rotation history, source artifact
declaration, material/owner/position and recovery/averaging provenance
are supplied. Use actual labeled values from a qualified result read.

- Components: `XX,YY,ZZ,XY,YZ,XZ`; do not reinterpret permutations.
- Stress tensor XY/YZ/XZ values are physical tensor shear; small strain
  `ENGINEERING` shear is gamma=2 epsilon_tensor.
- Principal values are symmetric-matrix eigenvalues; mean stress is
  trace/3; J2=1/2 dev:dev; von Mises=sqrt(3J2); Tresca difference is
  principal_max - principal_min. Do not assign stress units to strain.
- Use uniaxial stress to check that von Mises equals the axial stress magnitude.
  Pure shear of magnitude `τ` has principal values `τ, 0, -τ` and von Mises
  `sqrt(3) τ`. Proper rotations preserve principal stresses and von Mises.

- For MAX_VON_MISES retain the **entire same source tensor** with its
  owner/material/position/shell side/case/step, not elementwise component
  extrema. Do not mix shell top/bottom or dissimilar material/region.
- Reject stale or duplicate transform IDs, left-handed matrices, unknown
  shear convention, undefined location, unsupported ply/beam/complex/PSD
  recovery, unverified averaging and unauthenticated native claims.
