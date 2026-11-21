# BatchPost camera XML

Use a standard camera from the current schema when that meets the request. For a custom rotation, bind the model frame and unit enum and use a complete orthographic XML with `fitview=true`. For exact framing, start with an exported camera for the intended model or derive the view from its verified extents, then inspect the export with `fitview=false`.

| Field | Contract |
|---|---|
| `Rotation` | Nine row-major doubles for camera right, up and backward axes in model coordinates. Validate unit-length rows, pairwise orthogonality and determinant near +1 |
| `Translation` | Three doubles for model centre offset. Derive from the current model/view when fitting is disabled |
| `Perspective`, `IsPerspectiveOn` | Use `0 0 0` and `0` for orthographic. For perspective, obtain the encoded eye vector from an exported or independently validated camera |
| `LookTo`, `IsLookToAbs` | Target triple and relative (`0`) or absolute (`1`) coordinate flag |
| `UseXyClip`, `CameraXyClip/@XyClip` | Flag and four values ordered `x_min x_max y_min y_max` in model units. Include the child even with clipping disabled |
| `CameraScale/@Scale` | Required positive scale. Derive saved framing from the intended view |
| `FrontClipStatus`, `BackClipStatus`, `FrontClip`, `BackClip` | Optional plane flags and signed distances in model units. Derive from intended depth limits when enabled |
| `PartUnits` | Match the target. NX enum values include `0` mm, `1` inch, `3` m, `4` µm. `2` is unset/unknown |

Use `0` or `1` for Boolean attributes. This synthetic orthographic file exercises the identity rotation (view from +Z). Its scale and disabled extents allow an orientation test with `fitview=true`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Camera Rotation="1 0 0 0 1 0 0 0 1" Translation="0 0 0" Perspective="0 0 0"
        LookTo="0 0 0" IsPerspectiveOn="0" IsLookToAbs="0" UseXyClip="0" PartUnits="0">
  <CameraXyClip XyClip="0 0 0 0"/>
  <CameraScale Scale="1"/>
</Camera>
```

For a general orthographic direction, normalize the vector from the target toward the camera to obtain backward. Take right as the normalized cross product of the preferred up vector and backward, then up as backward crossed with right. Choose a different preferred up vector if it is parallel to backward.

Parse the file and check the fields and basis. When testing export, pass the actual XML path through `camera`. Compare with a different rotation and inspect the images for orientation, visibility and clipping. Record structural validation, reader acceptance and framing evidence according to what was exercised.
