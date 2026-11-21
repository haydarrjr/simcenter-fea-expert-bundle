# BatchPost entity selection XML

Bind nodes or elements by their FEM labels in the exact model/result scope. Resolve a named region through available mesh or result evidence. Ask for the mapping if that evidence cannot identify the labels.

Use `SelectionEntities` with `ElementIds`, `NodeIds`, or both as needed. Each child takes a comma-separated list of integer labels or inclusive ranges. Reject malformed or reversed ranges. These synthetic labels illustrate both forms.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SelectionEntities>
  <ElementIds>1-3</ElementIds>
  <NodeIds>10, 20</NodeIds>
</SelectionEntities>
```

For whole-model contours, use the selector advertised by the server. Graphs need explicit entities. Use the actual XML path in `selentity` when testing a file, with no competing inline selector. Check the parsed labels against model scope and verify exported labels when available. XML syntax and image creation alone cannot establish correct entity selection.
