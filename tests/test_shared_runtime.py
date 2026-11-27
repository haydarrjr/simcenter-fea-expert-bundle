"""Regressions for the versioned CLI, admission and shared resource ledger."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/fea-native-runtime-gate/scripts"
sys.path.insert(0, str(SCRIPTS))

from fea_controller import Controller, digest, now
from fea_runtime.artifacts import file_identity, read_artifact
from fea_runtime.contracts import Blocked, Denied, load_json, match, satisfies, validate
from fea_runtime.engineering.spectral import verify_response
from fea_runtime.host import check_schema
from fea_runtime.operations import records


def exact(value):
    return {"op": "exact", "value": value}


def effect(run, profile):
    target = {"kind": "sc3d", "host": "desktop", "native_process": "nx:verified-pid-and-start",
              "release": "2612.1700", "work": run, "display": run, "owner": "fem",
              "occurrence": "/", "model": run, "precondition": "0" * 64}
    if profile == "designcenter":
        capability = "sc3d.journal.qualified"
        tool, args = "dcopen-execute-tool", {"python_code": "def main(args):\n    return 3\n"}
        properties = {"python_code": {"type": "string"}}
    else:
        capability = "sc3d.mesh.generate"
        tool, args = "surface-mesh-generation-tool", {"mesh": {"size": 12}}
        properties = {"mesh": {"$ref": "#/$defs/settings"}}
    descriptor = {"name": tool, "inputSchema": {"type": "object", "properties": properties,
                   "additionalProperties": False, "required": list(args),
                   "$defs": {"settings": {"type": "object", "properties": {"size": {"type": "integer", "minimum": 1}},
                                           "required": ["size"], "additionalProperties": False}}}}
    catalog = [descriptor]
    binding = {"profile": profile, "tool": tool, "target": target, "evidence_ref": "target:" + run,
               "observed_at": now(), "catalog": catalog, "catalog_digest": digest(catalog),
               "descriptor_digest": digest(descriptor), "qualification": {
                   "release": target["release"], "evidence_ref": "qualified-fixture",
                   "capability": capability, "descriptor_digest": digest(descriptor),
                   "source_digest": digest(args.get("python_code")), "sandbox_reviewed": True,
                   "installed_member_evidence": "test-fixture",
               }}
    operation = {"version": 1, "operation_id": "effect", "run_id": run, "capability": capability,
                 "target": target, "args": args, "baseline": {"change": exact(False)},
                 "expected": {"change": exact(True)}, "dependencies": [], "output_scope": ".",
                 "deadline": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                 "authorization_ref": "test-grant"}
    verified = validate(operation, binding)
    authority = {"ref": "test-grant", **{key: verified[key]
                 for key in ("effect", "request_digest", "binding_digest")}}
    return operation, binding, authority


def preflight(target, run):
    return {"target": target, "observed_at": now(), "evidence_ref": "preflight:" + run,
            "witnesses": {"change": False}}


class RuntimeTests(unittest.TestCase):
    def test_cross_profile_unknown_survives_controller_restart(self):
        with tempfile.TemporaryDirectory(prefix="fea-runtime ü ") as directory:
            controller = Controller(directory)
            a, ba, au = effect("A", "simcenter3d")
            b, bb, bu = effect("B", "designcenter")
            for request, binding, grant in ((a, ba, au), (b, bb, bu)):
                controller.transition("prepare", operation=request, binding=binding, authority=grant)
            names = {"run_id": "A", "operation_id": "effect"}
            controller.transition("reserve", **names, request_digest=au["request_digest"], binding=ba,
                                  authority=au, preflight=preflight(a["target"], "A"))
            controller.transition("record", **names, transport_error="host timed out")
            restarted = Controller(directory)
            with self.assertRaises(Blocked):
                restarted.transition("reserve", run_id="B", operation_id="effect", request_digest=bu["request_digest"],
                                     binding=bb, authority=bu, preflight=preflight(b["target"], "B"))
            partial = {"target": a["target"], "evidence_ref": "unsettled", "observed_at": now(),
                       "witnesses": {"change": False}, "coverage": "COMPLETE", "settled": False}
            self.assertEqual(restarted.transition("reconcile", **names, observation=partial)["status"], "UNKNOWN")
            with self.assertRaisesRegex(ValueError, "fresh"):
                restarted.transition("reconcile", **names, observation=partial)
            settled = {**partial, "evidence_ref": "native settled", "observed_at": now(), "settled": True}
            self.assertEqual(restarted.transition("reconcile", **names, observation=settled)["status"], "NOT_APPLIED")
            rejected_grant = {**bu, "effect": "wrong"}
            with self.assertRaises(Denied):
                restarted.transition("reserve", run_id="B", operation_id="effect", request_digest=bu["request_digest"],
                                     binding=bb, authority=rejected_grant, preflight=preflight(b["target"], "B"))
            self.assertEqual(restarted.transition("reserve", run_id="B", operation_id="effect",
                             request_digest=bu["request_digest"], binding=bb, authority=bu,
                             preflight=preflight(b["target"], "B"))["status"], "DISPATCH_RESERVED")

    def test_nested_local_schema_and_exact_numeric_predicate(self):
        operation, binding, _ = effect("A", "simcenter3d")
        operation["args"]["mesh"]["size"] = True
        with self.assertRaisesRegex(ValueError, "/mesh/size"):
            validate(operation, binding)
        for ref in ("https://example.com/schema", "#/$defs/cycle"):
            schema = {"type": "object", "$defs": {"cycle": {"$ref": ref}},
                      "properties": {"mesh": {"$ref": ref}}}
            with self.assertRaisesRegex(Blocked, "reference"):
                check_schema(schema, {"mesh": {}})
        self.assertFalse(match({"id": True}, {"id": 1}))
        predicate = {"qoi": {"op": "numeric", "value": 10, "abs_tol": .02, "rel_tol": .01,
                              "units": "N", "dimension": "force", "frame": "basic"}}
        value = {"value": 10.11, "units": "N", "dimension": "force", "frame": "basic"}
        self.assertTrue(satisfies(predicate, {"qoi": value}))
        for wrong in ({"value": True}, {"frame": "occurrence"}, {"units": "kN"}, {"value": 10.13}):
            self.assertFalse(satisfies(predicate, {"qoi": {**value, **wrong}}))

    def test_json_validation_has_no_workspace_effects(self):
        with tempfile.TemporaryDirectory(prefix="fea runtime ü ") as directory:
            root = Path(directory)
            operation, binding, _ = effect("A", "simcenter3d")
            path = root / "request.json"
            import json

            path.write_text(json.dumps({"operation": operation, "binding": binding}), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(SCRIPTS / "fea_cli.py"),
                "operation", "validate", "--root", str(root / "does not exist"), "--request", str(path)],
                capture_output=True, check=True, encoding="utf-8")
            self.assertEqual(json.loads(result.stdout)["execution_status"], "VALIDATED")
            self.assertFalse((root / "does not exist").exists())
            for bad in ('{"a":{"x":true,"x":1}}', '{"a":1e999}', '{"a":NaN}'):
                path.write_text(bad, encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_json(path)

    def test_artifact_tampering_and_missing_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            src = root / "data.dat"
            src.write_bytes(b"opaque")
            item = {**file_identity(src), "path": "data.dat"}
            self.assertEqual(read_artifact(root, item, ["path"]), {"path": "data.dat"})
            src.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "no longer match"):
                read_artifact(root, item)
            operation, binding, _ = effect("A", "simcenter3d")
            operation["dependencies"] = ["missing"]
            verified = validate(operation, binding)
            grant = {"ref": "test-grant", **{key: verified[key]
                     for key in ("request_digest", "binding_digest", "effect")}}
            controller = Controller(root)
            with self.assertRaisesRegex(Blocked, "dependency"):
                controller.transition("prepare", operation=operation, binding=binding, authority=grant)
            self.assertEqual(records(controller.snapshot())["operations"], {})

    def test_nonlinear_observation_uses_the_canonical_control_parser(self):
        from fea_runtime.engineering.service import execute

        fixtures = Path(__file__).with_name("fixtures")
        name = "sol401-elastic-contact-cycle.txt"
        report = execute(fixtures, {"path": name, "method": "nonlinear_deck"})
        self.assertEqual(report["sol"], 401)
        self.assertEqual([item["id"] for item in report["subcases"]], [1, 2, 3, 4])
        self.assertEqual(report["subcases"][2]["effective"]["TSTEP"]["value"], "13")
        self.assertEqual(report["global_control"]["BCRESULTS"]["value"], "17")

    def test_scoped_sc3d_mutations_require_exact_shape_and_distinct_guards(self):
        from fea_runtime.sc3d import validate_batch

        spec = {"native_state": exact("VERIFIED")}
        operation = {"capability": "sc3d.bc.scale_nodal_force",
                     "target": {"path": "owned.sim", "schema": "sc3d.sim"},
                     "baseline": {"native_state": exact("UNLAUNCHED")}, "expected": spec,
                     "args": {"sim": "owned.sim", "fem": "owned_fem.fem", "fem_sha256": "a"*64,
                              "launcher_sha256": "b"*64,
                              "load": {"solution": "case", "step": "step", "name": "force",
                                       "grid_labels": [21,42], "scale_before": 1, "scale_after": 1.25}}}
        validate_batch(operation)
        for labels in ([21, 21], [True], [42, 21]):
            bad = deepcopy(operation)
            bad["args"]["load"]["grid_labels"] = labels
            with self.assertRaisesRegex(ValueError, "grid labels"):
                validate_batch(bad)
        bad = deepcopy(operation)
        bad["target"]["schema"] = "sc3d.fem"
        with self.assertRaisesRegex(ValueError, "editable part"):
            validate_batch(bad)

        mesh = {**operation, "capability": "sc3d.mesh.refine_region",
                "target": {"path": "owned_fem.fem", "schema": "sc3d.fem"},
                "args": {"fem": "owned_fem.fem", "cad": "owned.prt", "cad_sha256": "c"*64,
                         "launcher_sha256": "b"*64,
                         "region": {"cad_body": "owner", "cad_face": "face", "guard_body": "guard",
                                    "face_vertices_mm": [[0,0,0],[0,1,0],[1,0,0]], "size_mm": 2}}}
        validate_batch(mesh)
        mesh["args"]["region"]["guard_body"] = "owner"
        with self.assertRaisesRegex(ValueError, "guard body"):
            validate_batch(mesh)

    def test_owned_file_fences_cover_shared_dependencies_and_allow_independent_edit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ("a.sim", "b.sim", "c.sim", "one.fem", "two.fem"):
                (root / name).write_text(name, encoding="utf-8")
            controller = Controller(root)

            def prepare(name, fem):
                target = {"kind": "file", "path": name + ".sim", "schema": "sc3d.sim",
                          "sha256": file_identity(root / (name + ".sim"))["sha256"]}
                op = {"version": 1, "run_id": name, "operation_id": "scale",
                      "capability": "sc3d.bc.scale_nodal_force", "target": target,
                      "args": {"sim": name + ".sim", "fem": fem,
                               "fem_sha256": file_identity(root / fem)["sha256"],
                               "launcher_sha256": "c" * 64,
                               "load": {"solution": "SOL101", "step": "test", "name": "native force",
                                        "grid_labels": [12], "scale_before": 1, "scale_after": 1.5}},
                      "dependencies": [], "output_scope": ".",
                      "expected": {"native_state": exact("VERIFIED")},
                      "baseline": {"native_state": exact("UNLAUNCHED")},
                      "deadline": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                      "authorization_ref": "caller"}
                binding = {"target": target, "evidence_ref": name, "observed_at": now()}
                verified = validate(op, binding)
                grant = {"ref": "caller", **{key: verified[key] for key in
                         ("request_digest", "binding_digest", "effect")}}
                return controller.transition("prepare", operation=op, binding=binding, authority=grant)

            chosen = prepare("a", "one.fem")
            request = chosen["request"]
            controller.transition("reserve", run_id="a", operation_id="scale",
                                  request_digest=chosen["request_digest"], binding=chosen["binding"],
                                  authority=chosen["authority"], preflight={
                                      "target": request["target"], "observed_at": now(),
                                      "evidence_ref": "verified a",
                                      "witnesses": {"native_state": "UNLAUNCHED"}})
            with self.assertRaisesRegex(Blocked, "unreconciled effect"):
                prepare("b", "one.fem")
            self.assertEqual(prepare("c", "two.fem")["status"], "PREPARED")

    def test_local_file_read_commits_once_and_retains_a_read_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "owned.dat").write_bytes(b"owned content")
            target = {"kind": "file", "path": "owned.dat", "schema": "nastran.deck",
                      "sha256": file_identity(root / "owned.dat")["sha256"]}
            operation = {"version": 1, "run_id": "local", "operation_id": "deck",
                         "capability": "nastran.deck.inspect", "target": target,
                         "args": {"deck": "owned.dat", "input_scope": "."}, "dependencies": [],
                         "output_scope": ".", "expected": {"sol": exact(101)}}
            binding = {"target": target, "evidence_ref": "owned input", "observed_at": now()}
            controller = Controller(root)

            def inspect_while_unreserved(_operation):
                self.assertFalse(records(controller.snapshot())["operations"])
                return {"sol": 101}, {"sol": 101}, "original-deck", "UNVERIFIED", {}

            report, _ = controller.transition("local-file-read", operation=operation, binding=binding,
                                              reader=inspect_while_unreserved)
            self.assertEqual(report["status"], "ACCEPTED")
            self.assertEqual(report["observations"][0]["witnesses"], {"sol": 101})
            self.assertNotIn("reserved_at", report)

            def read_failed(_operation):
                raise ValueError("native file structure is malformed")

            with self.assertRaisesRegex(ValueError, "file structure"):
                controller.transition("local-file-read", operation={**operation, "operation_id": "bad"},
                                      binding=binding, reader=read_failed)
            failure = records(controller.snapshot())["operations"]["local/bad"]
            self.assertEqual(failure["status"], "READ_FAILED")
            self.assertNotIn("reserved_at", failure)

    def test_spectral_comparison_rejects_wrong_state_and_input_units(self):
        ident = {"sha256": "a" * 64, "unit": "m", "frame": "basic", "entity": "node 2 X",
                 "quantity": "displacement"}
        data = {"frf_identity": {**ident, "unit": "m/N"},
                "input_identity": {**ident, "unit": "N", "quantity": "force", "entity": "node 1 X"},
                "result_identity": ident, "phase": "exp(+iwt)", "convention": "one-sided-per-Hz",
                "frequencies_hz": [1, 3], "input_frequencies_hz": [1, 3],
                "result_frequencies_hz": [1, 3], "frf": [[0, 2], [2, 0]], "input_psd": [2, 2],
                "native_psd": [8, 8], "native_rms": 4, "tolerances": {"psd_abs": 0, "rms_abs": 0, "relative": 0}}
        self.assertEqual(verify_response(data)["status"], "MATCHED")
        self.assertEqual(verify_response({**data, "native_rms": 3})["status"], "DIFFERS")
        for key, other in (("input_frequencies_hz", [1, 4]), ("phase", "unspecified")):
            with self.assertRaises(ValueError):
                verify_response({**data, key: other})
        wrong = deepcopy(data)
        wrong["input_identity"]["unit"] = "kN"
        with self.assertRaises(ValueError):
            verify_response(wrong)


if __name__ == "__main__":
    unittest.main()
