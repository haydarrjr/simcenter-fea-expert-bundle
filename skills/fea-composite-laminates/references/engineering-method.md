# Classical laminate source workflow

The continuum/composite method (source: fea_expert_agent_plugin/docs/engineering/multiphysics-v3.md)
documents NASA RP-1351 provenance and independent reproduction. The source
request explicitly uses SI: Pa, m, N/m, N and K. Plies run from negative z to
positive z; `strain(z)=midplane_strain + z*curvature` with engineering gamma_xy.

For each transformed ply stiffness Qbar, integrate:

`A = sum Qbar*(z1-z0)`;
`B = sum Qbar*(z1^2-z0^2)/2`;
`D = sum Qbar*(z1^3-z0^3)/3`.

Integrate transformed thermal eigenstrain over the same thickness coordinates.
Then `[N;M] = [[A,B],[B,D]]*[epsilon0;kappa] - [NT;MT]`.
Do not convert engineering shear by rotating its components as though gamma_xy
were tensor shear: transformation must preserve virtual work.

Read the complete example
unsymmetric laminate (source: fea_expert_agent_plugin/examples/multiphysics_v3/unsymmetric_laminate.json)
before changing its material/ply fields. `prescribed_generalized_strain` provides
mixed strain/curvature constraints; the remaining components are solved from
declared resultants. Thermal-gradient input is kelvin per metre, while
`delta_T_midplane` is a temperature increment, not absolute Kelvin.

Reverse the stack while keeping material/angle/thickness tied to each ply.
In a reflected laminate A and D remain unchanged, B changes sign, and the
appropriate curvature/coupling response changes. Equal membrane stiffness
therefore does not establish an equivalent unsymmetric component.

For a result comparison, require element + physical ply identity + ply surface
+ frame + component + solver state. Reject an ambiguous layer number instead
of guessing it from a sorted array. A maximum ply stress without surface/sign
cannot distinguish a correct stack from a reversed one.

The method assumes thin laminae, plane stress, linear elasticity and intact
bonding. It is not a transverse/3D stress recovery, delamination, progressive
damage, fatigue or laminate strength acceptance engine. Route those questions
through model-form research and qualified solver/result evidence; keep the
computed ABD and ply fields useful as independent checks.
