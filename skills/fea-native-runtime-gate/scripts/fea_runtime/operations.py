"""Versioned transitions for the existing Controller and its ledger."""

from datetime import datetime, timezone
import hashlib
import os

from fea_controller import PENDING, canonical, digest, now, response_failed
from .artifacts import artifact, file_identity, read_artifact
from .contracts import (CAPABILITIES, Blocked, Denied, MAX_JSON, authorize, fields, identifier, match,
                        satisfies, scoped_path, stamp, target_identity, text, validate, load_json)


def _key(run_id, operation_id):
    return identifier(run_id) + "/" + identifier(operation_id)


def records(state):
    table = state.get("runtime_v1", {})
    if not table:
        return {"operations": {}, "artifacts": {}, "stops": []}
    fields(table, ("operations", "artifacts", "stops"))
    if type(table["operations"]) is not dict or type(table["artifacts"]) is not dict or type(table["stops"]) is not list:
        raise ValueError("invalid v1 controller ledger")
    return table


def _dependencies(controller, table, request):
    for dependency in request["dependencies"]:
        parent = table["operations"].get(_key(request["run_id"], dependency))
        if parent is None or parent["status"] != "ACCEPTED":
            raise Blocked(f"dependency lacks an accepted prior receipt: {dependency}")
    for reference in request.get("input_artifacts", []):
        if reference not in table["artifacts"]:
            raise Blocked("operation input artifact is absent")
        item = read_artifact(controller.root, table["artifacts"][reference])
        producer = table["operations"].get(_key(*item["producer"]))
        if not producer or producer["status"] != "ACCEPTED":
            raise Blocked("operation input artifact producer lacks an accepted receipt")
        if item["producer"][0] == request["run_id"] and item["producer"][1] not in request["dependencies"]:
            raise ValueError("same-run artifact use requires its explicit dependency")
        args = request["args"]
        inputs = {args.get("deck"), args.get("sim"), args.get("fem"), args.get("cad"), args.get("path")}
        if item["path"] not in inputs and item["sha256"] != request["target"].get("result_sha256"):
            raise ValueError("artifact is unrelated to the actual bound input")


def _fence(state, table, request, effect, resources):
    if effect == "PURE_READ":
        return
    if state.get("license_stop") or any(r["status"] in PENDING for r in state["operations"].values()):
        raise Blocked("unreconciled legacy reservation or license stop is fenced")
    previous_workspace_fence = digest(["owned-file-effects"])
    file_target = request["target"]["kind"] == "file"
    keys = set(resources)
    # Earlier v1 receipts used one conservative fence for all owned file effects.
    if file_target:
        keys.add(previous_workspace_fence)
    if keys & set(table["stops"]):
        raise Blocked("native resource has an unresolved license stop")
    for record in table["operations"].values():
        if keys & set(record["resources"]):
            if record["status"] in PENDING and record["effect"] != "PURE_READ":
                raise Blocked("native resource has an unreconciled effect")
            if (effect == "SOLVER_SUBMIT" and record["effect"] == effect
                    and record["status"] in {"ACCEPTED", "ENGINEERING_REJECTED", "REJECTED"}):
                raise Blocked("the native solver submission ID or directory has already been consumed")


def _deadline(request):
    if "deadline" in request and stamp(request["deadline"]) <= datetime.now(timezone.utc):
        raise Denied("operation dispatch deadline has elapsed")


def ready(controller, state, table, record):
    if record["status"] != "PREPARED":
        return False
    try:
        _deadline(record["request"])
        _dependencies(controller, table, record["request"])
        _fence(state, table, record["request"], record["effect"], record["resources"])
    except (Blocked, Denied, OSError, ValueError):
        return False
    return True


def _context(controller, request, binding):
    output = request["output_scope"]
    if output != "." and not scoped_path(controller.root, output).is_dir():
        raise ValueError("output scope is not a task-owned directory")
    target = request["target"]
    if target["kind"] == "file":
        identity = file_identity(scoped_path(controller.root, target["path"]))
        if identity["sha256"] != target["sha256"]:
            raise ValueError("file target does not match its observed digest")
    if request["capability"] == "batchpost.result.open":
        path = scoped_path(controller.root, binding["qualification"]["result_path"])
        if (os.path.normcase(os.fspath(path)) != os.path.normcase(request["args"]["file"])
                or file_identity(path)["sha256"] != target["result_sha256"]):
            raise ValueError("BatchPost open arguments do not identify the exact owned result")
    if request["capability"] == "batchpost.result.extract":
        prefix = binding["qualification"]["output_prefix"]
        path = scoped_path(controller.root, prefix, exists=False)
        if os.path.normcase(os.fspath(path)) != os.path.normcase(request["args"]["to"]["value"]):
            raise ValueError("BatchPost export arguments differ from the owned prefix")
        if path.suffix.lower() != ".csv" or not path.parent.is_dir():
            raise ValueError("structured contour requires a CSV prefix in an existing task-owned directory")
        if output != "." and not path.is_relative_to(scoped_path(controller.root, output)):
            raise ValueError("export prefix is outside the declared output scope")
        if path.exists() or any(path.parent.glob(path.stem + "-*")):
            raise ValueError("export prefix has existing files")
    if request["capability"] == "sc3d.deck.export":
        deck = request["expected"]["deck_path"]["value"]
        from pathlib import Path

        path = Path(deck)
        scope = controller.root if output == "." else scoped_path(controller.root, output)
        if not path.is_absolute() or not path.is_relative_to(scope):
            raise ValueError("native export deck must be inside the task-owned scope")
        if scoped_path(controller.root, path.relative_to(controller.root).as_posix(), exists=False).exists():
            raise ValueError("native export deck already exists")


def prepare(controller, operation, binding, authority=None):
    verified = validate(operation, binding)
    authorize(operation, verified, authority)
    _deadline(operation)
    _context(controller, operation, binding)
    name = _key(operation["run_id"], operation["operation_id"])
    with controller.edit() as state:
        table = records(state)
        _dependencies(controller, table, operation)
        _fence(state, table, operation, verified["effect"], verified["resources"])
        if name in table["operations"]:
            raise ValueError("duplicate operation identifier in run")
        record = {**verified, "request": operation, "binding": binding, "authority": authority,
                  "status": "PREPARED", "prepared_at": now(), "artifact_refs": []}
        table["operations"][name] = record
        state["runtime_v1"] = table
    return record


def reserve(controller, run_id, operation_id, request_digest, binding, authority=None, preflight=None):
    name = _key(run_id, operation_id)
    with controller.edit() as state:
        table = records(state)
        record = table["operations"][name]
        request = record["request"]
        verified = validate(request, binding)
        legacy_file_fence = (request["target"]["kind"] == "file" and record["effect"] != "PURE_READ"
                             and record["resources"] == [digest(["owned-file-effects"])])
        if (record["status"] != "PREPARED" or request_digest != record["request_digest"]
                or any(not match(record[key], value) for key, value in verified.items()
                       if key != "resources" or not legacy_file_fence)):
            raise ValueError("prepared request, binding or state changed")
        authorize(request, verified, authority)
        _deadline(request)
        _context(controller, request, binding)
        _dependencies(controller, table, request)
        _fence(state, table, request, record["effect"], verified["resources"])
        if record["effect"] != "PURE_READ":
            fields(preflight, ("target", "observed_at", "evidence_ref", "witnesses"))
            if (not match(preflight["target"], request["target"])
                    or not stamp(record["prepared_at"]) <= stamp(preflight["observed_at"]) <= datetime.now(timezone.utc)
                    or text(preflight["evidence_ref"]) == binding["evidence_ref"]
                    or not isinstance(preflight["witnesses"], dict)
                    or not satisfies(request["baseline"], preflight["witnesses"])):
                raise Blocked("effect precondition requires a fresh matching independent witness")
        record.update(status="DISPATCH_RESERVED", reserved_at=now(), dispatch_preflight=preflight,
                      resources=verified["resources"])
    return record


def _save_raw(controller, raw):
    from fea_controller import save

    payload = canonical(raw)
    if len(payload) + 1 > MAX_JSON:
        raise ValueError("raw response exceeds the bounded evidence limit")
    raw_digest = hashlib.sha256(payload).hexdigest()
    folder = scoped_path(controller.root, "evidence", exists=False)
    folder.mkdir(exist_ok=True)
    path = scoped_path(controller.root, "evidence/" + raw_digest + ".json", exists=False)
    if not path.exists():
        save(path, raw)
    if path.read_bytes() != payload + b"\n":
        raise ValueError("recorded raw evidence differs from its content address")
    return raw_digest


def local_file_read(controller, operation, binding, reader):
    """Evaluate a known local read outside the lock and commit one terminal receipt."""
    verified = validate(operation, binding)
    if (verified["effect"] != "PURE_READ" or operation["target"]["kind"] != "file"
            or CAPABILITIES[operation["capability"]]["backend"] != "local"):
        raise ValueError("single-commit execution applies only to pure local file reads")
    _deadline(operation)
    _context(controller, operation, binding)
    name = _key(operation["run_id"], operation["operation_id"])
    prior = records(controller.snapshot())
    _dependencies(controller, prior, operation)
    if name in prior["operations"]:
        raise ValueError("duplicate operation identifier in run")
    started_at = now()
    error = None
    projection = {}
    try:
        raw, witnesses, evidence_ref, disposition, projection = reader(operation)
        _context(controller, operation, binding)
        if evidence_ref in {binding["evidence_ref"], digest(raw)}:
            raise ValueError("local read needs a distinct scoped evidence reference")
        if disposition not in {"UNVERIFIED", "REJECTED"} or not isinstance(witnesses, dict):
            raise ValueError("invalid local check observation")
    except (OSError, TypeError, ValueError) as exc:
        error = exc
        raw, witnesses, evidence_ref, disposition = None, {}, None, "UNVERIFIED"
    with controller.edit() as state:
        table = records(state)
        _dependencies(controller, table, operation)
        if name in table["operations"]:
            raise ValueError("duplicate operation identifier in run")
        raw_digest = _save_raw(controller, raw)
        observed_at = now()
        record = {**verified, "request": operation, "binding": binding, "authority": None,
                  "prepared_at": started_at, "response_at": observed_at, "observed_at": observed_at,
                  "raw_digest": raw_digest, "artifact_refs": [],
                  "engineering_disposition": disposition}
        if error is None:
            observation = {"target": operation["target"], "observed_at": observed_at,
                           "evidence_ref": evidence_ref, "witnesses": witnesses, "coverage": "COMPLETE",
                           "settled": True, "engineering_disposition": disposition}
            record.update(status=_verification(operation, observation, "PURE_READ"),
                          outcome="RESPONSE_RECORDED", observations=[observation])
        else:
            record.update(status="READ_FAILED", outcome="FAILED_RESPONSE", transport_error=str(error)[:4096])
        table["operations"][name] = record
        state["runtime_v1"] = table
    if error is not None:
        raise error
    return record, projection


def record_response(controller, run_id, operation_id, raw=None, transport_error=None):
    name = _key(run_id, operation_id)
    with controller.edit() as state:
        table = records(state)
        record = table["operations"][name]
        if record["status"] != "DISPATCH_RESERVED":
            raise ValueError("operation lacks a dispatch reservation")
        if transport_error is not None:
            text(transport_error)
        raw_ref = _save_raw(controller, raw)
        payload = canonical(raw).lower()
        license_stop = any(token in payload for token in (
            b"licensed number of users already reached", b"nx_design_token",
            b"license checkout failed", b"unable to obtain a license"))
        failure = transport_error is not None or not raw or response_failed(raw) or license_stop
        status = "OBSERVATION_REQUIRED"
        if failure:
            status = "READ_FAILED" if record["effect"] == "PURE_READ" else "UNKNOWN"
        record.update(status=status, raw_digest=raw_ref, transport_error=transport_error,
                      response_at=now(), outcome="LICENSE_STOP" if license_stop else (
                          "TRANSPORT_LOST" if transport_error else "FAILED_RESPONSE" if failure else "RESPONSE_RECORDED"))
        if license_stop and record["effect"] != "PURE_READ":
            table["stops"] = sorted(set(table["stops"]) | set(record["resources"]))
    return record


def _verification(request, observation, effect):
    if observation["coverage"] != "COMPLETE" or not observation["settled"]:
        return "UNKNOWN"
    witnesses = observation["witnesses"]
    after = satisfies(request["expected"], witnesses)
    before = bool(request.get("baseline")) and satisfies(request["baseline"], witnesses)
    if after and not before:
        return "ENGINEERING_REJECTED" if observation.get("engineering_disposition") == "REJECTED" else "ACCEPTED"
    if before and not after:
        return "NOT_APPLIED"
    return "READ_FAILED" if effect == "PURE_READ" else "UNKNOWN"


def observe(controller, run_id, operation_id, observation, *, reconcile=False):
    name = _key(run_id, operation_id)
    fields(observation, ("target", "observed_at", "evidence_ref", "witnesses", "coverage", "settled"),
           ("artifacts", "engineering_disposition"))
    if type(observation["witnesses"]) is not dict or type(observation["settled"]) is not bool:
        raise ValueError("observation needs typed witnesses and settlement evidence")
    if observation["coverage"] not in {"COMPLETE", "PARTIAL", "UNVERIFIED"}:
        raise ValueError("unknown observation coverage")
    reference = text(observation["evidence_ref"])
    disposition = observation.get("engineering_disposition", "UNVERIFIED")
    if disposition not in {"UNVERIFIED", "ACCEPTED", "REJECTED"}:
        raise ValueError("unknown engineering disposition")
    with controller.edit() as state:
        table = records(state)
        record = table["operations"][name]
        if record["status"] not in PENDING:
            raise ValueError("operation is not awaiting observation")
        if record["status"] == "DISPATCH_RESERVED" and not reconcile:
            raise Blocked("unrecorded dispatch requires explicit reconciliation")
        request = record["request"]
        observed = stamp(observation["observed_at"])
        if (not match(target_identity(observation["target"]), target_identity(request["target"]))
                or not stamp(record.get("response_at", record["reserved_at"])) < observed <= datetime.now(timezone.utc)
                or reference in {record.get("raw_digest"), record["binding"]["evidence_ref"]}
                or reference == (record.get("dispatch_preflight") or {}).get("evidence_ref")
                or any(reference == prior["evidence_ref"] for prior in record.get("observations", []))):
            raise ValueError("fresh independent observation of the bound target is required")
        witnesses = observation["witnesses"]
        if request["capability"] == "batchpost.result.extract" and observation["coverage"] == "COMPLETE":
            from .batchpost import export_paths

            if not record.get("raw_digest") or record.get("outcome") != "RESPONSE_RECORDED":
                raise Blocked("complete BatchPost coverage needs a successful recorded native response")
            raw_path = scoped_path(controller.root, "evidence/" + record["raw_digest"] + ".json")
            raw = load_json(raw_path)
            if digest(raw) != record["raw_digest"]:
                raise ValueError("native raw evidence is not authentic to this receipt")
            path, values = export_paths(controller.root, request, record["binding"], raw)
            reported = observation.get("artifacts", [])
            if (not match(values, witnesses.get("field_values")) or len(reported) != 1
                    or reported[0].get("path") != path.relative_to(controller.root).as_posix()):
                raise ValueError("verified native CSV does not match the requested witness or artifact")
        verification = _verification(request, observation, record["effect"])
        specifications = observation.get("artifacts", [])
        if type(specifications) is not list or len(specifications) > 256:
            raise ValueError("invalid or excessive artifact evidence")
        new_refs = []
        record.setdefault("observations", [])
        if len(record["observations"]) >= 256:
            raise Blocked("observations reached the bounded ledger limit")
        for specification in specifications:
            if set(specification.get("parents", ())) != set(request.get("input_artifacts", ())):
                raise ValueError("artifact output omits or substitutes the declared input lineage")
            item = artifact(controller.root, request, specification, observed_at=observation["observed_at"])
            if any(parent not in table["artifacts"] for parent in item["parents"]):
                raise ValueError("artifact lineage refers to an absent or forward parent")
            table["artifacts"][item["id"]] = item
            new_refs.append(item["id"])
        record["observations"].append(observation)
        record["artifact_refs"].extend(new_refs)
        record.update(status=verification, observed_at=now(), engineering_disposition=disposition)
    return record
