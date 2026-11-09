# Assembly dynamics with physical mass, interfaces and complex response

## Contents

1. Model and state evidence
2. Coupled assembly equations
3. Modal and harmonic interpretation
4. Worked three-component assembly
5. Transfer, specialized dynamics and native readback

## Model and state evidence

Obtain the component/occurrence hierarchy, exclusive masses, center inertias,
coordinate transforms, mount locations and directional stiffnesses. Preserve
the operating state: support/contact changes and thermal prestress can change
the tangent operator. A modal result from the cold model is not automatically
the modal basis of a hot, partly separated assembly. The implemented rigid
assembly reference uses constant bilateral mount stiffness; it identifies the
need for another model but does not invent prestressed flexible modes.

Check inertia beyond positive diagonal values. In its principal axes a physical
three-dimensional mass distribution satisfies each inertia triangle inequality,
such as `I3 <= I1 + I2`, as well as nonnegative inertia. The example `(1,1,3)`
kg m² is positive definite but physically unrealizable and is rejected. Distinguish
the tensor's signed off-diagonal entries from a solver card's products of inertia.
The fetched Nastran 2606 CONM2 page states that its off-diagonal negative signs
are supplied by the solver; it also documents solution-dependent restrictions.

## Coupled assembly equations

Use generalized coordinates `q=[ux,uy,uz,theta_x,theta_y,theta_z]`. At mount i,
`u_i = B_i q`, where `B_i=[I,-skew(r_i)]`. If R maps local mount axes into
assembly axes, `A_i=R_i^T B_i`. Assemble:

```
K = sum A_i^T diag(k_i) A_i
f_thermal = sum A_i^T diag(k_i) d_i
K q = f_external + f_thermal
```

Here d_i is the local free-growth vector, not a prescribed rigid-body motion.
The restoring force on the body is `-R_i diag(k_i)(A_i q-d_i)`. Compute force
and moment equilibrium from those individual reactions independently of the
linear equation residual.

With total mass m, center c and inertia about the chosen origin I_O:

```
M = [[m I,         -m skew(c)],
     [m skew(c),    I_O      ]]
```

Changing reference origin changes the translation/rotation coupling and the
load moments together. Discarding the off-diagonal blocks while preserving m
is a different physical system. To avoid comparing unlike units in a numerical
norm, use a declared characteristic length ell and the congruence
`q=T q_scaled`, `T=diag(1,1,1,1/ell,1/ell,1/ell)`. The scale affects conditioning,
not the physical result; source tests vary it over three orders of magnitude.

## Modal and harmonic interpretation

Solve `K phi=lambda M phi`, with `f=sqrt(lambda)/(2 pi)`, through a mass
Cholesky transformation and a bounded Jacobi eigensolver. Verify each mode with
the action residual `||K phi-lambda M phi||/(||K phi||+lambda||M phi||)` in the
scaled coordinates. Preserve eigenvectors, mass normalization and the complete
six-mode basis. A supported body needs six restrained rigid-body coordinates;
a free mechanism is a model finding, not a small positive frequency to invent.

For the `exp(i omega t)` convention, harmonic response satisfies
`(K-omega² M+i omega C) qhat=fhat`. The source implementation uses explicit
Rayleigh damping `C=alpha M+beta K`, so modal damping varies as
`zeta_i=alpha/(2 omega_i)+beta omega_i/2`. Do not describe this as a uniform
damping ratio over a wide band. The reported complex response retains phase
and amplitude; a real-only magnitude cannot reconstruct interface work or
multi-input interference. Near-singular dynamic stiffness is rejected rather
than silently regularized.

Bind harmonic perturbations to an explicit `about_step_id`. The model screens
the static rotation norm plus the norm of harmonic component amplitudes against
0.05 rad. This conservative bound can reject a case without asserting that it
is the exact phase-dependent peak. A large harmonic response cannot bypass the
small-rotation assumption merely because the static load was small.

## Worked three-component assembly

Run `python -m fea_agent run-case examples/engineering_v2/assembly_case.json`.
The manufactured model contains a 90 kg housing, 25 kg gearbox and 3 kg nested
accessory, with distinct local frames and four anisotropic tilted mounts.
It derives a coupled mass matrix from the hierarchy instead of accepting an
already diagonal modal matrix. The six frequencies are approximately:

`46.038953, 46.871132, 81.924452, 99.940607, 137.154560, 148.704339 Hz`.

Cold, hot and hot-limit source states are solved in order. Their force and
moment residuals are below 1e-8 in their respective SI units. Heating reverses
the local axial reaction of M1. The case runner identifies this changed load
path and requests proof of a tensile attachment; a compression-only interface
would need a different active set and different modes. It does not equate
small equilibrium residual with a valid support assumption.

Independent holdouts use a symmetric four-mount closed-form six-mode system,
global coordinate rotation, origin translation and characteristic-length
changes. The realistic case has off-diagonal mass/inertia and stiffness coupling;
those invariance tests would fail if the code dropped a moment arm or composed
the hierarchy in the wrong order.

## Transfer, specialized dynamics and native readback

Use the same kinematic interpolation and its transpose for displacement and
load transfer: `u_boundary=B q`, `Q=B^T f`. Matching resultant force without
moment or virtual work is insufficient. For GFEM/DFEM, compare both transfer
work and the boundary's ability to reproduce the relevant deformation modes;
a rigid six-DOF transfer is not a flexible submodel interface.

Read [specialized dynamic methods](advanced-dynamics.md) for cyclic phase,
random-response coherence, rotor gyroscopy, aeroelastic damping and acoustic
interfaces. Those methods have explicit gaps; this six-DOF reference does not
silently become any of those solvers. The legacy SOL103 checker accepts only
pure translational supplied matrices; use the assembly implementation for this
mixed-coordinate reference instead of relabeling rotations as translations.

Use the documented result-access path in the
vendor workflow (source: fea_expert_agent_plugin/docs/engineering/vendor-api-workflows.md).
Map entity labels to result indices, preserve parent element for element-nodal
data, select the actual solution/loadcase/iteration and retain units and frame.
Borrowed result handles are not owned builders. Do not destroy an object whose
ownership or deletion API is unresolved. Real solver/model correlation requires
qualified Runtime readback and remains separate from these source computations.

## Frequency-resolution review

A converged complex linear solve at requested frequencies is not a response
envelope. Inspect `frequency_sampling_review`: the source tool marks modes in
the requested range with no sample inside the approximate isolated-mode
half-power half-width, zeta times natural frequency. Refine locally and track
phase and peak displacement/rotation as the frequency spacing decreases. The
criterion is a sampling warning, not a guarantee that every mode is excited or
that a sampled peak is exact. Closely spaced modes, cancellation and damping
sensitivity require the full complex response. In the mounted example, a local
46.878 Hz response is more than seven times the maximum at the original sparse
points. Do not size a mount or judge clearance from that sparse maximum.

## State-bound support loads versus an independent transfer pattern

Each computed static state now emits `support_submodel_transfer`: source
request digest, model/owner/revision/frame, step, mount IDs, application points
and forces **on the support**. These are the negatives of mount reactions on
the assembly. Their generalized resultant agrees with the assembly's applied
load, and the same motion operator preserves virtual work. A destination mesh
remains unbound until a qualified mapping is supplied; do not apply point
forces to arbitrary nearby nodes.

The optional two-point `interface_check` is an independent declared load
pattern, not an authenticated result from a service step. Its report says so.
The rigid-motion operator for two collinear points has rank five: twist about
the line cannot be observed and its conjugate torque cannot be represented.
A passing work/resultant check for this particular pattern does not establish
general six-degree-of-freedom transfer. Use noncollinear support geometry or
an explicitly qualified restricted load subspace, and retain target mesh and
state identity.
