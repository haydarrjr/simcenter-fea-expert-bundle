# Equivalent modal damping

Identify whether the task needs damping from measured response, damping projected from a physical FEM, or a specified modal damping law. For measured data, fit a model compatible with the excitation, frequency band and modal separation. Use a decay fit only where the decay can reasonably be attributed to the intended mode. Report uncertainty and validate a reconstructed complex FRF against held-out data.

For real modes `φᵢ`, project the viscous matrix `B` and structural loss matrix `K₄` onto the same modal basis. With diagonal terms `bᵢᵢ`, `k₄,ᵢᵢ`, modal mass `mᵢᵢ` and stiffness `kᵢᵢ`, compare viscous critical ratio `bᵢᵢ/(2mᵢᵢωᵢ)` and structural loss factor `k₄,ᵢᵢ/kᵢᵢ`. Confirm the solver and mode set's reported damping type before converting. Review rigid-root cutoff and quantify the effect of neglected off-diagonal coupling on FRF near the governing band.

For a supported Simcenter Nastran modal workflow, check effective `MDLDAMP`, `KDAMP` and relevant rigid-body limits on the exact solution. Verify property assignment and damping dimensions on the FEM, requests in the deck, tables in solver results, and then mode identity and transferred values in the mode set. Distinguish a blank/unsupported output from measured zero damping. Reconcile modes by [modal correlation](../../fea-modal-correlation/SKILL.md). Preserve solver and measured damping separately when they describe different operating states.

[Mode set theory and damping](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1899327?audience=external) · [Viscous and structural damping values](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1875000?audience=external)
