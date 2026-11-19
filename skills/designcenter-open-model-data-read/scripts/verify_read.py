"""Validate captured official Designcenter MCP structure and model-data reads."""
import argparse
from hashlib import sha256
import json
from pathlib import Path


def checksum(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             allow_nan=False).encode('utf-8')).hexdigest()


def payload(capture):
    reply = capture['reply']
    if 'error' in reply or 'transportError' in reply:
        raise ValueError('MCP transport failed')
    result = reply.get('result', reply)
    if result.get('isError'):
        raise ValueError('MCP reported an error')
    body = result.get('structuredContent')
    if body is None:
        blocks = [c['text'] for c in result.get('content', []) if c.get('type') == 'text']
        if len(blocks) != 1:
            raise ValueError('expected one structured Siemens response')
        body = json.loads(blocks[0])
    if body.get('toolExecutionStatus') != 'ToolExecutionStatus::Completed':
        raise ValueError('Siemens did not complete the model read')
    response = body.get('toolResponse')
    if not isinstance(response, dict) or response.get('error'):
        raise ValueError(f'Siemens model read failed: {response}')
    return response


def capture_pages(captures, name, parameter, flag, next_value):
    responses = []
    cursor = None
    seen = set()
    original_arguments = None
    for capture in captures:
        request = capture['request']
        args = dict(request['arguments'])
        if request['name'] != name or args.pop(parameter, None) != cursor:
            raise ValueError(f'{name} request does not match the returned continuation')
        if responses and (cursor is None or args != original_arguments):
            raise ValueError(f'{name} changed its query or continued after the terminal page')
        original_arguments = args
        response = payload(capture)
        responses.append(response)
        more = response.get(flag)
        if more is not None and type(more) is not bool:
            raise ValueError(f'{name} returned an invalid continuation flag')
        cursor = response.get(next_value) if more and next_value else None
        if more and cursor is not None:
            cursor_digest = checksum(cursor)
            if cursor_digest in seen:
                raise ValueError(f'{name} returned a repeated continuation')
            seen.add(cursor_digest)
    if not responses:
        raise ValueError(f'{name} has no captured pages')
    return responses, original_arguments, bool(responses[-1].get(flag))


def verify_read(structure, data, *, expected_part=None, data_cursor_field=None):
    registry, _, schema_partial = capture_pages(
        structure, 'explore-model-structure', 'PAGE', 'hasMoreSchema', 'nextPageToCall')
    pages, arguments, data_partial = capture_pages(
        data, 'read-model-data', 'CURSOR', 'hasMoreData', data_cursor_field)
    fields = {}
    for page in registry:
        for domain in page['domain']:
            for entity in domain['entities']:
                key = domain['name'], entity['name']
                allowed = fields.setdefault(key, {'scalar_properties': set(), 'relational_properties': set()})
                for typ, values in allowed.items():
                    values.update(prop['name'] for prop in entity.get(typ, []))
    query = json.loads(arguments['schemaForExtraction'])
    requested = {}
    for domain in query['domain']:
        for entity in domain['entities']:
            key = domain['name'], entity['name']
            if key not in fields or entity['name'] in requested:
                raise ValueError(f'unknown or ambiguous extraction entity: {key}')
            required = set()
            for typ, allowed in fields[key].items():
                selected = set(entity.get(typ, []))
                if not selected <= allowed:
                    raise ValueError(f'extraction property absent from discovered schema: {key}')
                required.update(selected)
            requested[entity['name']] = required
    if not requested:
        raise ValueError('no entities requested')
    contexts = {(page.get('DesigncenterVersion'), page.get('currentApplication'), page.get('partUnits'))
                for page in pages}
    if len(contexts) != 1:
        raise ValueError('model-read application, release or units changed across pages')
    release, application, units = contexts.pop()
    records = {name: [] for name in requested}
    for page in pages:
        for name, rows in page['data'].items():
            if name in records:
                if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                    raise ValueError(f'expected object records for {name}')
                records[name].extend(rows)
    active = sorted({row['filePath'] for row in records.get('PartInfo', [])
                     if row.get('isWorkPart') is True and row.get('filePath')})
    if len(active) > 1:
        raise ValueError('model read reports multiple active work parts')
    if expected_part and active and active[0].replace('\\', '/').casefold() != expected_part.replace('\\', '/').casefold():
        raise ValueError('model read belongs to a different active part')
    missing = {name: sorted({field for row in rows for field in requested[name]
                             if field not in row or row[field] is None})
               for name, rows in records.items()}
    absent = sorted(name for name in requested if all(name not in page['data'] for page in pages))
    partial = schema_partial or data_partial or not all((release, application, units)) or (
        expected_part and not active) or absent or any(missing.values())
    return {'status': 'PARTIAL' if partial else 'VERIFIED', 'release': release,
            'application': application, 'units': units, 'active_part': active[0] if active else None,
            'schema_pages': len(registry), 'data_pages': len(pages),
            'schema_has_more': schema_partial, 'data_has_more': data_partial,
            'missing_fields': missing, 'absent_entities': absent, 'records': records,
            'capture_sha256': [checksum(item) for item in [*structure, *data]]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--structure', nargs='+', type=Path, required=True)
    parser.add_argument('--data', nargs='+', type=Path, required=True)
    parser.add_argument('--expected-part')
    parser.add_argument('--data-cursor-field', help='Exact response field advertised for data continuation')
    cli = parser.parse_args()
    captures = lambda files: [json.loads(path.read_text(encoding='utf-8-sig')) for path in files]
    print(json.dumps(verify_read(captures(cli.structure), captures(cli.data),
                                expected_part=cli.expected_part,
                                data_cursor_field=cli.data_cursor_field), ensure_ascii=False, indent=2))
