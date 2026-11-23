# BatchPost entity selection XML

Bind nodes or elements by their FEM labels in the exact model/result scope. Resolve a named region through available mesh or result evidence. Ask for the mapping if that evidence cannot identify the labels.

Use `SelectionEntities` with `ElementIds`, `NodeIds`, or both as needed. Replace the tokens below with comma-separated integer labels, inclusive ranges, or a combination. Reject malformed or reversed ranges.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SelectionEntities>
  <ElementIds>${element_labels}</ElementIds>
  <NodeIds>${node_labels}</NodeIds>
</SelectionEntities>
```

For whole-model contours, use the selector advertised by the server. Graphs need explicit entities. Use the actual XML path in `selentity` when testing a file, with no competing inline selector. Check the parsed labels against model scope and verify exported labels when available. XML syntax and image creation alone cannot establish correct entity selection.
