# Verify restored states and finite kinematics

## Restart

Record the state requested for restoration, including displacement, stress, internal material variables and contact, and velocity or acceleration for a dynamic continuation. For a restart selected within one run, distinguish the restoration source, the immediate preceding step and the start of the target time interval. For a separate-run restart, bind database generation, model and mesh compatibility, and all continuation files.

Use a controlled continuation whose first accepted result differentiates the requested source from a fresh or sequential start. Keep the target load history, restraints and output locations fixed while changing only the restart selection. Verify the solver's restoration record as well as the changed path. Where history variables matter, compare the first accepted increment and a later state. Check the semantics of the reported start-of-subcase frame before treating it as the restored state.

## Large rotations and deformation

State whether the response is governed by large rotations, finite strain, or both. A geometric update can be essential even when material response stays linear. Define reference and current configurations, follower versus fixed directions, strain measure and stress measure before setting the comparison.

A stress-free rigid motion provides an objectivity check for a suitable element and material formulation. Prescribe a known rotation at the boundary, compare an independent free coordinate with the rigid transformation, and check that final stresses and reactions are within engineering tolerances for the unloaded state. Check the deformation along the path as well as the endpoint. For finite-strain acceptance add a separate reference with measurable stretch and the same stress and strain measures as the selected solver output.
