# Imported CAD to Simcenter model

Inspect the imported assembly via Designcenter Open and Model Inspection. Establish import units and provenance per body, assembly occurrence transforms, physical interfaces, geometry defects and the extent of healing or idealization. Retain the map from native body/face to property, mesh, load, result and support. Name/position matches alone are insufficient for face mapping after geometry changes.

Select the expected element family, regionwise target size and mesh convergence quantities. Check for thin-region, fillet, notch, bolt/contact and load application sensitivities. Retain intended connection separations. Audit actual element type and order, midside geometry and physical region ownership. Any change to mesh, interface or boundary state needs an owned copy, qualified tool and readback.

Use [boundary-transfer method](../../fea-open-meshing/references/engineering-method.md) to check mapped load and power, and [solver investigation](../../fea-solver-investigation/SKILL.md) for compatible deck/results. Use a compatible independent mechanics bound to test scale, transfer and deflection. Distinguish CAD inspection, mesh generation and solve evidence.
