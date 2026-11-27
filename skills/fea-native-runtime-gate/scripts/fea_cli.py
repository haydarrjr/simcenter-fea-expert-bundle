"""Thin local CLI for the shared Simcenter FEA controller."""

import argparse
from pathlib import Path
import subprocess
import sys

from fea_controller import Controller, canonical, digest
from fea_runtime import VERSION
from fea_runtime.artifacts import csv_rows, read_artifact
from fea_runtime.contracts import CAPABILITIES, Blocked, Denied, fields, identifier, load_json, validate
from fea_runtime.operations import ready, records


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def _actions(parent):
    return parent.add_subparsers(dest="action", required=True)


def _request(parser, *, product=False):
    parser.add_argument("--root", type=Path, default=Path(".work/fea-runtime"))
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--authority", type=Path)
    if product:
        parser.add_argument("--product", required=True, type=Path)


def parser():
    result = Parser(description=__doc__)
    domains = result.add_subparsers(dest="domain", required=True)
    caps = _actions(domains.add_parser("capabilities"))
    search = caps.add_parser("search")
    search.add_argument("--query", required=True)
    search.add_argument("--domain", dest="scope", choices=("sc3d", "nastran", "batchpost"))
    caps.add_parser("describe").add_argument("id")
    for domain in ("sc3d", "nastran", "batchpost"):
        actions = _actions(domains.add_parser(domain))
        _request(actions.add_parser("prepare"))
        if domain == "nastran":
            _request(actions.add_parser("inspect"))
            _request(actions.add_parser("verify"))
            _request(actions.add_parser("submit"), product=True)
        elif domain == "sc3d":
            _request(actions.add_parser("batch"), product=True)
    operations = _actions(domains.add_parser("operation"))
    for action in ("validate", "reserve", "record", "observe", "reconcile", "reconcile-job"):
        _request(operations.add_parser(action))
    runs = _actions(domains.add_parser("run"))
    for action in ("status", "next"):
        command = runs.add_parser(action)
        command.add_argument("--root", type=Path, default=Path(".work/fea-runtime"))
        command.add_argument("--run-id")
    artifact = _actions(domains.add_parser("artifact")).add_parser("inspect")
    artifact.add_argument("--root", type=Path, default=Path(".work/fea-runtime"))
    artifact.add_argument("--id", required=True)
    artifact.add_argument("--field", action="append", default=[])
    artifact.add_argument("--row-start", type=int, default=0)
    artifact.add_argument("--row-count", type=int, default=0)
    return result


def project(record):
    operation = record["request"]
    return {
        "run_id": operation["run_id"], "operation_id": operation["operation_id"],
        "capability": operation["capability"], "execution_status": record["status"],
        "engineering_disposition": record.get("engineering_disposition", "UNVERIFIED"),
        "request_digest": record["request_digest"], "binding_digest": record["binding_digest"],
        "target": operation["target"], "evidence_ref": record.get("raw_digest"),
        "artifact_refs": record["artifact_refs"], "outcome": record.get("outcome"),
    }


def local_read(controller, payload, action):
    expected = "nastran.deck.inspect" if action == "inspect" else "nastran.artifact.verify"
    if payload["operation"]["capability"] != expected:
        raise ValueError("operation capability differs from the local read command")

    def read(operation):
        if action == "inspect":
            from fea_runtime.native import inspect_deck

            deck, _ = inspect_deck(controller.root, operation["args"])
            if deck.files[deck.entry]["sha256"] != operation["target"]["sha256"]:
                raise ValueError("deck bytes changed during inspection")
            closure = digest(deck.files)
            detail = {"entry": deck.entry, "sequence": deck.solution,
                      "subcases": list(deck.subcases), "closure_digest": closure}
            witnesses = {"sol": deck.solution, "subcases": list(deck.subcases), "deck_digest": closure}
            return deck.summary(), witnesses, "deck:" + closure, "UNVERIFIED", {"deck": detail}
        from fea_runtime.engineering.service import execute as engineering_check

        report = engineering_check(controller.root, operation["args"])
        disposition = "REJECTED" if report.get("status") in {"DIFFERS", "REJECTED"} else "UNVERIFIED"
        checksum = digest(report)
        witnesses = {"method": operation["args"]["method"], "report_status": report.get("status"),
                     "report_digest": checksum}
        return {"report": report}, witnesses, "check:" + checksum, disposition, {}

    record, extra = controller.transition("local-file-read", **payload, reader=read)
    return {**project(record), **extra}


def execute(args):
    domain, action = args.domain, args.action
    if domain == "capabilities":
        if action == "describe":
            return {"capability": args.id, "descriptor": CAPABILITIES[args.id]}
        query = args.query.casefold()
        return {"capabilities": [{"id": name, "backend": descriptor["backend"], "availability": descriptor["availability"],
                                   "qualification": descriptor["qualification"]}
                                  for name, descriptor in CAPABILITIES.items()
                                  if (not args.scope or name.startswith(args.scope + "."))
                                  and query in (name + " " + descriptor["owner"] + " " +
                                                descriptor["outputs"]).casefold()]}
    if domain == "operation" and action == "validate":
        payload = load_json(args.request)
        fields(payload, ("operation", "binding"))
        verified = validate(**payload)
        operation = payload["operation"]
        return {"execution_status": "VALIDATED", "run_id": operation["run_id"],
                "operation_id": operation["operation_id"], **verified}
    controller = Controller(args.root)
    if domain in {"run", "artifact"}:
        state = controller.snapshot()
        table = records(state)
        if domain == "artifact":
            item = table["artifacts"][args.id]
            metadata = read_artifact(controller.root, item, args.field)
            if args.row_count:
                return {"artifact": metadata, "row_start": args.row_start,
                        "rows": csv_rows(controller.root, item, args.row_start, args.row_count)}
            return {"artifact": metadata}
        run = identifier(args.run_id) if args.run_id else None
        return {"operations": [project(record) for name, record in table["operations"].items()
                               if (not run or name.startswith(run + "/"))
                               and (action == "status" or ready(controller, state, table, record))][:100]}
    payload = load_json(args.request)
    authority = load_json(args.authority) if args.authority else None
    if domain != "operation":
        fields(payload, ("operation", "binding"))
        if not payload["operation"]["capability"].startswith(domain + "."):
            raise ValueError("operation capability differs from the CLI domain")
    if action == "prepare":
        return project(controller.transition("prepare", **payload, authority=authority))
    if action in {"inspect", "verify"}:
        return local_read(controller, payload, action)
    if action == "submit":
        from fea_runtime.native import submit

        if payload["operation"]["capability"] != "nastran.job.submit":
            raise ValueError("expected a native job submission")
        return project(submit(controller, payload["operation"], payload["binding"], authority, args.product))
    if action == "batch":
        from fea_runtime.sc3d import ACTIONS, execute_batch

        if payload["operation"]["capability"] not in ACTIONS:
            raise ValueError("expected a supported isolated model operation")
        return project(execute_batch(controller, **payload, authority=authority, product=args.product))
    if action == "reconcile-job":
        from fea_runtime.native import reconcile_job

        fields(payload, ("run_id", "operation_id"))
        return project(reconcile_job(controller, **payload))
    if action == "reserve":
        fields(payload, ("run_id", "operation_id", "request_digest", "binding"), ("preflight",))
        pending = records(controller.snapshot())["operations"][payload["run_id"] + "/" + payload["operation_id"]]
        if CAPABILITIES[pending["request"]["capability"]]["backend"] != "host":
            raise Blocked("local dispatch requires its explicit native or file command")
        reserved = controller.transition(action, **payload, authority=authority)
        return {**project(reserved), "dispatch": {
            "profile": reserved["binding"]["profile"], "tool": reserved["binding"]["tool"],
            "arguments": reserved["request"]["args"]}}
    if action == "record":
        fields(payload, ("run_id", "operation_id"), ("raw", "transport_error"))
    else:
        fields(payload, ("run_id", "operation_id", "observation"))
    return project(controller.transition(action, **payload))


def main(argv=None):
    try:
        args = parser().parse_args(argv)
        report = execute(args)
        status = report.get("execution_status", "NOT_DISPATCHED")
        exit_code = {"UNKNOWN": 4, "READ_FAILED": 5, "ENGINEERING_REJECTED": 6}.get(status, 0)
        result = {"contract_version": VERSION, "command_status": "COMPLETED",
                  "execution_status": status, "engineering_disposition": "UNVERIFIED", **report}
    except (Blocked, Denied, KeyError, TypeError, ValueError, OSError, subprocess.SubprocessError) as exc:
        exit_code = 4 if isinstance(exc, Blocked) else 3 if isinstance(exc, Denied) else (
            5 if isinstance(exc, (OSError, subprocess.SubprocessError)) else 2)
        result = {"contract_version": VERSION, "command_status": {
            2: "INPUT_REJECTED", 3: "AUTHORIZATION_REJECTED", 4: "BLOCKED", 5: "RUNTIME_ERROR"}[exit_code],
                  "execution_status": "UNVERIFIED", "engineering_disposition": "UNVERIFIED",
                  "findings": [str(exc)[:1000]]}
        print(str(exc)[:1000], file=sys.stderr)
    print(canonical(result).decode("utf-8"))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
