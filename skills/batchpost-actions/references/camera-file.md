# Create a BatchPost Camera File

## Scope

This document is a self-contained guide to the BatchPost `<Camera>` format. Its numeric examples are model-specific reference material, not prevalidated defaults for the user's model.

Distinguish two goals:

- **Create/test a camera orientation:** a complete documented camera below may be used. Run it with `fitview=true` so BatchPost adapts framing to the current model, then inspect the result. This validates that the file is accepted and the rotation affects the view.
- **Reproduce an exact saved camera/framing:** use a camera exported for that model, or derive and verify Translation, Scale, XyClip and clipping planes from authoritative model/view data. Values from another model cannot prove exact framing.

## Workflow

1. Clarify the requested view direction, model coordinate system/units, and destination path. If only a built-in orientation is needed, prefer the actual server's standard camera option. If the user specifically requests an XML file, produce the file rather than substituting a standard name and calling the task complete.
2. Choose a starting point appropriate to the goal. For exact reproduction, prefer a camera exported from NX for the same model and derive a new copy. For a new orientation or format test, start from a complete example below, preserve its required fields, and use `fitview=true` on the target model. Do not present example Translation, Scale or clips as exact target-model values.
3. Use the row-major right/up/backward convention in the reference. Validate all nine rotation values: row norms should be approximately one, pairwise dot products approximately zero, and determinant approximately +1. Check even copied example matrices. If an example fails, report the discrepancy and derive a valid basis for the requested direction rather than propagating it.
4. Preserve numeric booleans and include `CameraXyClip` and `CameraScale`, because the current format requires them. Preserve all required attributes: Rotation, Translation, Perspective, LookTo, IsPerspectiveOn, IsLookToAbs, UseXyClip and PartUnits. Front/back clip fields are optional. For a hand-authored orthographic file, use `Perspective="0 0 0"`. A requested perspective view requires a suitable exported or otherwise validated eye vector.
5. Parse the saved XML and check matrix and required reader fields independently. When export is requested, use the current MCP schema to pass the XML file path as `camera`, with a valid result and posttemplate/snapshot. Built-in-camera success is only a control test, not evidence that the XML was accepted.
6. First run a target-model export with `fitview=true` to validate file consumption and model visibility. Compare against a built-in/default camera or a second rotation to prove the XML affects the view. Run `fitview=false` only when testing the file's own Translation/Scale/clip framing; poor framing with values from another model is a model-specific mismatch, not automatically a format failure.
7. Inspect the exported image for nonblank model visibility, framing, requested direction and unintended clipping. Record actual warnings and validation results. If image contents cannot be inspected, report file acceptance and artifact evidence separately from visual acceptance. Preserve the input camera and close only a result opened and owned by this task.
8. Return the new file path, changed orientation/settings, whether fitview was used, and any model information still required. Do not report exact saved-camera reproduction when only example values plus fitview were tested.

## Camera Format Reference

### 9.3 Camera XML Schema

**Root element:** `<Camera>` with these attributes:

| Attribute | Type | Meaning |
|---|---|---|
| `Rotation` | 9 space-separated doubles | 3×3 rotation matrix, **row-major**. Row 0 = camera right axis in world space; Row 1 = camera up axis; Row 2 = camera backward axis (pointing from model toward camera). |
| `Translation` | 3 doubles | Model centre offset (world-space X Y Z). Not the eye position. |
| `Perspective` | 3 doubles | **For orthographic views (`IsPerspectiveOn=0`) always use `"0 0 0"`.** For perspective views this encodes the reciprocal-distance eye vector; obtain it by exporting from NX. Setting a unit vector here (e.g. `0 0 1`) when perspective is off will cause DSS to reject the file. |
| `LookTo` | 3 doubles | Look-at target point. Interpretation depends on `IsLookToAbs`. |
| `IsPerspectiveOn` | **0 or 1** | Perspective (`1`) vs orthographic (`0`) projection. **Use integers, not `true`/`false`.** |
| `IsLookToAbs` | **0 or 1** | Whether `LookTo` is in absolute model coordinates (`1`) or relative (`0`). |
| `UseXyClip` | **0 or 1** | Whether the XY viewport extents in `<CameraXyClip>` are applied. |
| `FrontClipStatus` | **0 or 1** | Whether the front (near) clipping plane is active. |
| `FrontClip` | double | Near clipping plane distance in model units (positive value). |
| `BackClipStatus` | **0 or 1** | Whether the back (far) clipping plane is active. |
| `BackClip` | double | Far clipping plane distance in model units (negative value, i.e. behind the model centre). |
| `PartUnits` | integer | NX unit system enum: **0 = mm**, 1 = inches, 3 = m, 4 = µm. (2 = unknown/unset.) |

> **Boolean values MUST be `0` or `1`.** NX's XML layer does not accept `true`/`false` strings for logical attributes and will reject the file with an invalid-config error.

**Child elements:**

| Element | Attribute | Type | Meaning |
|---|---|---|---|
| `<CameraXyClip>` | `XyClip` | 4 doubles | Viewport extents: **`x_min x_max y_min y_max` in model units** (not normalised). Must be present even when `UseXyClip=0`; the values are ignored in that case. |
| `<CameraScale>` | `Scale` | double | View scale factor (world units per screen pixel, approximately). Typical exported values are 0.3–1.0 for CAE models measured in mm. |

**Standard view rotation matrices** (row-major; each row is a camera-space axis in world coordinates):

```
top        — Rotation: "1 0 0  0 1 0  0 0 1"   (identity; camera looks from +Z)
trimetric  — Rotation: "0.707107 0.707107 0.000000  -0.408248 0.408248 0.816497  0.577350 -0.577350 0.577350"
isometric  — from NX; similar to trimetric but camera is placed differently
```

For the trimetric matrix above: Row 0 (right) = `(1,1,0)/sqrt(2)`, Row 1 (up) = `(-1,1,2)/sqrt(6)`, Row 2 (backward) = `(1,-1,1)/sqrt(3)`.
The rotation rows must form an orthonormal basis.

**Complete camera example (top view, mm model):**

The numeric framing values below illustrate a model with bounding extents roughly 450×300mm centred near (225, 150, 0):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Camera
  Rotation="1 0 0 0 1 0 0 0 1"
  Translation="-0 -225.0 -150"
  Perspective="0 0 0"
  LookTo="0 0 0"
  IsPerspectiveOn="0"
  IsLookToAbs="0"
  UseXyClip="1"
  FrontClipStatus="1"
  FrontClip="975.43"
  BackClipStatus="1"
  BackClip="-975.43"
  PartUnits="0">
  <CameraXyClip XyClip="-501.24 501.24 -281.88 281.88"/>
  <CameraScale Scale="0.345"/>
</Camera>
```

**Complete camera example (trimetric view, same model):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Camera
  Rotation="0.70710678118654757 0.70710678118654757 -0 -0.40824829046386307 0.40824829046386307 0.81649658092772615 0.57735026918962584 -0.57735026918962584 0.57735026918962584"
  Translation="-159.099 -214.330 43.301"
  Perspective="0 0 0"
  LookTo="0 0 0"
  IsPerspectiveOn="0"
  IsLookToAbs="0"
  UseXyClip="1"
  FrontClipStatus="1"
  FrontClip="1351.34"
  BackClipStatus="1"
  BackClip="-1351.34"
  PartUnits="0">
  <CameraXyClip XyClip="-465.07 465.07 -261.53 261.53"/>
  <CameraScale Scale="0.372"/>
</Camera>
```

**Authoring notes:**
- **The only portable hand-authored fields are `Rotation`, `IsPerspectiveOn`, `PartUnits`, and `IsLookToAbs`.** All other fields (`Translation`, `Scale`, `FrontClip`, `BackClip`, `XyClip`) depend on the specific model's extents and cannot be guessed. Work with the user to determine model scale (they either tell you, or agree to determine the bounding box from a CSV result export)
- The safest strategy: export from NX, then replace only `Rotation` if you need a different view direction
- `Rotation` rows must form an orthonormal right-handed basis. Use exact fractions (e.g. `1/sqrt(2) = 0.70710678118654757`) to avoid numerical rejection.
- For orthographic views, always set `Perspective="0 0 0"`. Any non-zero value (especially a unit vector) will cause DSS to reject the file.
- `FrontClip` and `BackClip` are typically set to +/-(half the model's bounding-sphere radius). Setting them to 0 while `FrontClipStatus=1` may clip the entire model.
- `<CameraXyClip>` must always be present; if `UseXyClip=0` the values are ignored and you can write zeros.
