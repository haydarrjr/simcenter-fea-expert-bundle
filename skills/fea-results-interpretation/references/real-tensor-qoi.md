# Real tensor mechanics, case identity and negative evidence

Trigger only when all six **real** components, explicit stress/strain
dimension and unit, frame/proper rotation history, source artifact
declaration, material/owner/position and recovery/averaging provenance
are supplied. Run the strict offline source-only `assess-tensor` CLI.

- Components: `XX,YY,ZZ,XY,YZ,XZ`; do not reinterpret permutations.
- Stress tensor XY/YZ/XZ values are physical tensor shear; small strain
  `ENGINEERING` shear is gamma=2 epsilon_tensor.
- Principal values are symmetric-matrix eigenvalues; mean stress is
  trace/3; J2=1/2 dev:dev; von Mises=sqrt(3J2); Tresca difference is
  principal_max - principal_min. Do not assign stress units to strain.
- Positive physical example: sigma_xx=100 MPa, other components zero:
  principal [100,0,0] MPa and von Mises 100 MPa; 45-degree rotation
  preserves both. Pure shear XY=60 MPa produces von Mises
  60 sqrt(3) MPa and principal [60,0,-60] MPa.
- For MAX_VON_MISES retain the **entire same source tensor** with its
  owner/material/position/shell side/case/step, not elementwise component
  extrema. Do not mix shell top/bottom or dissimilar material/region.
- Reject stale or duplicate transform IDs, left-handed matrices, unknown
  shear convention, undefined location, unsupported ply/beam/complex/PSD
  recovery, unverified averaging and unauthenticated native claims.

See P09 verification guide (source: fea_expert_agent_plugin/docs/qualification/tensor-qoi-source-slice.md).
