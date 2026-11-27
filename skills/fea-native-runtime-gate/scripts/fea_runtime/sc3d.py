"""Run the existing supported NXOpen import, persistence and export path in isolation."""

from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess

from fea_controller import digest, now, save
from .artifacts import file_identity
from .contracts import Blocked, fields, fresh_at, load_json, number, relative, scoped_path, sha, stamp, text


ACTIONS = {
    "sc3d.model.import": "import",
    "sc3d.model.read_saved": "read",
    "sc3d.model.persist": "export",
    "sc3d.bc.scale_nodal_force": "scale-force",
    "sc3d.mesh.refine_region": "refine-region",
}


MUTATION_READBACK = {"scale-force": "inspect-force", "refine-region": "inspect-region"}


def _native_predicates(operation):
    if operation["baseline"].get("native_state") != {"op": "exact", "value": "UNLAUNCHED"}:
        raise ValueError("batch effects require an unlaunched baseline")
    if operation["expected"].get("native_state") != {"op": "exact", "value": "VERIFIED"}:
        raise ValueError("batch effects require a verified native-state witness")


def _part_path(value, suffix):
    if not relative(value).lower().endswith(suffix):
        raise ValueError(f"exact owned {suffix} path required")


def _validate_mutation(operation, action):
    args = operation["args"]
    if action == "scale-force":
        fields(args, ("sim", "fem", "fem_sha256", "launcher_sha256", "load"))
        _part_path(args["sim"], ".sim")
        sha(args["fem_sha256"])
        spec = args["load"]
        fields(spec, ("solution", "step", "name", "grid_labels", "scale_before", "scale_after"))
        for key in ("solution", "step", "name"):
            text(spec[key])
        labels = spec["grid_labels"]
        if (type(labels) is not list or not 1 <= len(labels) <= 10000
                or any(type(label) is not int or label <= 0 for label in labels)
                or labels != sorted(set(labels))):
            raise ValueError("grid labels must be sorted, unique positive native IDs")
        before, after = (number(spec[key]) for key in ("scale_before", "scale_after"))
        if not 0 < before <= 1e6 or not 0 < after <= 1e6 or before == after:
            raise ValueError("force edit requires distinct positive native scales")
        target, schema = args["sim"], "sc3d.sim"
    else:
        fields(args, ("fem", "cad", "cad_sha256", "launcher_sha256", "region"))
        _part_path(args["cad"], ".prt")
        sha(args["cad_sha256"])
        spec = args["region"]
        fields(spec, ("cad_body", "cad_face", "guard_body", "face_vertices_mm", "size_mm"))
        for key in ("cad_body", "cad_face", "guard_body"):
            text(spec[key])
        if spec["cad_body"] == spec["guard_body"]:
            raise ValueError("guard body and target CAD body must differ")
        if not 0 < number(spec["size_mm"]) <= 1e6:
            raise ValueError("face size must be positive and in millimeters")
        points = spec["face_vertices_mm"]
        if (type(points) is not list or not 3 <= len(points) <= 256
                or any(type(point) is not list or len(point) != 3 for point in points)):
            raise ValueError("at least three measured CAD vertices in millimeters are required")
        for point in points:
            for coordinate in point:
                number(coordinate)
        if points != [list(point) for point in sorted({tuple(point) for point in points})]:
            raise ValueError("measured CAD vertices must be sorted and unique")
        target, schema = args["fem"], "sc3d.fem"
    _part_path(args["fem"], ".fem")
    sha(args["launcher_sha256"])
    if (operation["target"]["path"] != target or operation["target"]["schema"] != schema):
        raise ValueError("mutation target does not identify the requested editable part and schema")
    _native_predicates(operation)


def validate_batch(operation):
    args = operation["args"]
    action = ACTIONS[operation["capability"]]
    if action in MUTATION_READBACK:
        _validate_mutation(operation, action)
        return
    required = ("sim", "fem", "launcher_sha256")
    optional = ()
    if action == "import":
        required += ("deck", "input_scope", "unit_system", "sequence")
        optional = ("rename", "rename_step")
    elif action == "export":
        required += ("export", "solution", "sequence")
    fields(args, required, optional)
    sha(args["launcher_sha256"])
    if action != "read" and (type(args["sequence"]) is not int or args["sequence"] not in {101, 103}):
        raise Blocked("isolated model operation requires the supported SOL 101 or SOL 103 family")
    if not relative(args["sim"]).lower().endswith(".sim") or not relative(args["fem"]).lower().endswith(".fem"):
        raise ValueError("exact owned SIM and FEM paths are required")
    if Path(args["sim"]).stem.casefold() == Path(args["fem"]).stem.casefold():
        raise ValueError("FEM and SIM must have distinct base names")
    path = args["sim"]
    if action == "import":
        path = relative(args["deck"])
        if args["input_scope"] != ".":
            relative(args["input_scope"])
        if args["unit_system"] != "N-m-kg-s":
            raise Blocked("the qualified translator import profile uses N-m-kg-s")
    if path != operation["target"]["path"]:
        raise ValueError("isolated operation requires a bound input file")
    if action == "export":
        output = relative(args["export"])
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", args["solution"]):
            raise ValueError("export requires a safe, exact, named solution")
        sim = Path(args["sim"])
        expected = (sim.parent / (sim.stem + "-" + args["solution"] + ".dat").lower()).as_posix()
        if output.casefold() != expected.casefold():
            raise ValueError("export path does not match the native default beside the owned SIM")
    rename = args.get("rename")
    if rename is not None and (type(rename) is not list or len(rename) != 2 or rename[0] == rename[1]
                               or not all(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", name)
                                          for name in rename)):
        raise ValueError("rename requires distinct exact solution names")
    rename_step = args.get("rename_step")
    if rename_step is not None and (type(rename_step) is not list or len(rename_step) != 3
                                    or not all(isinstance(name, str)
                                               and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _-]{0,79}", name)
                                               for name in rename_step)
                                    or rename_step[1].casefold() == rename_step[2].casefold()):
        raise ValueError("step rename requires exact solution and distinct step names")
    if action != "read":
        _native_predicates(operation)


def _invoke(exe, folder, label, request, seconds):
    receipt = folder / (label + "-receipt.json")
    envelope = folder / (label + "-request.json")
    save(envelope, {**request, "receipt": str(receipt)})
    env = {**os.environ, "FEA_RUNTIME_JOURNAL_REQUEST": str(envelope),
           "UGII_BASE_DIR": str(exe.parent.parent)}
    with (folder / (label + ".log")).open("xb") as stream:
        process = subprocess.Popen([str(exe), str(Path(__file__).with_name("sc3d_journal.py"))],
                                   cwd=folder, env=env, stdin=subprocess.DEVNULL, stdout=stream,
                                   stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    save(folder / (label + "-launch.json"), {"pid": process.pid, "launched_at": now()})
    try:
        exit_code = process.wait(timeout=min(120, seconds))
    except subprocess.TimeoutExpired as exc:
        raise Blocked("isolated SC3D launch is still unsettled after its deadline") from exc
    if exit_code != 0 or not receipt.exists():
        raise Blocked(f"SC3D journal did not produce native receipt; inspect {label}.log")
    return load_json(receipt)


def _owned(controller, operation):
    args = operation["args"]
    action = ACTIONS[operation["capability"]]
    output = operation["output_scope"]
    scope = controller.root if output == "." else scoped_path(controller.root, output)
    mapping = {}
    for key in ("sim", "fem", "cad", "deck", "export"):
        if key in args:
            fresh = action == "import" and key in {"sim", "fem"} or key == "export"
            path = scoped_path(controller.root, args[key], exists=not fresh)
            if not path.parent.is_dir() or (key != "deck" and not path.is_relative_to(scope)):
                raise ValueError("native file is outside its owned output scope")
            if fresh and path.exists():
                raise ValueError("native output already exists")
            mapping[key] = str(path)
    if action in MUTATION_READBACK:
        guard = "fem" if action == "scale-force" else "cad"
        if file_identity(Path(mapping[guard]))["sha256"] != args[guard + "_sha256"]:
            raise ValueError("native dependency differs from its admitted digest")
        target = operation["target"]["path"]
        table = controller.snapshot().get("runtime_v1", {})
        if any(item["path"] == target for item in table.get("artifacts", {}).values()):
            raise ValueError("the editable path is already retained as an immutable artifact")
    if action == "import":
        from .native import inspect_deck

        deck, _ = inspect_deck(controller.root, args)
        if len(deck.files) != 1 or deck.solution != args["sequence"]:
            raise Blocked("isolated NXOpen import currently accepts a single closed native input deck")
    return scope, mapping


def _observe_mutation(controller, operation, names, exe, folder, native, response, recorded, revision, before):
    action = native["action"]
    args = operation["args"]
    changed, guard = ("sim", "fem") if action == "scale-force" else ("fem", "cad")
    persisted = {key: file_identity(Path(native[key])) for key in (changed, guard)}
    if persisted[changed] == before[changed] or persisted[guard] != before[guard]:
        raise ValueError("saved mutation did not change only the owned target file")
    remaining = (stamp(operation["deadline"]) - datetime.now(timezone.utc)).total_seconds()
    if remaining <= 0:
        raise Blocked("deadline elapsed before independent reopen")
    reopen = _invoke(exe, folder, "readback", {**native, "action": MUTATION_READBACK[action]}, remaining)
    if (reopen["scope"] != response["after"]
            or any(file_identity(Path(native[key])) != persisted[key] for key in persisted)):
        raise ValueError("fresh native reopen disagrees with the saved mutation")
    if action == "scale-force" and (reopen["dirty"] or reopen["dependent_fem_dirty"]):
        raise ValueError("solver-backed force mutation did not reopen cleanly")
    if action == "refine-region" and reopen["dependent_cad_dirty"]:
        raise ValueError("CAD dependency unexpectedly became dirty")
    return controller.transition("observe", **names, observation={
        "target": operation["target"], "observed_at": fresh_at(recorded["response_at"]),
        "evidence_ref": "nx-reopen:" + digest({"record": recorded["raw_digest"], "reopen": reopen}),
        "coverage": "COMPLETE", "settled": True,
        "witnesses": {"native_state": "VERIFIED", "before": response["before"],
                      "after": response["after"], "dirty": reopen["dirty"],
                      "reopened_before_inspection_dirty": reopen.get("dirty_on_open", reopen["dirty"]),
                      "result_file": persisted[changed]},
        "artifacts": [{"path": args[changed], "type": "sc3d." + changed,
                       "tool": "run_journal", "build": revision, "coverage": "COMPLETE",
                       "parents": operation.get("input_artifacts", [])}],
    })


def execute_batch(controller, operation, binding, authority, product):
    if os.name != "nt":
        raise Blocked("the isolated SC3D execution profile requires Windows")
    validate_batch(operation)
    exe = Path(product).resolve(strict=True) / "NXBIN/run_journal.exe"
    if not exe.is_file() or file_identity(exe)["sha256"] != operation["args"]["launcher_sha256"]:
        raise Blocked("installed SC3D journal executable differs from the bound artifact")
    revision = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
         "(Get-Item -LiteralPath $env:FEA_RUNTIME_NX_EXE).VersionInfo.ProductVersion"],
        env={**os.environ, "FEA_RUNTIME_NX_EXE": str(exe)}, capture_output=True, check=True, timeout=15,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout.decode().strip()
    if revision != "2612.1700":
        raise Blocked("the isolated SC3D route requires the qualified 2612.1700 product")
    scope, mapping = _owned(controller, operation)
    action = ACTIONS[operation["capability"]]
    prepared = controller.transition("prepare", operation=operation, binding=binding, authority=authority)
    names = {key: operation[key] for key in ("run_id", "operation_id")}
    preflight = {"target": operation["target"], "observed_at": now(),
                 "evidence_ref": "preflight:" + prepared["request_digest"],
                 "witnesses": {"native_state": "UNLAUNCHED"}}
    controller.transition("reserve", **names, binding=binding, authority=authority,
                          request_digest=prepared["request_digest"], preflight=preflight)
    seconds = 120
    if "deadline" in operation:
        seconds = max(0, (stamp(operation["deadline"]) - datetime.now(timezone.utc)).total_seconds())
    args = operation["args"]
    native = {"action": action, **mapping}
    for key in ("rename", "rename_step", "solution", "region", "load"):
        if key in args:
            native[key] = args[key]
    folder = scope / ("nx-" + operation["run_id"] + "-" + operation["operation_id"])
    try:
        folder.mkdir()
        owned_parts = ("cad", "fem") if action == "refine-region" else ("sim", "fem")
        before = {key: file_identity(Path(mapping[key])) for key in owned_parts} if action != "import" else None
        if action in MUTATION_READBACK:
            changed = "fem" if action == "refine-region" else "sim"
            guard = next(key for key in owned_parts if key != changed)
            if (before[changed]["sha256"] != operation["target"]["sha256"]
                    or before[guard]["sha256"] != args[guard + "_sha256"]):
                raise Blocked("owned mutation bytes changed before dispatch")
        response = _invoke(exe, folder, "native", native, seconds)
        recorded = controller.transition("record", **names, raw={"native_response": response})
        if action in MUTATION_READBACK:
            return _observe_mutation(controller, operation, names, exe, folder, native,
                                     response, recorded, revision, before)
        if action == "import":
            if "meter" not in Path(mapping["deck"]).with_suffix(".lis").read_text(
                    encoding="utf-8", errors="replace").lower():
                raise ValueError("import translator unit evidence is unavailable")
            before = {key: file_identity(Path(mapping[key])) for key in ("sim", "fem")}
        observed = _invoke(exe, folder, "readback", {**native, "action": "read"}, seconds)
        if before != {key: file_identity(Path(mapping[key])) for key in ("sim", "fem")}:
            raise ValueError("owned native files changed unexpectedly")
        expected = response["saved"] if action == "import" else response
        if observed != expected or observed["dirty"] != {"sim": False, "fem": False}:
            raise ValueError("fresh native reopen does not agree with the saved state")
        witnesses = {"native_state": "VERIFIED", "inventory": observed,
                     "solution_names": [solution["name"] for solution in observed["solutions"]],
                     "step_names": {solution["name"]: [step["name"] for step in solution["steps"]]
                                    for solution in observed["solutions"]},
                     "dirty": observed["dirty"]}
        artifacts = [{"path": args[key], "type": "sc3d." + key, "tool": "run_journal",
                      "build": revision, "coverage": "COMPLETE", "parents": operation.get("input_artifacts", [])}
                     for key in ("sim", "fem")] if action == "import" else []
        if action == "export":
            from .native import inspect_deck

            deck, _ = inspect_deck(controller.root, {"deck": args["export"], "input_scope": operation["output_scope"]})
            if deck.solution != args["sequence"]:
                raise ValueError("effective exported deck sequence differs")
            witnesses["deck"] = deck.summary()
            artifacts.append({"path": args["export"], "type": "nastran.deck", "tool": "run_journal",
                              "build": revision, "coverage": "COMPLETE", "parents": operation.get("input_artifacts", [])})
        observation = {"target": operation["target"], "observed_at": now(),
                       "evidence_ref": "reopen:" + digest({"observed": observed, "receipt": str(folder)}),
                       "witnesses": witnesses, "coverage": "COMPLETE", "settled": True,
                       "artifacts": artifacts}
        return controller.transition("observe", **names, observation=observation)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        status = controller.snapshot()["runtime_v1"]["operations"][names["run_id"] + "/" + names["operation_id"]]["status"]
        if status == "DISPATCH_RESERVED":
            controller.transition("record", **names, transport_error=str(exc)[:4096])
        raise
