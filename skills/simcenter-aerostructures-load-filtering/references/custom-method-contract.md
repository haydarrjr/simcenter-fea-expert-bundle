# Custom load case filtering contract

Register a module descriptor (`.xmd`) under `UGII_AEROSTRUCTURES_MODULE_PATH`. In its `module` element, give each `method` a stable ID and a path to its XML descriptor. In the method descriptor, declare `type="loadfiltering"`, `script="python"`, the input parameters and a Boolean output indexed by load case (`type="boolean" indexby="lc"`). Keep descriptor IDs, evaluation inputs and output IDs aligned. Validate the descriptor against the installed module schema.

The Python evaluation script receives a method context. Read input arrays with `context.GetInputTable().GetLoadArrayPropertyValue(parameter_id).GetValues()`. For a Nodal Force Report input, declare `type="free_body_load_extraction"` and the physical measure of the selected component. Read Boolean, integer and scalar inputs with the corresponding typed property getter.

| Operation | Installed ABB binding to verify | Input contract |
| --- | --- | --- |
| Select scalar extrema | `NXOpen.CAE.AeroStructures.Author.ABB.Lcf1dMinMax(values, positive_only, count, selected)` | One finite scalar per case, a sign policy and a positive retention count |
| Select a two-dimensional convex hull | `NXOpen.CAE.AeroStructures.Author.ABB.LcfConvexHull(x, y, tolerance, selected)` | Two finite arrays in identical case order and a tolerance defined in the coordinates used by the hull. Establish the scaling before mixing force and moment |

Initialize the output mask with one Boolean per admitted load case. Check the return status against the installed binding before publishing it with `context.GetOutputTable().GetBooleanArrayPropertyValue(output_id).SetValues(selected)`. Verify the selected case identities through native readback. Independently check extrema, ties or hull boundary membership using the declared filtering policy.
