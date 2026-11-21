# Dynamic component representations

Compare representations for the target assembly, frequency band, port DOFs, physical state and recovery quantities.

| Representation | Choose when | Verify |
| --- | --- | --- |
| Full FEM | Model detail, interior fields or state-dependent properties are needed. | Actual mesh/properties, interfaces and requested recovery. |
| Mode set | A modal basis supports the requested response and needed observation points are retained. | Basis normalization, frequency coverage, modal mass and damping, port mapping, residual effects and recovery. |
| FRF set | A measured or computed transfer model describes the relevant ports over the working band. | Input/reference and output coordinates, quantity/units, phase convention, frequency grid, representation of translations and rotations, mapping and interpolation. |
| External superelement | A solver-compatible reduced component has explicit retained interface and matrix lineage. | [Generation and assembly](external-superelements.md), including recovery, bound files and retained DOFs. |

Before substitution, verify the interface transformation and compare governing frequencies, FRFs and, where needed, field recovery against an independent full representation or measurements. Compare close mode clusters as subspaces. Report operating-state or bandwidth limits with the representation. Use the [runtime gate](../../fea-native-runtime-gate/SKILL.md) for qualified edits.

[FRF set in assembly FEM](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1390975?audience=external) · [Mode set or FRF set](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1411480?audience=external)
