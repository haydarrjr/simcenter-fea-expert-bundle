# NVH transfer path analysis

Define operating state, receiver, source, physical interfaces and desired band. Match load type and transfer function to the formulation, for example interface force with a compatible structural or acoustic transfer. Use independently measured loads or [load identification](nvh-load-identification.md) when needed. Resolve incompatible units, frames, phase and band before combining data.

Compute path contributions `cᵢ(f) = Hᵢ(f)fᵢ(f)` and combine coherent paths as complex values. For correlated stochastic sources retain cross terms in power. Quantify reconstruction error against an independent receiver before ranking paths. Preserve phase cancellation, band weighting, uncertainty or unobserved paths in the report. A ranking depends on the actual receiver, state and metric. Test a synthetic cancellation case and a held-out receiver.

A request for a stored contribution plot starts at its bound datasets and scenario. Use [artifact forensics](../../fea-artifact-forensics/SKILL.md) for source, convention and state. Check the qualified native route separately if authoring or evaluation is requested.

[Simcenter 3D transfer path analysis](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1665256?audience=external)
