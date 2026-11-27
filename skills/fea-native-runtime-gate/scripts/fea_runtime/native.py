"""Explicit Windows native job dispatch and original-file evidence collection."""

from datetime import datetime, timezone
from functools import lru_cache
import importlib.util
from hashlib import sha256
import os
from pathlib import Path
import re
import subprocess
import sys
from time import monotonic, sleep

from fea_controller import digest, now, save
from .artifacts import file_identity
from .contracts import Blocked, fields, identifier, number, relative, scoped_path, stamp


SEQUENCES = {101, 103, 108, 111, 401}
STATE_PATTERNS = {
    "time": re.compile(r"^\s+TIME\s*=\s*([+\-\d.E]+)\s*$"),
    "frequency": re.compile(r"^\s+FREQUENCY\s*=\s*([+\-\d.E]+)\s*$"),
    "random": re.compile(r"\bRANDOM\s+(\d+)\s*$"),
}
SUBCASE = re.compile(r"\bSUBCASE\s+(\d+)\s*$")
MODES = re.compile(r"^\s+([1-9][0-9]*)\s+([1-9][0-9]*)\s+[+\-\d.E]+(?:\s+[+\-\d.E]+){4}\s*$")
TERMINATED = re.compile(r"^Simcenter Nastran finished\b", re.MULTILINE)
COMPLETE = re.compile(r"^.*\bAnalysis complete\s+(\d+)\s*$", re.MULTILINE)
BUILD = re.compile(r"^Simcenter Nastran (\d+\.\d+) .+ Control File:", re.MULTILINE)


@lru_cache(maxsize=1)
def deck_parser():
    root = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location(
        "_fea_bundle_nastran_deck", root / "simcenter-nastran/scripts/deck.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_local(operation):
    args = operation["args"]
    capability = operation["capability"]
    if capability.startswith("sc3d."):
        from .sc3d import validate_batch

        validate_batch(operation)
        return
    if capability == "nastran.artifact.verify":
        from .engineering.service import validate_request

        validate_request(operation)
        return
    required = ("deck", "input_scope")
    if capability == "nastran.job.submit":
        required += ("job_dir", "sequence", "solution_monitor", "subcases", "states", "outputs",
                     "memory_mb", "unit_system")
    fields(args, required)
    relative(args["deck"])
    if args["input_scope"] != ".":
        relative(args["input_scope"])
    if capability == "nastran.deck.inspect":
        if args["deck"] != operation["target"]["path"]:
            raise ValueError("deck inspection requires the bound file target")
        return
    target = operation["target"]
    if type(args["sequence"]) is not int or args["sequence"] not in SEQUENCES:
        raise Blocked("native solver sequence is outside the implemented dispatch profile")
    if type(args["solution_monitor"]) is not bool or (args["solution_monitor"] and args["sequence"] != 103):
        raise Blocked("solution monitor override is restricted to the supported SOL 103 profile")
    if type(args["memory_mb"]) is not int or not 128 <= args["memory_mb"] <= 4096:
        raise ValueError("memory must be an integer between 128 and 4096 MiB")
    if args["unit_system"] not in {"N-m-kg-s", "N-mm-tonne-s"}:
        raise ValueError("explicit supported coherent deck unit system required")
    job_dir = relative(args["job_dir"])
    identifier(target["job_id"])
    if job_dir != target["job_dir"] or operation["output_scope"] != job_dir.rpartition("/")[0]:
        raise ValueError("job directory must belong directly to the bound output scope")
    subcases = args["subcases"]
    if (type(subcases) is not list or not subcases or len(subcases) > 256
            or any(type(index) is not int or index < 1 for index in subcases)
            or sorted(set(subcases)) != subcases):
        raise ValueError("explicit sorted native subcase IDs are required")
    states = args["states"]
    if type(states) is not list or len(states) > 10000:
        raise ValueError("explicit bounded native state expectations required")
    for state in states:
        fields(state, ("kind", "value"), ("subcase",))
        if state["kind"] not in {"mode", *STATE_PATTERNS}:
            raise ValueError("unsupported native state coordinate")
        number(state["value"])
        if "subcase" in state and state["subcase"] not in subcases:
            raise ValueError("requested state references an unrequested subcase")
    if args["sequence"] != 101 and not states:
        raise ValueError("modal, nonlinear and frequency jobs need explicit state expectations")
    if args["outputs"] != ["op2"]:
        raise Blocked("the current native job profile requires an OP2 output")
    if (operation["baseline"].get("job_state") != {"op": "exact", "value": "UNLAUNCHED"}
            or operation["expected"].get("job_state") != {"op": "exact", "value": "COMPLETED"}):
        raise ValueError("solver job witnesses must bind the unlaunched and completed states")


def inspect_deck(root, args):
    entry = scoped_path(root, args["deck"])
    scope = root if args["input_scope"] == "." else scoped_path(root, args["input_scope"])
    return deck_parser().read_deck(entry, root=scope), scope


def solver_program(product):
    if os.name != "nt":
        raise Blocked("this native solver dispatch profile requires Windows")
    product = Path(product).resolve(strict=True)
    path = product / "NXNASTRAN/bin/nastranw.exe"
    if not path.is_file():
        raise Blocked("installed Siemens Nastran launcher is unavailable")
    return path


def _prespawn(controller, request, product):
    args, target = request["args"], request["target"]
    exe = solver_program(product)
    if file_identity(exe)["sha256"] != target["executable_sha256"]:
        raise Blocked("installed solver launcher has changed")
    if target["release"] != "2612.0000":
        raise Blocked("this native solver dispatch profile requires observed 2612.0000")
    deck, scope = inspect_deck(controller.root, args)
    if digest(deck.files) != target["deck_digest"] or deck.solution != args["sequence"]:
        raise ValueError("deck closure or effective solution differs from the bound target")
    if sorted(deck.subcases) != args["subcases"]:
        raise ValueError("job subcase requirements differ from the effective deck")
    blocked_cards = {"DMIG", "DMI", "DMIJ", "DMIJI", "DMIK", "DTI", "RESTART", "DEQATN", "MDLPRM"}
    if blocked_cards & {card.name for card in deck.cards}:
        raise Blocked("external matrix, restart or advanced parameter behavior is outside this job profile")
    out = scoped_path(controller.root, args["job_dir"], exists=False)
    if out.exists() or not out.parent.is_dir():
        raise Blocked("native job directory must be new and inside its existing task-owned scope")
    return exe, deck, scope, out


def submit(controller, request, binding, authority, product):
    exe, deck, scope, out = _prespawn(controller, request, product)
    verified = controller.transition("prepare", operation=request, binding=binding, authority=authority)
    names = {"run_id": request["run_id"], "operation_id": request["operation_id"]}
    preflight = {"target": request["target"], "witnesses": {"job_state": "UNLAUNCHED"},
                 "observed_at": now(), "evidence_ref": "preflight:" + verified["request_digest"]}
    controller.transition("reserve", **names, binding=binding, authority=authority,
                          request_digest=verified["request_digest"], preflight=preflight)
    try:
        out.mkdir()
        written = []
        for name, metadata in deck.files.items():
            path = scoped_path(scope, name)
            dest = scoped_path(out, name, exists=False)
            dest.parent.mkdir(parents=True, exist_ok=True)
            data = path.read_bytes()
            if sha256(data).hexdigest() != metadata["sha256"]:
                raise ValueError("source deck changed during staging")
            with dest.open("xb") as stream:
                stream.write(data)
            written.append(name)
        entry = scoped_path(out, deck.entry)
        staged = deck_parser().read_deck(entry, root=out, expected_hashes={name: meta["sha256"] for name, meta in deck.files.items()})
        if staged.files != deck.files:
            raise ValueError("staged closure differs from the approved effective deck")
        scratch = out / "scratch"
        scratch.mkdir()
        # Resolve only scoped inputs and fixed Siemens switches. The installed rcf and
        # effective run controls remain visible in the retained original solver log.
        args = request["args"]
        argv = [str(exe), entry.relative_to(out).as_posix(), "prog=bundle", "old=no", "scratch=yes",
                f"memory={args['memory_mb']}mb", "sdir=scratch"]
        if args["solution_monitor"]:
            argv.append("sys442=2")
        started = now()
        invocation = {"started_at": started, "output_stem": entry.stem, "argv": argv,
                      "inputs": deck.files, "entry": deck.entry, "unit_system": args["unit_system"],
                      "executable": file_identity(exe), "dependency_count": len(written)}
        save(out / "invocation.json", invocation)
        with (out / "launcher.txt").open("xb") as stream:
            process = subprocess.Popen(argv, cwd=out, stdin=subprocess.DEVNULL, stdout=stream,
                                       stderr=subprocess.STDOUT,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        launcher = {"pid": process.pid, "observed_at": now(), "launched_by_this_process": True}
        save(out / "launcher.json", launcher)
        remaining = max(0, (stamp(request["deadline"]) - datetime.now(timezone.utc)).total_seconds())
        end = monotonic() + min(remaining, 120)
        try:
            launcher["returncode"] = process.wait(timeout=min(remaining, 30))
        except subprocess.TimeoutExpired:
            launcher["returncode"] = None
        save(out / "launcher.json", launcher)
        raw = job_evidence(out, request)
        while raw["job_state"] == "PENDING" and monotonic() < end:
            sleep(min(.25, max(0, end - monotonic())))
            raw = job_evidence(out, request)
        controller.transition("record", **names, raw=raw)
        return reconcile_job(controller, **names)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        current = controller.snapshot()["runtime_v1"]["operations"][names["run_id"] + "/" + names["operation_id"]]
        if current["status"] == "DISPATCH_RESERVED":
            controller.transition("record", **names, transport_error=str(exc)[:4096])
        raise


def _diagnostic(path):
    with path.open("rb") as stream:
        data = stream.read(64 * 1024 * 1024 + 1)
    if len(data) > 64 * 1024 * 1024:
        raise Blocked("diagnostic exceeds the bounded solver text reader")
    return data.decode("utf-8", errors="replace")


def states_seen(f06):
    subcase = None
    modes = False
    seen = set()
    cases = set()
    for line in f06.splitlines():
        if line.startswith("1"):
            modes = False
        if match := SUBCASE.search(line):
            subcase = int(match[1])
            cases.add(subcase)
        if "R E A L   E I G E N V A L U E S" in line:
            modes = True
        if modes and (match := MODES.match(line)):
            seen.add(("mode", int(match[1]), subcase))
        for kind, pattern in STATE_PATTERNS.items():
            if match := pattern.search(line):
                seen.add((kind, float(match[1]), subcase))
    return cases, seen


def job_evidence(out, request):
    from .contracts import load_json

    invocation = load_json(out / "invocation.json")
    for name, metadata in invocation["inputs"].items():
        if file_identity(scoped_path(out, name))["sha256"] != metadata["sha256"]:
            raise ValueError("submitted deck and dependency bytes no longer match")
    stem = invocation["output_stem"]
    if stem != Path(invocation["entry"]).stem:
        raise ValueError("invalid invocation output stem")
    found = {}
    for ext in ("log", "f04", "f06", "op2"):
        path = scoped_path(out, f"{stem}.{ext}", exists=False)
        if path.is_file() and path.stat().st_size:
            # A job directory was created exclusively immediately before this launch.
            if path.stat().st_mtime < stamp(invocation["started_at"]).timestamp() - 2:
                raise ValueError("stale solver output cannot witness this invocation")
            found[ext] = path
    if "log" not in found:
        return {"job_state": "PENDING"}
    log = _diagnostic(found["log"])
    if not TERMINATED.search(log):
        return {"job_state": "PENDING"}
    info = {ext: {"name": path.name, **file_identity(path)} for ext, path in found.items()}
    build = BUILD.search(log)
    result = {"job_state": "FAILED", "artifacts": info, "build": build[1] if build else None}
    license_status = re.search(r"(unable to obtain a license|license checkout failed|all licenses.*in use)", log, re.I)
    if license_status:
        result["diagnostic"] = license_status[0]
        return result
    if (set(found) != {"log", "f04", "f06", "op2"} or COMPLETE.findall(log) != ["0"]
            or result["build"] != request["target"]["release"]):
        result["diagnostic"] = "termination, build or required original outputs did not match"
        return result
    f06 = _diagnostic(found["f06"])
    if "END OF JOB" not in f06 or re.search(r"\b(?:USER|SYSTEM) FATAL(?: MESSAGE)?\b", f06):
        result["diagnostic"] = "F06 termination is missing or reports a fatal message"
        return result
    cases, states = states_seen(f06)
    args = request["args"]
    required = args["states"]
    missing = [state for state in required if not any(
        state["kind"] == kind and state["value"] == value
        and ("subcase" not in state or state["subcase"] == subcase)
        for kind, value, subcase in states)]
    if not set(args["subcases"]) <= cases or missing:
        return {**result, "job_state": "COVERAGE_INCOMPLETE", "observed_subcases": sorted(cases),
                "missing_states": missing}
    return {**result, "job_state": "COMPLETED", "observed_subcases": sorted(cases),
            "matched_states": len(required)}


def reconcile_job(controller, run_id, operation_id):
    names = {"run_id": run_id, "operation_id": operation_id}
    record = controller.snapshot()["runtime_v1"]["operations"][run_id + "/" + operation_id]
    request = record["request"]
    if request["capability"] != "nastran.job.submit" or record["status"] not in {
            "OBSERVATION_REQUIRED", "UNKNOWN", "DISPATCH_RESERVED"}:
        raise ValueError("operation is not a pending native solver job")
    out = scoped_path(controller.root, request["args"]["job_dir"], exists=False)
    if not (out / "invocation.json").is_file():
        raise Blocked("native submission has no recoverable launch evidence")
    result = job_evidence(out, request)
    refs = [{"path": (out / evidence["name"]).relative_to(controller.root).as_posix(),
             "type": "nastran." + kind, "tool": "nastranw", "build": result["build"] or "unverified",
             "coverage": "COMPLETE" if result["job_state"] == "COMPLETED" else "PARTIAL",
             "parents": request.get("input_artifacts", [])} for kind, evidence in result.get("artifacts", {}).items()]
    reference = "job:" + digest({"result": result, "observed_at": now()})
    observation = {"target": request["target"], "observed_at": now(), "evidence_ref": reference,
                   "witnesses": {"job_state": result["job_state"]}, "artifacts": refs,
                   "coverage": "COMPLETE" if result["job_state"] == "COMPLETED" else "PARTIAL",
                   "settled": result["job_state"] != "PENDING"}
    return controller.transition("reconcile", **names, observation=observation)
