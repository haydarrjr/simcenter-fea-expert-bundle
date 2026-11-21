# Custom Load Case Filtering Module Templates (`.xmd`, `.xml`, `.py`)

These authoring patterns require validation against the installed module schema and ABB binding. Confirm input and tolerance measures, array lengths, result labels and status semantics before deployment. In this synthetic hull, both inputs use the same force unit. Mixed force and moment pairs require an explicit scaling and tolerance definition.

Parent skill: [simcenter-aerostructures-load-filtering](../SKILL.md)

## 1. Module Descriptor: `ExampleLoadFiltering.xmd`

Place this file in the directory pointed to by `UGII_AEROSTRUCTURES_MODULE_PATH`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<module id="ExampleLoadFiltering" path=".">
  <method id="ExampleNfrExtremes" path="ExampleNfrExtremes.xml"/>
  <method id="ExampleNfrHull" path="ExampleNfrHull.xml"/>
</module>
```

---

## 2. 1D Min/Max Filtering Method (`ExampleNfrExtremes`)

### Method Descriptor: `ExampleNfrExtremes.xml`
```xml
<?xml version="1.0" encoding="utf-8"?>
<method id="ExampleNfrExtremes" version="1" uiname="NFR 1D Min Max" type="loadfiltering" category="Load Case Filtering" script="python" author="Aerostructures" description="1D Min/Max load case filtering on Nodal Force Report free-body loads">
  <input>
    <parameter id="F" uiname="F" type="free_body_load_extraction" measure="Force" description="Extracted Free Body Force"/>
    <parameter id="positiveOnly" uiname="Positive Only" type="boolean" default="false" description="Consider only positive values"/>
    <parameter id="nbOfLoadCases" uiname="Number of Load Cases" type="integer" default="1" lowerbound="1" description="Number of extreme load cases to retain"/>
  </input>
  <output>
    <parameter id="B" uiname="Selected" type="boolean" description="Output list of boolean" indexby="lc"/>
  </output>
</method>
```

### Evaluation Script: `ExampleNfrExtremes.py`
```python
# nx: threaded
import NXOpen
import NXOpen.CAE.AeroStructures
import NXOpen.CAE.AeroStructures.Author


def evaluate(context):
    input_table = context.GetInputTable()

    F_prop = input_table.GetLoadArrayPropertyValue("F")
    F_values = F_prop.GetValues()

    positiveOnly = input_table.GetBooleanPropertyValue("positiveOnly")
    nbOfLoadCases = input_table.GetIntegerPropertyValue("nbOfLoadCases")

    B_values = [False] * len(F_values)
    status = NXOpen.CAE.AeroStructures.Author.ABB.Lcf1dMinMax(
        F_values, positiveOnly, nbOfLoadCases, B_values
    )

    output_table = context.GetOutputTable()
    B_prop = output_table.GetBooleanArrayPropertyValue("B")
    B_prop.SetValues(B_values)
    context.Log("ExampleNfrExtremes status: " + str(status))
```

---

## 3. 2D Convex Hull of Force Components (`ExampleNfrHull`)

### Method Descriptor: `ExampleNfrHull.xml`
```xml
<?xml version="1.0" encoding="utf-8"?>
<method id="ExampleNfrHull" version="1" uiname="NFR Force Convex Hull" type="loadfiltering" category="Load Case Filtering" script="python" author="Aerostructures" description="2D Convex Hull load case filtering on Nodal Force Report two force components">
  <input>
    <parameter id="F1" uiname="F1" type="free_body_load_extraction" measure="Force" description="Primary Free Body Force"/>
    <parameter id="F2" uiname="F2" type="free_body_load_extraction" measure="Force" description="Secondary Free Body Force"/>
    <parameter id="Tolerance" uiname="Tolerance" type="scalar" measure="Force" default="0.0" lowerbound="0.0" description="Tolerance in the coordinate units of the input force pair"/>
  </input>
  <output>
    <parameter id="B" uiname="Selected" type="boolean" description="Output list of boolean" indexby="lc"/>
  </output>
</method>
```

### Evaluation Script: `ExampleNfrHull.py`
```python
# nx: threaded
import NXOpen
import NXOpen.CAE.AeroStructures
import NXOpen.CAE.AeroStructures.Author


def evaluate(context):
    input_table = context.GetInputTable()

    F1_prop = input_table.GetLoadArrayPropertyValue("F1")
    F1_values = F1_prop.GetValues()

    F2_prop = input_table.GetLoadArrayPropertyValue("F2")
    F2_values = F2_prop.GetValues()

    tolerance = input_table.GetScalarPropertyValue("Tolerance")

    B_values = [False] * len(F1_values)
    status = NXOpen.CAE.AeroStructures.Author.ABB.LcfConvexHull(
        F1_values, F2_values, tolerance, B_values
    )

    output_table = context.GetOutputTable()
    B_prop = output_table.GetBooleanArrayPropertyValue("B")
    B_prop.SetValues(B_values)
    context.Log("ExampleNfrHull status: " + str(status))
```
