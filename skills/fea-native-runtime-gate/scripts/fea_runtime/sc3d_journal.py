"""Internal NXOpen batch journal with a closed set of owned-file operations."""

import json
import os
from pathlib import Path
import re

import NXOpen
import NXOpen.CAE


IMPORT_FLAGS = ("createSolution", "importNonBulkData", "importExecutiveControl", "importCaseControl",
                "importBulkData", "importGrids", "importElements", "importMaterials",
                "importPhysProps", "importLoads", "importConstraints", "importOutputRequests")


def save_part(part):
    result = part.Save(NXOpen.BasePart.SaveComponents.FalseValue,
                       NXOpen.BasePart.CloseAfterSave.FalseValue)
    try:
        if result.NumberUnsavedParts or result.NumberUnsavedObjects:
            raise RuntimeError("NXOpen reported incomplete part persistence")
    finally:
        result.Dispose()


def assert_parts(sim, request):
    if not isinstance(sim, NXOpen.CAE.SimPart) or not sim.FemPart:
        raise RuntimeError("did not resolve a SIM and its linked FEM")
    if Path(sim.FullPath) != Path(request["sim"]) or Path(sim.FemPart.FullPath) != Path(request["fem"]):
        raise RuntimeError("opened part dependencies do not match the exact owned paths")


def inspect_sim(sim):
    fem = sim.FemPart
    collectors = fem.BaseFEModel.MeshManager.GetMeshCollectors()
    return {
        "sim": sim.FullPath, "fem": fem.FullPath,
        "dirty": {"sim": bool(sim.IsModified), "fem": bool(fem.IsModified)},
        "cad": fem.FullPathForAssociatedCadPart,
        "units": str(fem.PartUnits),
        "collectors": [{"name": collector.Name, "meshes": [mesh.Name for mesh in collector.GetMeshes()]}
                       for collector in collectors],
        "solutions": [
            {"name": solution.Name, "type": solution.SolutionType,
             "steps": [{"name": step.Name, "bcs": [bc.DescriptorName for bc in step.GetBcs()]}
                       for step in (solution.GetStepByIndex(i) for i in range(solution.StepCount))],
             "bcs": [bc.DescriptorName for bc in solution.GetBcs()]}
            for solution in sim.Simulation.Solutions
        ],
    }


def import_model(session, request):
    for key in ("fem", "sim"):
        if Path(request[key]).exists():
            raise RuntimeError("native import target already exists")
    options = session.CaeSession.GetDataContainer()
    try:
        for key, argument in (("solverInputFileFullPath", "deck"),
                              ("femFileName", "fem"), ("simFileName", "sim")):
            options.AddString(key, request[argument])
        for key in IMPORT_FLAGS:
            options.AddLogical(key, True)
        sim = session.CaeSession.ImportSimulation("NX NASTRAN", options)
    finally:
        options.Dispose()
    assert_parts(sim, request)
    original = inspect_sim(sim)
    if "rename" in request:
        current, desired = request["rename"]
        solutions = list(sim.Simulation.Solutions)
        exact = [solution for solution in solutions if solution.Name == current]
        if len(exact) != 1 or any(solution.Name.casefold() == desired.casefold() for solution in solutions):
            raise RuntimeError("solution rename target is absent, ambiguous or conflicts")
        exact[0].SetName(desired)
    if "rename_step" in request:
        owner, current, desired = request["rename_step"]
        solutions = [solution for solution in sim.Simulation.Solutions if solution.Name == owner]
        if len(solutions) != 1:
            raise RuntimeError("step mutation requires exact solution ownership")
        solution = solutions[0]
        steps = [solution.GetStepByIndex(index) for index in range(solution.StepCount)]
        matching = [step for step in steps if step.Name == current]
        if len(matching) != 1 or any(step.Name.casefold() == desired.casefold() for step in steps):
            raise RuntimeError("step rename target is absent, ambiguous or conflicts")
        matching[0].SetName(desired)
    save_part(sim.FemPart)
    save_part(sim)
    return {"original": original, "saved": inspect_sim(sim)}


def read_model(session, request):
    sim, status = session.Parts.OpenBaseDisplay(request["sim"])
    try:
        if status.NumberUnloadedParts:
            raise RuntimeError("referenced parts did not all reopen")
    finally:
        status.Dispose()
    assert_parts(sim, request)
    if (session.Parts.BaseDisplay.Tag != sim.Tag or session.Parts.BaseWork.Tag != sim.Tag):
        raise RuntimeError("work/display roles differ from opened SIM")
    before = inspect_sim(sim)
    if request["action"] == "export":
        target = Path(request["export"])
        if target.exists():
            raise RuntimeError("native export target already exists")
        solutions = [item for item in sim.Simulation.Solutions if item.Name == request["solution"]]
        if len(solutions) != 1:
            raise RuntimeError("exact native solution selection required")
        if not re.match(r"^SE(?:STATIC 101|MODES 103)\b", solutions[0].SolutionType):
            raise RuntimeError("unqualified solution family for this owned-file export route")
        solutions[0].Solve(NXOpen.CAE.SimSolution.SolveOption.WriteSolverInputFile,
                           NXOpen.CAE.SimSolution.SetupCheckOption.CompleteCheckAndOutputErrors)
        if not target.is_file() or inspect_sim(sim) != before:
            raise RuntimeError("fresh deck or unchanged native solution signature was not witnessed")
    return before


def main():
    path = Path(os.environ["FEA_RUNTIME_JOURNAL_REQUEST"])
    request = json.loads(path.read_text(encoding="utf-8"))
    session = NXOpen.Session.GetSession()
    if not session.IsBatch or session.Parts.BaseWork or session.Parts.BaseDisplay:
        raise RuntimeError("the native operation requires an isolated empty batch session")
    if request["action"] == "import":
        result = import_model(session, request)
    elif request["action"] in {"read", "export"}:
        result = read_model(session, request)
    else:
        raise RuntimeError("unsupported isolated NXOpen operation")
    with Path(request["receipt"]).open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, allow_nan=False)


if __name__ == "__main__":
    main()
