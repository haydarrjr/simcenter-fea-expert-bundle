# Worked case: stepped arm, mixed loading and compliant attachment

## Input and engineering question

Complete executable request (source: fea_expert_agent_plugin/examples/model_preparation_support_arm.json)
and independent expected values (source: fea_expert_agent_plugin/examples/model_preparation_support_arm.expected.json)
are committed with this case. It is a synthetic verification scenario, not an
allowable calculation for a certified alloy or a native Siemens benchmark.

A 500 mm cantilever has a common centroidal axis and 50 mm width. The original
section depth is 40 mm over x=0–100 mm and 20 mm over x=100–500 mm. Proposal B
uses 39 mm and 20.25 mm in the same regions. Both have 600,000 mm³ volume and
1.62 kg mass; matching mass alone is not the decision criterion.

| Input | Declared value |
|---|---|
| Material | E=70,000 MPa; nu=0.33; density=2700 kg/m³; isotropic linear elastic |
| Shear factor | 5/6, energy-equivalent solid-rectangle parabolic-shear approximation |
| Point forces | +100 N at x=500 mm; -40 N at x=300 mm |
| Point couple | +8000 N·mm at x=400 mm |
| Distributed load | +0.12 N/mm from x=100 to 500 mm |
| Root compliance | k_t=20,000 N/mm; k_r=1,000,000 N·m/rad |
| Protected features | root attachment/fillet 0–20 mm; shoulder at 100 mm; tip load interface 490–500 mm |

The question is whether proposal B and omission of shear deformation fit the
specified **global reduced-model comparison budgets**, while retaining the
separate root-fillet peak-stress task. The thresholds below are deliberate
case inputs. They are not recommendations for a different part.

| QoI | Absolute allowance | Relative allowance |
|---|---:|---:|
| Tip displacement | 0.001 mm | 3% |
| Tip section rotation | 0.000001 rad | 4% |
| Bottom nominal stress at x=250 mm, RIGHT | 10,000 Pa | 4% |
| Total elastic energy including springs | 0.00001 J | 3% |
| Mass | 1e-10 kg | 0% |
| Root-fillet local peak at x=10 mm | 0.1 MPa | 3%, but this QoI is unavailable from the beam model |

Explicit regime limits are abs(u)/L<=0.01, abs(theta)<=0.02 rad,
abs(slope)<=0.02, abs(nominal strain)<=0.001, maximum depth/L<=0.2 and
maximum width/L<=0.2. These limits screen this calculation; neither their
values nor a pass establish the material allowable or 3D model validity.

## Execute and inspect

```sh
python -m fea_agent plan-domain examples/model_preparation_support_arm.json
python -m unittest tests.test_preparation_worked_case -v
```

The route reports `fea.model-preparation-assessment.v1`. `status` describes the
global approximation choice; `local_requirements`, unavailable QoIs and
`engineering_accepted=false` must also be read. Numerical results below are
independently checked against exact-rational virtual-work integrals in
`tests/test_preparation_worked_case.py`, not copied back as test expectations.

| Computed quantity | Original Timoshenko | Proposal B Timoshenko | Proposal B EB |
|---|---:|---:|---:|
| Tip displacement, mm | 1.392528914286 | 1.358320433754 | 1.356194339167 |
| Tip section rotation, rad | 0.005017900000 | 0.004870575844 | 0.004870575844 |
| Bottom nominal stress at 250 mm, MPa | 10.425000000 | 10.169181527 | 10.169181527 |
| Total elastic energy, J | 0.092668668891 | 0.090298149696 | 0.090186078840 |
| Mass, kg | 1.62 | 1.62 | 1.62 |

All models have root reactions -108 N and -60.4 N·m. Original bending energy
is 0.090440028571 J, shear energy 0.000112960320 J, translation-spring energy
0.000291600000 J and rotation-spring energy 0.001824080000 J. Omitting support
compliance would remove 0.0356 mm of tip motion, larger than the proposed
shear omission. A perfect-clamp assumption is therefore a material choice.

The original maximum nominal strain is about 0.000212571429 at the RIGHT
side of the shoulder. The maximum centerline slope occurs internally near
x=499.872330 mm, not exactly at the tip. Whole-span checks find it even when
only the stated QoI stations are requested.

## Quantitative decision

Tip displacement geometry difference is 0.034208480532 mm. Proposal B shear
omission is 0.002126094587 mm, so the accounted EB difference is
0.036334575119 mm against an allowance of 0.042775867429 mm. Energy is the
controlling global budget: 0.002482590052 J accounted difference against
0.002790060067 J. The remaining computable QoIs and declared regime checks pass.
The selected global approximation is **Euler–Bernoulli for proposal B** under
these particular hypotheses and budgets.

The root-fillet peak stress remains unavailable. Its reported value is null,
not zero; it cannot pass its supplied budget. The feature IDs remain retained
geometry/local-model requirements. This is not complete engineering acceptance
of the arm or permission to remove the attachment/shoulder/load interface.

## Independent derivation

For x in metres, the right-side bending moment polynomials are:

| Interval | M(x), N·m | V(x), N |
|---|---|---|
| 0–0.1 | 60.4-108x | 108 |
| 0.1–0.3 | 61-120x+60x² | 120-120x |
| 0.3–0.4 | 73-160x+60x² | 160-120x |
| 0.4–0.5 | 65-160x+60x² | 160-120x |

The independent oracle integrates (0.5-x)M/(EI) and V/(kappa GA) for tip motion,
M/(EI) for rotation and M²/(2EI)+V²/(2kappa GA) for energy, using exact Python
`Fraction` arithmetic. It adds the two root spring contributions and calculates
the x=0.25 nominal stress separately. The production method instead constructs
local load polynomials, integrates response recurrence and uses a three-point
Gaussian rule exact for the polynomial energy integrands. This gives two
separate computational paths to the expected values.

## Negative and competing cases

| Exact change to the request | Expected behavior and engineering reason |
|---|---|
| Replace proposal with one 50×24 mm section over the full 500 mm | Reject under the original multi-QoI budgets even though mass remains 1.62 kg. Preserving volume does not preserve the stiffness distribution or rotation. |
| Swap width/depth in each proposed segment | Reject; mass is unchanged but bending-axis inertia and stresses change. |
| Copy original segments into proposal; set tip displacement allowance to 1e-10 m and relative=0 | Select Timoshenko. Geometry is identical but omitted shear exceeds that QoI budget. |
| Lower allowable section rotation to 1e-5 rad | Reject the reduced-model use under the declared regime criterion, even if geometry differences are small. |
| Request only mass or local peak stress | Reject an uninformative mechanical choice; no stiffness-sensitive response has been assessed. |
| Add a gap to the segment partition, use force unit Pa, use a boolean modulus or add an unrecognized torque field | Reject invalid/unsupported data with a specific error, not a generic completed plan. |

The core tests also use a mass-equivalent 24 mm uniform approximation to the
stepped beam under a 100 N tip load with a 1% displacement-only budget. Its
Timoshenko discrepancy is 0.978593%; its EB discrepancy looks smaller because
the errors partly cancel. The additive geometry-plus-shear accounting correctly
retains Timoshenko. This is a focused demonstration of why an apparently closer
single number must not hide two opposing modeling approximations.

Native follow-up uses the [release-specific handoff](siemens-2606.md), including
section orientation, actual support behavior, solver/discretization parity
and a separate local model for the root-fillet stress.
