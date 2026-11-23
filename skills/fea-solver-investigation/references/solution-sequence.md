# Solution Sequence

Use the official Siemens profiles for live setup, deck export and result
reads. Follow the batch stages for a qualified Simcenter Nastran deck.
Use the linked native method for in-session evaluations. Qualify model
persistence, solver execution and result recovery independently.

## 1. Bind the target

For live work, check release, exact SIM/FEM paths, work and display roles,
and existing solutions. Use an authorized working copy and preserve its
original solutions and artifacts. For CAE journals, resolve the work part
through `Session.GetSession().Parts.BaseWork` and confirm the owning FEM.
For deck-only work, bind the exact input, solver release and all dependencies.

## 2. Configure the requested solution

Choose by physical state, excitation and requested output. Then verify the
effective solution and subcase before creating, editing or running it.

| Requested analysis | Route and setup reference | Verify before submission or evaluation |
| --- | --- | --- |
| Linear structural statics | **SOL 101** · [Setup](../../fea-linear-static/references/sol101.md) · [CAD-associative updates](../../simcenter-parametric-sol101/SKILL.md) | Linear assumptions, effective load and restraint sets, case independence and requested displacement, reaction or stress recovery |
| Unloaded, unprestressed free-free normal modes | **SOL 103** · [Free-free setup](../../fea-dynamics/references/sol103-free-free.md) | No external grounding, intentional internal connectivity, mass, extraction range or count and mode-shape output |
| Supported normal modes | **SOL 103** · [Modal setup and Lanczos](../../designcenter-open-journal-authoring/references/cae-2612.md) · [Effective deck checks](../../simcenter-nastran/references/deck-and-solutions.md) | Intended support DOFs and couplings, effective `SPC`/`MPC`, mass, `METHOD`/`EIGRL` and real mode-shape recovery. For a prestressed basis, qualify the operating state and supported prestress setup for the installed release |
| Linearized buckling about a reference load | **SOL 105** · [Preload and eigenfactor checks](../../fea-results-interpretation/references/sol103-sol105-quant.md#sol105-inputs-and-checks) | Reference load and preload state, supports, requested eigenpairs and load-factor sign |
| Nonlinear statics with applicable element, material and output support | **SOL 106** · [Nonlinear setup and I/O](../../simcenter-nastran/references/nonlinear-static-io.md) · [Load path](../../fea-multistep-nonlinear/references/open-solver-workflows.md) | Selected `NLPARM`, load increments, material law and requested nonlinear outputs |
| Staged nonlinear analysis with preload or contact | **SOL 401** · [Nonlinear setup and I/O](../../simcenter-nastran/references/nonlinear-static-io.md) · [Contact convergence](../../fea-connector-contact/references/contact-convergence.md) | Effective step controls and inherited state, contact and bolt definitions where applicable, and requested increment, contact and preload outputs |
| Nonlinear kinematics, staged contact or explicit subcase restoration | **SOL 402** · [Nonlinear setup and I/O](../../simcenter-nastran/references/nonlinear-static-io.md) · [Restart and finite kinematics](../../fea-multistep-nonlinear/references/restart-and-finite-kinematics.md) | Effective step controls, geometry and strain options, contact state and restart source where applicable, plus result format and requested fields |
| Deterministic direct harmonic response or complex FRF | **SOL 108** · [Forced response](../../fea-dynamics/references/forced-response.md) | Input/response DOFs, load or enforced motion, damping, frequency grid, complex quantity and phase convention |
| Deterministic modal harmonic response or complex FRF | **SOL 111** · [Forced response](../../fea-dynamics/references/forced-response.md) | Modal basis, damping, frequency coverage and complex magnitude/phase recovery for the selected excitation and response |
| Stationary random response, PSD/CSD, RMS or crossing rates | **SOL 111** · [Random response setup](../../fea-random-response/references/nastran-random-response.md) | Excitation subcases, `RANDOM`, `RANDPS`, `TABRND1`, spectra and units. Request the random output associated with the intended state and quantity |
| External superelement generation | **Qualified generation sequence** · [External superelements](../../fea-model-preparation/references/external-superelements.md) | Reduction basis, retained interface DOFs and recovery, `EXTSEOUT`, and matrix and connection-deck outputs |
| Residual assembly with an external superelement | **Qualified assembly sequence** · [External superelements](../../fea-model-preparation/references/external-superelements.md) | Interface mapping, `ASSIGN` file units and the exact matrix and connection deck from the generation job. Request assembly field results |
| Aeroelastic static trim and load extraction | **SOL 144** · [Airframe model hierarchy and solver cards](../../simcenter-airframe-structural-verification/references/airframe-model-hierarchy-and-cards.md) | Trim condition, structural/aerodynamic correspondence, effective loads, requested recovery and equilibrium |
| Signed transient response | **Applicable transient sequence** · [Transient field histories](../../fea-dynamics/references/transient-field-history.md) | Physical time grid, initial conditions, loading and damping history, and saved recovery intervals |
| Base-excitation peaks or shock response spectrum | **Native Response Dynamics or documented solver spectrum route** · [Response spectra](../../fea-dynamics/references/response-spectrum.md) | Spectrum quantity and damping, modal basis, enforced DOFs, event or solver settings, and peak recovery |
| Mode-set or FRF-set response, modal damping, or NVH source/path analysis | **Method-specific native or data workflow** · [Component representations](../../fea-model-preparation/references/component-representations.md) · [Dynamics routing](../../fea-sc3d-tool-routing/references/dynamics-routing.md) | Match the basis or existing input data to the requested response or NVH quantity. Use the method's own evaluation and result checks |

Compare SOL 106, 401 and 402 against the installed release's supported elements,
materials, contact treatment and step dependencies before choosing a nonlinear
sequence. Use [static structural routing](../../fea-sc3d-tool-routing/references/static-routing.md)
for thermal loads, instability or postbuckling. Use
[specialized dynamics](../../fea-dynamics/references/advanced-dynamics.md)
for cyclic, rotating, shock-design, flutter or acoustic methods. Check solver
or native evaluation capability for the selected release.

Set output requests for the selected route. Verify the native solution and step
membership before export, or qualify the effective setup directly from the
deck for deck-only work.

## 3. Export and qualify the exact deck

For qualified NXOpen exports, use the [export-only operation](../../designcenter-open-journal-authoring/references/cae-2612.md)
with `SolveOption.WriteSolverInputFile` and the [runtime gate](../../fea-native-runtime-gate/SKILL.md).
Check exporter diagnostics, [effective Case Control](../../simcenter-nastran/SKILL.md),
loads and constraints, units and output requests. Stage the verified deck in
a new task-owned job directory and verify its hash. Preserve and verify the
complete dependency closure, including INCLUDEs, externally assigned files
and restart inputs where applicable. Retain the original and staged inputs.

## 4. Run the installed Siemens batch solver

Use the isolated job directory as the working directory. Resolve the
authorized Siemens product root and the executable for the installed solver.
The qualified Windows 2612 Desktop Bundle path is
`NXNASTRAN\bin\nastranw.exe`. Use invocation options for the exact release,
sequence, license and runtime mode. The observed standalone SOL 103 invocation below requests Solution Monitor.
Use the staged `$deck` path and verify that the monitor setup applies.

```powershell
& (Join-Path $productRoot 'NXNASTRAN\bin\nastranw.exe') $deck 'prog=bundle' 'old=no' 'scratch=yes' 'sys442=2'
```

Before launching, confirm monitor and restart requirements. In particular,
use the [2612 nonlinear runtime diagnostics](../../simcenter-nastran/references/nonlinear-static-io.md#release-specific-diagnostics)
for the observed unmonitored SOL 401 route and omit `sys442=2` there.

The Windows launcher can return early. Confirm fresh job files, native
termination, F06 diagnostics and achievement of the requested states.
Reconcile a pending launch before retrying. Record the invocation and
input/output hashes.

## 5. Select and verify the result format

Choose a format that exposes the required states and fields. Use solver-native
SCD5 where applicable. For supported SOL 101 and SOL 103 results use
`NXBIN\scd5_convert.exe -c=2` with explicit input OP2 and output SCD5 paths.
Disable SOL 101-only performance mode for SOL 103 and validate the conversion
log and result catalog. Retain the original OP2 for fields unavailable in SCD5.
[SCD5 conversion guide](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1968781?audience=external)

Check the [SOL 402 OP2 reader compatibility](../../simcenter-nastran/references/nonlinear-static-io.md#release-specific-diagnostics)
for the installed release. For SOL 111 random output, separately verify
the PSD frequency states and RMS summary using the applicable result reader.
Use [random displacement CSV](../../batchpost-actions/references/random-displacement-csv.md)
for the supported nodal displacement path. For external superelements, bind
post-processing to the assembly field result.

## 6. Read and verify the results

Open the exact job result with [BatchPost](../../batchpost-actions/SKILL.md) or
the reader specified by the native workflow. Resolve actual subcases, states,
result types, units and components before extraction. Use Nastran diagnostics
or scoped original F06/log text for termination, warnings and data outside
the result catalog. Preserve the original job and result artifacts and verify
the requested engineering quantities against the selected method.

## 7. Confirm persistence where requested

Use [native persistence](../../fea-native-runtime-gate/references/native-persistence.md)
for an admitted save and independent reopen, or record operator save evidence
when applicable. Report saved model state, completed job and recovered results
with their own evidence.
