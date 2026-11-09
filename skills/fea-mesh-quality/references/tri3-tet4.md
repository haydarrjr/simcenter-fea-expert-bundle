# TRI3/TET4 source quality reference

Trigger when genuine node coordinates (with length unit), element connectivity,
declared owner/property bindings and a provenance-bearing project threshold
policy are available. Reject a claim based on only element counts.

**Geometry:** TRI3 `A=|| (b-a) cross (c-a) ||/2`. Oriented signed projection
uses a declared normalized reference normal; a negative sign detects
reversal. TET4 `J=det(b-a,c-a,d-a)`, `V=J/6`. For both, the
shape ratio is longest edge over shortest vertex-to-opposite-side altitude.
A zero-volume TET4 is degenerate; a negative J is inverted even with an
acceptable absolute volume. This is not the native solver's maximum Jacobian
parameter or a higher-order integration point evaluation.

**Independent numbers:** Right TRI3 (0,0),(1,0),(0,1) has A=1/2 and
ratio=2. Right-angled TET4 with unit coordinate edges has J=1,
V=1/6, ratio=sqrt(6). Swapping 2 TET4 nodes yields J=-1.

**Applicability:** Linear TRI3/TET4 only. Supplied normal is required
for TRI3, and one closed mesh family is evaluated per request.
Declare max ratio, min area/volume, minimum normal alignment, coincidence
tolerance, connected-component count, and their provenance. Spatial
coincidence is reported without merging. Duplicates require explicit
pair provenance; even intentional duplicates retain a warning.

**Escalation:** TET10/TRI6/HEX, quadratic Jacobians, shell warpage,
contact discontinuity, recovery quality, stress singularities, native
quality controls and actual solver thresholds need separate evidence.
Refer to P08 source guide (source: fea_expert_agent_plugin/docs/qualification/mesh-vvuq-source-slice.md).
