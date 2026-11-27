"""Operation v1 normalization, capability discovery and witness validation."""

from datetime import datetime, timezone
import math
from pathlib import Path, PureWindowsPath
import re
import stat
from time import monotonic, sleep


class Blocked(ValueError):
    """Availability or recovery prevents dispatch."""


class Denied(ValueError):
    """Dispatch lacks the required authority."""


SHA = re.compile(r"[0-9a-f]{64}")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}")
MAX_JSON = 8 * 1024 * 1024


def load_json(path, *, max_bytes=MAX_JSON):
    from fea_controller import strict_json_load

    return strict_json_load(path, max_bytes)


def fields(value, required, optional=()):
    if type(value) is not dict or not set(required) <= value.keys() <= set(required) | set(optional):
        raise ValueError(f"expected fields {', '.join(required)}; optional: {', '.join(optional)}")


def text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 4096:
        raise ValueError("a nonempty string within 4096 characters is required")
    return value


def identifier(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError("invalid identifier")
    return value


def sha(value):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise ValueError("invalid SHA-256 digest")
    return value


def stamp(value):
    result = datetime.fromisoformat(text(value))
    if result.tzinfo is None:
        raise ValueError("time must carry a UTC offset")
    return result


def fresh_at(after):
    limit = monotonic() + 1
    threshold = stamp(after)
    current = datetime.now(timezone.utc)
    while current <= threshold and monotonic() < limit:
        sleep(.001)
        current = datetime.now(timezone.utc)
    if current <= threshold:
        raise Blocked("unable to timestamp fresh local evidence after response")
    return current.isoformat()


def relative(value):
    text(value)
    parts = value.split("/")
    if any(part in {"", ".", ".."} or part.rstrip(" .") != part
           or re.search(r'[\\:*?"<>|\x00-\x1f]', part) or PureWindowsPath(part).is_reserved()
           for part in parts):
        raise ValueError("expected a canonical workspace-relative path")
    return value


def scoped_path(root, name, *, exists=True):
    root = Path(root)
    current = root
    for part in relative(name).split("/"):
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("aliases and reparse points are outside the runtime path contract")
    resolved = current.resolve(strict=exists)
    if not resolved.is_relative_to(root):
        raise ValueError("path escapes runtime root")
    return resolved


def _cap(owner, backend, target, effect, args, outputs, profile=None, tools=()):
    return dict(owner=owner, backend=backend, target=target, effect=effect, inputs=args,
                outputs=outputs, profile=profile, tools=tools,
                applicability="Current advertised profile/build and matching evidence",
                resource=target, verification="Independent scoped witness",
                qualification="UNVERIFIED", qualification_refs=[])


CAPABILITIES = {
    "sc3d.model.inspect": _cap("fea-sc3d-tool-routing", "host", "sc3d", "PURE_READ",
                               "Current tool schema", "Observed part or mesh data", "simcenter3d",
                               ("part-info-tool", "mesh-info-tool")),
    "sc3d.cad.inspect": _cap("designcenter-open-model-data-read", "host", "sc3d", "PURE_READ",
                             "Current tool schema", "Observed CAD model data", "designcenter",
                             ("read-model-data",)),
    "sc3d.mesh.generate": _cap("fea-sc3d-tool-routing", "host", "sc3d", "CAE_MUTATION",
                               "Current tool schema and qualified owned selection", "Mesh readback",
                               "simcenter3d", ("surface-mesh-generation-tool", "solid-mesh-generation-tool")),
    "sc3d.deck.export": _cap("designcenter-open-journal-authoring", "host", "sc3d", "DECK_EXPORT",
                             "Existing exact 2612 SOL103 export template", "Fresh deck and solution witness",
                             "designcenter", ("dcopen-execute-tool",)),
    "sc3d.journal.qualified": _cap("designcenter-open-journal-authoring", "host", "sc3d", "CAE_MUTATION",
                                   "Individually reviewed exact NXOpen journal", "Native readback",
                                   "designcenter", ("dcopen-execute-tool",)),
    "sc3d.model.import": _cap("designcenter-open-journal-authoring", "local", "file", "FILE_MUTATION",
                              "Owned supported deck, FEM/SIM paths, optional exact solution rename",
                              "Translator receipt, saved FEM/SIM and fresh-process inventory"),
    "sc3d.model.read_saved": _cap("fea-native-runtime-gate", "local", "file", "PURE_READ",
                                  "Owned SIM and linked FEM", "Isolated native inventory"),
    "sc3d.model.persist": _cap("fea-native-runtime-gate", "local", "file", "DECK_EXPORT",
                                "Owned batch files and an exact native solution",
                                "Fresh effective deck and fresh-process reopen"),
    "nastran.deck.inspect": _cap("simcenter-nastran", "local", "file", "PURE_READ",
                                  "{deck, input_scope}", "Deck closure and effective controls"),
    "nastran.artifact.verify": _cap("fea-acceptance-verifier", "local", "file", "PURE_READ",
                                    "{path, method, options}", "Bounded independent numerical evidence"),
    "nastran.job.submit": _cap("simcenter-nastran", "local", "nastran", "SOLVER_SUBMIT",
                                "{deck, input_scope, job_dir, sequence, solution_monitor, subcases, states, outputs}",
                                "Native job receipt and result artifact references"),
    "batchpost.result.catalog": _cap("batchpost-actions", "host", "batchpost", "PURE_READ",
                                     "Current list schema", "Native case/state/type catalog", "batchpost", ("list",)),
    "batchpost.result.open": _cap("batchpost-actions", "host", "batchpost", "WORKER_MUTATION",
                                  "{file}", "Native opened result identity", "batchpost", ("open",)),
    "batchpost.result.close": _cap("batchpost-actions", "host", "batchpost", "WORKER_MUTATION",
                                   "Current close schema", "Native closed result state", "batchpost", ("close",)),
    "batchpost.result.extract": _cap("batchpost-actions", "host", "batchpost", "FILE_MUTATION",
                                     "Current tool schema with exact catalog selection", "Native export and covered field",
                                     "batchpost", ("contour", "graphi")),
}


TARGETS = {
    "sc3d": (("host", "native_process", "release", "work", "display", "owner", "occurrence", "model"),
             ("revision", "precondition")),
    "nastran": (("release", "executable_sha256", "job_dir", "job_id", "deck_digest"), ()),
    "batchpost": (("host", "worker", "release", "result_sha256"), ("catalog_digest",)),
    "file": (("path", "sha256", "schema"), ()),
}


def target_identity(target):
    kind = target.get("kind")
    if kind not in TARGETS:
        raise ValueError("unknown target variant")
    required, optional = TARGETS[kind]
    fields(target, ("kind", *required), optional)
    for key in required:
        text(target[key])
        if key in {"sha256", "result_sha256", "executable_sha256", "deck_digest"}:
            sha(target[key])
        if key in {"path", "job_dir"}:
            relative(target[key])
    if kind == "sc3d":
        if ("revision" in target) == ("precondition" in target):
            raise ValueError("supply a native revision or a scoped precondition witness")
        if "revision" in target:
            text(target["revision"])
        else:
            sha(target["precondition"])
    if "catalog_digest" in target:
        sha(target["catalog_digest"])
    return {key: target[key] for key in ("kind", *required)}


def resource_keys(target):
    from fea_controller import digest

    kind = target["kind"]
    if kind == "sc3d":
        return [digest([kind, target["host"], target["native_process"]])]
    if kind == "batchpost":
        return [digest([kind, target["host"], target["worker"]])]
    if kind == "nastran":
        return [digest([kind, "directory", target["job_dir"].casefold()]),
                digest([kind, "job", target["job_id"].casefold()])]
    return []


def match(actual, expected):
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(match(actual[key], val) for key, val in expected.items())
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(match(a, b) for a, b in zip(actual, expected))
    return actual == expected


def number(value):
    if type(value) not in {int, float} or abs(value) > 1.7976931348623157e308 or not math.isfinite(value):
        raise ValueError("finite numeric witness required")
    return value


def predicates(items):
    if type(items) is not dict or not items:
        raise ValueError("nonempty independent witness predicates required")
    for predicate in items.values():
        if type(predicate) is not dict:
            raise ValueError("invalid witness predicate")
        if predicate.get("op") == "exact":
            fields(predicate, ("op", "value"))
        elif predicate.get("op") == "numeric":
            fields(predicate, ("op", "value", "abs_tol", "rel_tol", "units", "dimension", "frame"))
            number(predicate["value"])
            if min(number(predicate["abs_tol"]), number(predicate["rel_tol"])) < 0:
                raise ValueError("tolerances must be nonnegative")
            for key in ("units", "dimension", "frame"):
                text(predicate[key])
        else:
            raise ValueError("unsupported witness predicate")


def satisfies(items, witnesses):
    for name, predicate in items.items():
        if name not in witnesses:
            return False
        actual = witnesses[name]
        if predicate["op"] == "exact":
            if not match(actual, predicate["value"]):
                return False
            continue
        try:
            fields(actual, ("value", "units", "dimension", "frame"))
            value = number(actual["value"])
        except ValueError:
            return False
        if not all(actual[key] == predicate[key] for key in ("units", "dimension", "frame")):
            return False
        reference = predicate["value"]
        difference = abs(value - reference)
        tolerance = predicate["abs_tol"] + predicate["rel_tol"] * abs(reference)
        if not math.isfinite(difference) or not math.isfinite(tolerance) or difference > tolerance:
            return False
    return True


def before(value, timestamp):
    return stamp(value) <= stamp(timestamp) <= datetime.now(timezone.utc)


def validate(operation, binding):
    from fea_controller import digest

    fields(operation, ("version", "run_id", "operation_id", "capability", "target",
                       "args", "dependencies", "expected", "output_scope"),
           ("baseline", "deadline", "authorization_ref", "input_artifacts"))
    if type(operation["version"]) is not int or operation["version"] != 1:
        raise ValueError("unsupported operation version")
    fields(operation["args"], (), operation["args"].keys() if isinstance(operation["args"], dict) else ())
    name = identifier(operation["operation_id"])
    identifier(operation["run_id"])
    target = operation["target"]
    if not isinstance(target, dict):
        raise ValueError("target must be a JSON object")
    target_identity(target)
    desc = CAPABILITIES.get(text(operation["capability"]))
    if desc is None or desc["backend"] == "unavailable":
        raise Blocked("capability has no admitted execution binding")
    if desc["target"] != target["kind"]:
        raise ValueError("wrong target variant for capability")
    if operation["output_scope"] != ".":
        relative(operation["output_scope"])
    depends = operation["dependencies"]
    if type(depends) is not list or len(depends) > 256 or name in depends:
        raise ValueError("invalid or cyclic dependency list")
    if len(set(map(identifier, depends))) != len(depends):
        raise ValueError("duplicate dependencies")
    inputs = operation.get("input_artifacts", [])
    if type(inputs) is not list or len(inputs) > 256 or len(set(map(sha, inputs))) != len(inputs):
        raise ValueError("invalid artifact input references")
    predicates(operation["expected"])
    if desc["effect"] != "PURE_READ":
        predicates(operation.get("baseline"))
        if match(operation["baseline"], operation["expected"]):
            raise ValueError("effect requires distinguishable baseline and expected witnesses")
        text(operation.get("authorization_ref"))
        if "deadline" not in operation:
            raise ValueError("effect requires a dispatch deadline")
    if "deadline" in operation:
        stamp(operation["deadline"])
    fields(binding, ("target", "evidence_ref", "observed_at"),
           ("profile", "tool", "catalog", "catalog_digest", "descriptor_digest",
            "fem", "solution_tag", "qualification"))
    if not match(binding["target"], target):
        raise ValueError("binding target differs from operation")
    text(binding["evidence_ref"])
    if stamp(binding["observed_at"]) > datetime.now(timezone.utc):
        raise ValueError("binding witness is in the future")
    if desc["backend"] == "host":
        from .host import validate_host

        validate_host(operation, binding, desc)
    else:
        from .native import validate_local

        validate_local(operation)
    resources = resource_keys(target)
    if target["kind"] == "file" and desc["effect"] != "PURE_READ":
        resources = [digest(["owned-file-effects"])]
    return {"request_digest": digest(operation), "binding_digest": digest(binding),
            "effect": desc["effect"], "resources": resources}


def authorize(operation, validated, authority):
    if validated["effect"] == "PURE_READ":
        return
    expected = {"ref": operation["authorization_ref"], "request_digest": validated["request_digest"],
                "effect": validated["effect"], "binding_digest": validated["binding_digest"]}
    if not match(authority, expected):
        raise Denied("trusted caller grant must match the exact effect, binding and request digest")
