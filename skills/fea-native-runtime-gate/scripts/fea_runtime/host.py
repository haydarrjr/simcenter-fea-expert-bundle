"""Validation at the boundary of an existing host-managed native profile."""

from pathlib import PureWindowsPath
import re

from .contracts import Blocked, fields, match, relative, sha, text


SCHEMAS = {
    "https://json-schema.org/draft/2020-12/schema": "Draft202012Validator",
    "http://json-schema.org/draft-07/schema": "Draft7Validator",
}
SCHEMA_MAPS = {"properties", "patternProperties", "dependentSchemas"}
SCHEMA_LISTS = {"allOf", "anyOf", "oneOf", "prefixItems"}
SCHEMA_CHILDREN = {"items", "additionalItems", "additionalProperties", "propertyNames",
                   "contains", "not", "if", "then", "else", "unevaluatedProperties", "unevaluatedItems"}
SCHEMA_VALUES = {"$schema", "type", "enum", "const", "required", "minimum", "maximum",
                 "exclusiveMinimum", "exclusiveMaximum", "multipleOf", "minLength", "maxLength",
                 "pattern", "minItems", "maxItems", "uniqueItems", "minProperties", "maxProperties",
                 "minContains", "maxContains", "dependentRequired", "title", "description", "default",
                 "examples", "deprecated", "readOnly", "writeOnly", "$comment"}


def schema_tree(schema, supported, definitions, group, visiting=()):
    if type(schema) is bool:
        return
    if type(schema) is not dict or any(key not in supported for key in schema):
        raise Blocked("advertised schema uses an unsupported keyword")
    if "$ref" in schema:
        ref = schema["$ref"]
        match = re.fullmatch(r"#/" + re.escape(group) + r"/([A-Za-z0-9_.-]+)", ref)
        if not match or match[1] not in definitions or match[1] in visiting:
            raise Blocked("advertised schema reference is external, unresolved or cyclic")
        schema_tree(definitions[match[1]], supported, definitions, group, (*visiting, match[1]))
    for key in schema.keys() & SCHEMA_MAPS:
        for child in schema[key].values():
            schema_tree(child, supported, definitions, group, visiting)
    for key in schema.keys() & SCHEMA_LISTS:
        for child in schema[key]:
            schema_tree(child, supported, definitions, group, visiting)
    for key in schema.keys() & SCHEMA_CHILDREN:
        value = schema[key]
        for child in value if type(value) is list else [value]:
            schema_tree(child, supported, definitions, group, visiting)


def check_schema(schema, args):
    try:
        import jsonschema
        from referencing import Registry
    except ImportError as exc:
        raise Blocked("DEPENDENCY_MISSING: install the pinned host schema dependencies") from exc
    dialect = schema.get("$schema", next(iter(SCHEMAS))).rstrip("#")
    if dialect not in SCHEMAS:
        raise Blocked("advertised schema dialect is unsupported")
    validator = getattr(jsonschema, SCHEMAS[dialect])
    supported = (SCHEMA_MAPS | SCHEMA_LISTS | SCHEMA_CHILDREN | SCHEMA_VALUES)
    supported &= set(validator.VALIDATORS) | {"$schema", "title", "description", "default",
                                             "examples", "deprecated", "readOnly", "writeOnly", "$comment"}
    group = "definitions" if SCHEMAS[dialect] == "Draft7Validator" else "$defs"
    definitions = schema.get(group, {})
    if not isinstance(definitions, dict):
        raise Blocked("advertised schema definitions must be an object")
    try:
        validator.check_schema(schema)
        for name, node in definitions.items():
            schema_tree(node, supported | {"$ref"}, definitions, group, (name,))
        schema_tree(schema, supported | {group, "$ref"}, definitions, group)
        validator(schema, registry=Registry()).validate(args)
    except jsonschema.exceptions.SchemaError as exc:
        raise Blocked(f"malformed advertised tool schema: {exc.message}") from exc
    except jsonschema.exceptions.ValidationError as exc:
        path = "/".join(str(part) for part in exc.absolute_path)
        raise ValueError(f"native arguments violate the advertised schema at /{path}: {exc.validator}") from exc


def _single(arguments, key):
    value = arguments.get(key)
    fields(value, ("type", "value"))
    if value["type"] != "single":
        raise ValueError(f"{key} must select exactly one observed value")
    return value["value"]


def checked_selection(args, qualification, target):
    from fea_controller import digest

    catalog = qualification.get("result_catalog")
    if not isinstance(catalog, dict) or digest(catalog) != target.get("catalog_digest"):
        raise ValueError("result selection requires the exact observed worker catalog")
    selection = qualification.get("selection")
    fields(selection, ("case", "state", "result", "component", "position", "labels", "entity",
                       "units", "frame", "convention", "owner"))
    for key in ("result", "component", "position", "units", "frame", "convention", "owner"):
        text(selection[key])
    if selection["convention"] != "real":
        raise Blocked("structured contour requires verified real-valued coverage")
    if selection["position"] not in {"Nodal", "Elemental"}:
        raise Blocked("structured contour currently requires nodal or elemental coverage")
    entity = selection["entity"]
    if entity != {"Nodal": "node_ids", "Elemental": "element_ids"}[selection["position"]]:
        raise ValueError("entity type does not match the requested field position")
    labels = selection["labels"]
    if (not isinstance(labels, list) or not labels or len(labels) > 10000
            or any(type(label) is not int or label < 1 for label in labels)
            or sorted(set(labels)) != labels):
        raise ValueError("labels must be unique ordered native positive integers")
    case, state = (_single(args, key) for key in ("loadcase_index", "iteration_index"))
    if any(type(index) is not int or index < 1 for index in (case, state)):
        raise ValueError("case and state must be positive native indexes")
    if not match([case, state], [selection["case"], selection["state"]]):
        raise ValueError("argument case or state does not match the selection")
    try:
        cases = [entry for entry in catalog["loadcases"] if entry["index"] == case]
        [case_entry] = cases
        [iteration] = [entry for entry in case_entry["iterations"] if entry["index"] == state]
        [result] = [entry for entry in iteration["result_types"] if entry["unique_name"] == selection["result"]]
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError("case, state or unique result is absent or ambiguous in the catalog") from exc
    if (not selection["result"].endswith(f"[{selection['position']}]")
            or selection["component"] not in result["components"]
            or _single(args, "resulttype") != result["name"]
            or _single(args, "component") != selection["component"]
            or _single(args, "unit") != selection["units"]
            or args.get(entity) != ",".join(map(str, labels))):
        raise ValueError("native arguments do not match the exact observed result selection")
    fields(args, ("loadcase_index", "iteration_index", "resulttype", "component", "unit", "to", entity))
    _single(args, "to")


def validate_host(operation, binding, descriptor):
    from fea_controller import digest, export_journal, normalize_journal

    required = ("profile", "tool", "catalog", "catalog_digest", "descriptor_digest")
    if any(key not in binding for key in required):
        raise Blocked("a current advertised host catalog and exact tool binding are required")
    catalog = binding["catalog"]
    if type(catalog) is not list or len(catalog) > 256 or any(type(item) is not dict for item in catalog):
        raise ValueError("invalid host catalog")
    if digest(catalog) != binding["catalog_digest"] or binding["profile"] != descriptor["profile"]:
        raise ValueError("host profile or catalog digest mismatch")
    tool = binding["tool"]
    if tool not in descriptor["tools"]:
        raise Blocked("tool is outside the qualified semantic route")
    advertised = [item for item in catalog if item.get("name") == tool]
    if len(advertised) != 1 or digest(advertised[0]) != binding["descriptor_digest"]:
        raise Blocked("current tool descriptor is absent, ambiguous or changed")
    schema = advertised[0].get("inputSchema")
    if not isinstance(schema, dict):
        raise Blocked("current tool has no supported object input schema")
    if "$schema" in schema and not isinstance(schema["$schema"], str):
        raise Blocked("invalid advertised schema dialect")
    args, target = operation["args"], operation["target"]
    check_schema(schema, args)
    capability = operation["capability"]
    if descriptor["effect"] == "PURE_READ":
        return
    qualification = binding.get("qualification")
    if not isinstance(qualification, dict):
        raise Blocked("effect requires target-specific native qualification evidence")
    if (qualification.get("release") != target["release"]
            or qualification.get("descriptor_digest") != binding["descriptor_digest"]
            or qualification.get("capability") != capability
            or not qualification.get("evidence_ref")):
        raise Blocked("qualification does not bind this release, capability and descriptor")
    if target["kind"] == "batchpost":
        if qualification.get("owned_worker") != target["worker"]:
            raise Blocked("BatchPost effect requires a task-owned worker")
        if capability == "batchpost.result.open":
            fields(args, ("file",))
            relative(qualification.get("result_path"))
        elif capability == "batchpost.result.close":
            fields(args, ())
            if qualification.get("opened_result_sha256") != target["result_sha256"]:
                raise Blocked("close requires evidence of the exact task-owned open result")
        elif tool == "contour":
            checked_selection(args, qualification, target)
        else:
            raise Blocked("structured graph admission requires independently qualified state coverage")
    elif capability == "sc3d.deck.export":
        fields(args, ("python_code",))
        expected_source = export_journal(target, binding.get("fem"), binding.get("solution_tag"))
        if args["python_code"] != expected_source:
            raise ValueError("only the existing exact Siemens export template is admitted")
        before, after = operation["baseline"], operation["expected"]
        try:
            deck = PureWindowsPath(after["deck_path"]["value"])
            valid = (all(before[key]["op"] == "exact" for key in
                         ("deck_path", "deck_present", "original_solution_signature"))
                     and all(after[key]["op"] == "exact" for key in
                             ("deck_path", "deck_present", "export_finished", "deck_qualified",
                              "original_solution_signature"))
                     and match(before["deck_path"], after["deck_path"])
                     and deck.parent == PureWindowsPath(target["model"]).parent
                     and deck.suffix.lower() in {".dat", ".bdf", ".nas"}
                     and before["deck_present"]["value"] is False
                     and after["deck_present"]["value"] is True
                     and after["export_finished"]["value"] is True
                     and after["deck_qualified"]["value"] is True
                     and bool(before["original_solution_signature"]["value"])
                     and match(before["original_solution_signature"], after["original_solution_signature"]))
        except (KeyError, TypeError):
            valid = False
        if not valid:
            raise ValueError("export needs predeclared unmodified solution and fresh effective deck witnesses")
    elif capability == "sc3d.journal.qualified":
        fields(args, ("python_code",))
        source = normalize_journal(args["python_code"])
        if (source != args["python_code"] or sha(qualification.get("source_digest")) != digest(source)
                or qualification.get("sandbox_reviewed") is not True
                or not qualification.get("installed_member_evidence")):
            raise Blocked("exact normalized journal approval and installed member evidence required")
