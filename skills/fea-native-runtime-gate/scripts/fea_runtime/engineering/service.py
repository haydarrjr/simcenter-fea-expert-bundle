"""Dispatch a bounded independent check over exact original artifact bytes."""

from dataclasses import asdict
from importlib.util import find_spec

from ..contracts import Blocked, fields, load_json, relative, scoped_path, sha, text


METHODS = {"f06", "nonlinear_deck", "nonlinear_f06", "bdf", "op2", "op4", "mesh",
           "modal_subspace", "tensor", "spectral", "deck_result_reconcile", "mesh_convergence"}


def validate_request(operation):
    args = operation["args"]
    fields(args, ("path", "method"), ("options",))
    if relative(args["path"]) != operation["target"]["path"]:
        raise ValueError("engineering check requires its exact bound artifact")
    method = text(args["method"])
    if method not in METHODS:
        raise Blocked("engineering method has no integrated adapter")
    if "options" in args and type(args["options"]) is not dict:
        raise ValueError("engineering options must be a JSON object")


def execute(root, args):
    path = scoped_path(root, args["path"])
    method = args["method"]
    size = path.stat().st_size
    if size == 0 or size > 32 * 1024 * 1024:
        raise ValueError("engineering input is empty or exceeds the supported byte limit")
    if method == "f06":
        from .solver_linked.f06 import parse_f06

        value = parse_f06(path.read_text(encoding="latin-1"))
        return value.to_dict()
    if method == "nonlinear_deck":
        from ..artifacts import file_identity
        from ..native import deck_parser

        deck = deck_parser().read_deck(path, root=path.parent)
        if deck.solution not in {401, 402}:
            raise ValueError("expected a SOL 401 or SOL 402 deck")
        return {**deck.summary(), **file_identity(path),
                "applicability": "Effective text controls and hashes; physical history needs native evidence"}
    if method == "nonlinear_f06":
        from .nonlinear_diagnostics.core import parse_f06

        result = asdict(parse_f06(path.read_text(encoding="latin-1")))
        return {**result, "applicability": "Original-file observations only; 2612 engineering diagnosis unqualified"}
    if method in {"bdf", "op2", "op4", "mesh"}:
        for dependency in ("numpy", "pyNastran"):
            if find_spec(dependency) is None:
                raise Blocked(f"DEPENDENCY_MISSING: {dependency}")
        from .artifacts import bdf, matrices, op2
        from .artifacts.common import ArtifactLimits, Budget, read_options

        limits = ArtifactLimits()
        raw_options = args.get("options") or {}
        reader_options = {key: value for key, value in raw_options.items() if key != "mesh_scope"}
        options = read_options(reader_options)
        reader = {"bdf": bdf.read_bdf, "op2": op2.read_op2, "op4": matrices.read_op4, "mesh": bdf.read_bdf}[method]
        if method in {"bdf", "mesh"}:
            from ..native import deck_parser

            deck_parser().read_deck(path, root=path.parent)
        result = reader(path, options, limits, Budget(limits))
        if method == "mesh":
            return mesh_metrics(result, args.get("options", {}))
        return result
    data = load_json(path)
    if method == "deck_result_reconcile":
        return reconcile_originals(root, data)
    if method == "mesh_convergence":
        from .mesh_vvuq.core import ConvergencePolicy, Level, StudyIdentity, assess_convergence

        fields(data, ("levels", "policy", "expected_identity"))
        supplied = data["levels"]
        if type(supplied) is not list or not 3 <= len(supplied) <= 16:
            raise ValueError("a convergence assessment requires between 3 and 16 levels")
        levels = tuple(Level(**{**item, "identity": StudyIdentity(**item["identity"])}) for item in supplied)
        return asdict(assess_convergence(levels, ConvergencePolicy(**data["policy"]),
                                         StudyIdentity(**data["expected_identity"])))
    if method == "spectral":
        from .spectral import verify_response

        return verify_response(data)
    if method == "modal_subspace":
        if find_spec("numpy") is None or find_spec("scipy") is None:
            raise Blocked("DEPENDENCY_MISSING: numpy and scipy")
        from .multiphysics.modal import compare_modal_subspaces

        return compare_modal_subspaces(data)
    if method == "tensor":
        from .frames import FramedTensor
        from .tensor_qoi.core import Field, Location, ResultState, evaluate_field

        spec = dict(data)
        spec["location"] = Location(**data["location"])
        spec["tensor"] = FramedTensor(**data["tensor"])
        spec["state"] = ResultState(**data["state"])
        return asdict(evaluate_field(Field(**spec)))
    raise Blocked("unknown verification method")


def reconcile_originals(root, data):
    """Bind exact Siemens deck and OP2 files to the independent identity comparison."""
    from ..artifacts import file_identity
    from ..native import deck_parser

    fields(data, ("deck", "op2", "unit_system", "frame"), ("result_names",))
    if data["unit_system"] not in {"N-m-kg-s", "N-mm-tonne-s"} or data["frame"] != "basic":
        raise ValueError("declare a supported coherent unit system and basic coordinate frame")
    if find_spec("numpy") is None or find_spec("pyNastran") is None:
        raise Blocked("DEPENDENCY_MISSING: numpy and pyNastran")
    from .artifacts.bdf import read_bdf
    from .artifacts.common import ArtifactLimits, Budget, read_options
    from .artifacts.op2 import read_op2
    from .artifacts.reconcile import reconcile_model_results

    limits = ArtifactLimits()
    originals = {}
    for kind in ("deck", "op2"):
        item = data[kind]
        fields(item, ("path", "sha256"))
        path = scoped_path(root, item["path"])
        if path.stat().st_size > limits.max_file_bytes or file_identity(path)["sha256"] != sha(item["sha256"]):
            raise ValueError("engineering source size or hash differs from the declared original")
        originals[kind] = path
    if originals["op2"].suffix.lower() != ".op2":
        raise ValueError("expected a native OP2 result")
    deck_parser().read_deck(originals["deck"], root=originals["deck"].parent)
    reports = []
    for kind, reader in (("deck", read_bdf), ("op2", read_op2)):
        budget = Budget(limits)
        options = {"nastran_dialect": "nx"} if kind == "deck" else {}
        if kind == "op2" and "result_names" in data:
            options = read_options({"result_names": data["result_names"]})
        report = reader(originals[kind], options, limits, budget)
        if file_identity(originals[kind])["sha256"] != data[kind]["sha256"]:
            raise ValueError("original bytes changed during engineering reconciliation")
        reports.append({"payload": report, "bounded_output_complete": not budget.omissions,
                        "source": {"units": data["unit_system"], "frame": data["frame"],
                                   "sha256": data[kind]["sha256"]}})
    return reconcile_model_results(*reports)


def mesh_metrics(report, options):
    from .mesh_vvuq.core import Element, MeshPolicy, Node, assess_mesh
    from .units import convert

    context = options.get("mesh_scope")
    fields(context, ("owner", "coordinate_unit", "policy"), ("reference_normal",))
    owner = text(context["owner"])
    values = report["nodes"]
    labels, coordinates = values["labels"], values["xyz_basic"]
    if (labels.get("complete") is not True or coordinates.get("complete") is not True
            or values["count"] != len(labels["values"]) or values["unresolved_basic_coordinates"]):
        raise ValueError("mesh analysis requires complete coordinates resolved to the basic frame")
    nodes = tuple(Node(str(label), tuple(convert(x, context["coordinate_unit"], "m", "length") for x in xyz), owner)
                  for label, xyz in zip(labels["values"], coordinates["values"], strict=True))
    cells = []
    for element in report["elements"]:
        if element["type"] == "CTETRA" and len(element["node_labels"]) == 4:
            family, normal = "TET4", None
        elif element["type"] == "CTRIA3" and len(element["node_labels"]) == 3:
            family, normal = "TRI3", context.get("reference_normal")
        else:
            raise Blocked("independent mesh metrics are limited to linear TET4 or TRI3")
        cells.append(Element(str(element["label"]), family, tuple(map(str, element["node_labels"])), owner,
                             str(element["property_id"]), tuple(normal) if normal is not None else None))
    if not cells or report.get("element_count") != len(cells):
        raise ValueError("mesh analysis requires complete supported element coverage")
    properties = frozenset((owner, str(item["id"])) for item in report["properties"])
    return asdict(assess_mesh(nodes, tuple(cells), MeshPolicy(**context["policy"]), properties, frozenset()))
