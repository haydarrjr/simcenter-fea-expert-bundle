import NXOpen
import NXOpen.CAE


def main(args):
    parts = NXOpen.Session.GetSession().Parts
    work = parts.BaseWork
    if not isinstance(work, NXOpen.CAE.SimPart):
        raise RuntimeError("The live work part is not a SIM")

    def part(p):
        return (p.FullPath, str(p.Tag), str(p.PartUnits), p.IsModified) if p else None

    def bcs(container):
        return [(b.Name, str(b.Tag), b.DescriptorName) for b in container.GetBcs()]

    solutions = []
    for q in work.Simulation.Solutions:
        steps = []
        for i in range(q.StepCount):
            step = q.GetStepByIndex(i)
            steps.append({"name": step.Name, "tag": str(step.Tag), "bcs": bcs(step)})
        solutions.append({"name": q.Name, "tag": str(q.Tag), "type": q.SolutionType,
                          "solver": q.SolverType, "bcs": bcs(q), "steps": steps,
                          "result_refs": [q.GetResultReferenceByIndex(i).GetResultFile()
                                          for i in range(q.ResultReferenceCount)]})
    return {"work": part(work), "display": part(parts.BaseDisplay),
            "fem": part(work.FemPart), "solutions": solutions}
