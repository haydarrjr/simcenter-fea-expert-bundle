# BatchPost result selection and verification

Resolve the absolute file from task evidence. Ask for its path when ownership or identity remains unresolved. A shared worker retains its opened result and preferences. Reuse the bound result with appropriate ownership, close a task-owned result before changing files when required by the worker, and restore temporary preferences using known prior values. Error `-32001` with “no result is open” requires establishing open state. An empty catalog after open is a reader-coverage observation. Use [artifact forensics](../../fea-artifact-forensics/SKILL.md) to reconcile exact job identity and choose a suitable function, matrix or other result reader. Use the original F06 or authorized diagnostic tools for solver status.

## Multiple selections

Compatible selections expand into combinations. Two compatible loadcases and three cameras can yield six combinations for one result/iteration. Availability and filtering can change that count. Each output target applies to the selected scope. SCE can consolidate results, and CSV grouping depends on preferences. Inspect actual paths and content to establish file count and mapping. Start with an explicit small selection before expanding.

## Modal exports on 2612

Use explicit iteration IDs from `list` because range selection did not preserve requested coverage on the observed worker. For a missing or mixed export, try one target and component per call. Inspect actual CSV column labels because `Magnitude` included XYZ in the observed output. Compare unique state IDs with the exact requested set and check for duplicate, missing and extra state groups. Match frequencies to the signed roots in F06.

Use [verify_modal_csv.py](../scripts/verify_modal_csv.py) for the observed English layout with `Load Case N:Mode M` headings. Verify the column-to-state mapping independently for other layouts. For an undeformed mesh image use a reader-verified post template with mesh displayed and deformation disabled. Assess requested orientation, framing, model visibility and legend in the image.
