"""Qualify a structured contour against an owned original native result.

Run explicitly on Windows. The supplied manifest binds the workspace result,
its accepted predecessor receipt, observed case and column, and an independent
predeclared physical value. This fixture runner owns one existing official
BatchPost worker for the duration of its qualification.
"""

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sys


def qualify(package, product, root, manifest, evidence):
    sys.path.insert(0, str(package))
    from scripts.qualify_codex_readonly import AppServer
    scripts = package / "skills/fea-native-runtime-gate/scripts"
    sys.path.insert(0, str(scripts))
    from fea_controller import Controller, digest, now, save
    from fea_runtime.artifacts import file_identity
    from fea_runtime.batchpost import export_paths
    from fea_runtime.contracts import load_json, scoped_path, validate

    class BatchPostClient(AppServer):
        def send(self, message):
            super().send({"jsonrpc": "2.0", **message})

    controller = Controller(root)
    report_root = root / evidence
    report_root.mkdir()
    result = scoped_path(root, manifest["result"])
    archive = {}

    def call(name, argv, expected_error=False):
        try:
            reply = client.request("tools/call", {"name": name, "arguments": argv}, timeout=45)
        except RuntimeError as exc:
            if expected_error and "no results file is open" in str(exc):
                archive.setdefault("calls", []).append({"name": name, "observed_empty": True})
                return {}
            raise
        archive.setdefault("calls", []).append({"name": name, "arguments": argv, "response": reply})
        if bool(reply.get("isError")) != expected_error:
            raise ValueError(f"native BatchPost {name} failed: {reply.get('content')}")
        return reply

    def single(value):
        return {"type": "single", "value": value}

    def exact(value):
        return {"op": "exact", "value": value}

    worker_log = report_root / "worker.log"
    with worker_log.open("w", encoding="utf-8") as log:
        client = BatchPostClient([sys.executable, "-B", "-u", str(scripts / "batchpost_mcp.py"),
                                  "--ugii-base-dir", str(product)], report_root, log)
        opened = False
        try:
            archive["initialize"] = client.request("initialize", {"protocolVersion": "2024-11-05",
                "capabilities": {}, "clientInfo": {"name": "fea-contour-qualification", "version": "1"}}, timeout=65)
            client.send({"method": "notifications/initialized"})
            advertised = client.request("tools/list", {})["tools"]
            archive["tools"] = advertised
            descriptor = next(item for item in advertised if item["name"] == "contour")
            worker_info = re.search(r"native pid=(\d+)", worker_log.read_text(encoding="utf-8"))
            if not worker_info:
                raise ValueError("worker ownership has no native process evidence")
            worker = "pid-" + worker_info[1]
            opening = call("open", {"file": str(result)})
            opened = True
            if not any(str(result) in block.get("text", "") for block in opening["content"]):
                raise ValueError("native open response lost exact path identity")
            raw_catalog = call("list", {})
            catalog = raw_catalog.get("structuredContent") or json.loads(raw_catalog["content"][0]["text"])
            target = {"kind": "batchpost", "host": "isolated-local-windows", "worker": worker,
                      "release": manifest["release"], "result_sha256": file_identity(result)["sha256"],
                      "catalog_digest": digest(catalog)}
            selection = manifest["selection"]
            case = next(item for item in catalog["loadcases"] if item["index"] == selection["case"])
            step = next(item for item in case["iterations"] if item["index"] == selection["state"])
            field = next(item for item in step["result_types"] if item["unique_name"] == selection["result"])
            prefix = (report_root / "contour.csv").relative_to(root).as_posix()
            argv = {"loadcase_index": single(selection["case"]), "iteration_index": single(selection["state"]),
                    "resulttype": single(field["name"]), "component": single(selection["component"]),
                    "unit": single(selection["units"]), selection["entity"]: ",".join(map(str, selection["labels"])),
                    "to": single(str(root / prefix))}
            observed = now()
            qualification = {"release": target["release"], "capability": "batchpost.result.extract",
                             "descriptor_digest": digest(descriptor), "owned_worker": worker,
                             "evidence_ref": manifest["qualification_basis"], "result_catalog": catalog,
                             "selection": selection, "output_prefix": prefix}
            binding = {"target": target, "observed_at": observed, "evidence_ref": "catalog:" + digest(raw_catalog),
                       "profile": "batchpost", "tool": "contour", "catalog": advertised,
                       "catalog_digest": digest(advertised), "descriptor_digest": digest(descriptor),
                       "qualification": qualification}
            operation = {"version": 1, "run_id": manifest["run_id"], "operation_id": manifest["operation_id"],
                         "capability": "batchpost.result.extract", "target": target, "args": argv,
                         "dependencies": manifest["dependencies"], "input_artifacts": [manifest["result_artifact"]],
                         "output_scope": evidence, "baseline": {"export_present": exact(False)},
                         "expected": {"export_present": exact(True)}, "authorization_ref": manifest["authorization"],
                         "deadline": (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()}
            verified = validate(operation, binding)
            authority = {"ref": operation["authorization_ref"], **{k: verified[k] for k in
                         ("request_digest", "binding_digest", "effect")}}
            controller.transition("prepare", operation=operation, binding=binding, authority=authority)
            names = {key: operation[key] for key in ("run_id", "operation_id")}
            preflight = {"target": target, "observed_at": now(), "witnesses": {"export_present": False},
                         "evidence_ref": f"preflight:{worker}:{now()}"}
            controller.transition("reserve", **names, request_digest=verified["request_digest"],
                                  binding=binding, preflight=preflight, authority=authority)
            try:
                raw = call("contour", argv)
            except (OSError, ValueError, RuntimeError) as exc:
                controller.transition("record", **names, transport_error=str(exc)[:4096])
                raise
            controller.transition("record", **names, raw=raw)
            path, values = export_paths(root, operation, binding, raw)
            next_catalog = call("list", {})
            if (next_catalog.get("structuredContent") or json.loads(next_catalog["content"][0]["text"])) != catalog:
                raise ValueError("native result catalog changed during extraction")
            if file_identity(result)["sha256"] != target["result_sha256"]:
                raise ValueError("exact result identity changed during extraction")
            expected = manifest["reference"]
            passed = values.keys() == expected.keys() and all(
                abs(value - expected[label]) <= manifest["absolute_tolerance"] +
                manifest["relative_tolerance"] * abs(expected[label]) for label, value in values.items())
            receipt = controller.transition("observe", **names, observation={
                "target": target, "observed_at": now(), "evidence_ref": "readback:" + digest(values),
                "coverage": "COMPLETE", "settled": True,
                "engineering_disposition": "ACCEPTED" if passed else "REJECTED",
                "witnesses": {"field_values": values, "export_present": True,
                              "reference": expected, "absolute_tolerance": manifest["absolute_tolerance"],
                              "relative_tolerance": manifest["relative_tolerance"]},
                "artifacts": [{"type": "batchpost.contour.csv", "path": path.relative_to(root).as_posix(),
                               "tool": "contour", "build": target["release"], "coverage": "COMPLETE",
                               "parents": [manifest["result_artifact"]]}]})
            archive["result"] = {"status": receipt["status"], "values": values,
                                 "artifact_refs": receipt["artifact_refs"]}
        finally:
            try:
                if opened:
                    call("close", {})
                    call("list", {}, expected_error=True)
            finally:
                client.close()
                save(report_root / "qualification.json", archive)
    return archive["result"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("package", "product", "root", "manifest"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = qualify(args.package.resolve(strict=True), args.product.resolve(strict=True),
                     args.root.resolve(strict=True), manifest, args.evidence)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["status"] == "ACCEPTED" else 6)
