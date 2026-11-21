import NXOpen
import NXOpen.CAE


def main(args):
    parts = NXOpen.Session.GetSession().Parts
    work = parts.BaseWork
    sim = work if isinstance(work, NXOpen.CAE.SimPart) else None
    fem = sim.FemPart if sim else work
    if not sim and not isinstance(fem, NXOpen.CAE.BaseFemPart):
        raise RuntimeError("The live work part is not a SIM, FEM or assembly FEM")

    def part(p):
        return (p.FullPath, str(p.Tag), str(p.PartUnits), p.IsModified) if p else None

    def bcs(container):
        return [(b.Name, str(b.Tag), b.DescriptorName) for b in container.GetBcs()]

    def capture(row, key, read):
        try:
            row[key] = read()
        except Exception as error:
            row.pop(key, None)
            row.setdefault("field_errors", {})[key] = str(error)

    def describe_step(q, index):
        entry = {"index": index}
        try:
            step = q.GetStepByIndex(index)
            entry.update(name=step.Name, tag=str(step.Tag))
        except Exception as error:
            entry["field_errors"] = {"identity": str(error)}
            return entry
        capture(entry, "bcs", lambda: bcs(step))
        return entry

    def describe_solution(q):
        entry = {"name": q.Name, "tag": str(q.Tag)}
        capture(entry, "type", lambda: q.SolutionType)
        capture(entry, "solver", lambda: q.SolverType)
        capture(entry, "bcs", lambda: bcs(q))
        capture(entry, "steps", lambda: [describe_step(q, i) for i in range(q.StepCount)])
        capture(entry, "result_refs", lambda: [
            q.GetResultReferenceByIndex(i).GetResultFile() for i in range(q.ResultReferenceCount)])
        return entry

    result = {"work": part(work), "display": part(parts.BaseDisplay), "fem": part(fem),
              "part_kind": "SIM" if sim else "AFM" if isinstance(fem, NXOpen.CAE.AssyFemPart) else "FEM",
              "solutions": [], "field_errors": {}}

    if sim:
        capture(result, "solutions", lambda: [describe_solution(q) for q in sim.Simulation.Solutions])
        capture(result, "active_solution_tag", lambda: str(sim.Simulation.ActiveSolution.Tag)
                if sim.Simulation.ActiveSolution else None)
    if isinstance(fem, NXOpen.CAE.BaseFemPart):
        capture(result, "associated_cad_path", lambda: fem.FullPathForAssociatedCadPart)
        capture(result, "root_mesh_collectors", lambda: [
            {"name": c.Name, "mesh_count": len(c.GetMeshes())}
            for c in fem.BaseFEModel.MeshManager.GetMeshCollectors()])
        if isinstance(fem, NXOpen.CAE.AssyFemPart):
            capture(result, "assembly_children", lambda: [
                {"identifier": child.JournalIdentifier, "tag": str(child.Tag)}
                for child in fem.BaseFEModel.GetChildren()])
    elif sim:
        result["field_errors"]["fem"] = "The SIM did not resolve a BaseFemPart"
    return result
