"""Deterministic local policy overlays; upstream Siemens capture stays immutable.

No upstream payload is embedded here. Policy version and source/packaged digests
are returned in build evidence. Transform only hash-validated integration input.
"""
from __future__ import annotations
import re

POLICY_VERSION = 'fea-integration-safety-v1'
START = '<!-- FEA integration safety v1 -->'
END = '<!-- End FEA integration safety v1 -->'
POLICY = '''## FEA integration safety contract (overrides conflicting legacy guidance)

- Discover the current tool catalog and exact input schemas before calling tools.
  A connected server need not expose every tool from older documentation.
  If a call fails, check dc_connection_status first. Retry bounded read-only
  discovery after recovery; never replay an uncertain mutation blindly.
- Documentation: use documentation-search-tool only when currently advertised.
  If absent after connectivity recovery, route to the advertised Product Support
  search tool using its current schema and version-specific Siemens sources.
  If neither route is available, report BLOCKED_BY_OFFICIAL_MCP_CAPABILITY /
  NOT_RUN; do not invent syntax, citations, or answers from memory.
- Pagination: send PAGE or CURSOR only if that exact parameter exists in the
  current tool input schema. A response mentioning hasMoreSchema/hasMoreData
  does not authorize unsupported arguments. If continuation is unavailable,
  report the read as PARTIAL with the unresolved scope; do not claim completeness.
- Journal sandbox: import only NXOpen modules. Never import sys or another
  standard-library module. Use sys.argv only when the current journal tool
  explicitly supplies sys; otherwise stop and verify the supported entry point.
  Keep main(args), session acquisition and builder cleanup requirements.
- A sandbox SUCCESS, exit code zero, or no captured stdout is not observable
  proof that statements, assertions, or error paths executed. Report execution
  transport status separately from observable test evidence. Without inspectable
  output/readback, the claimed behavior remains UNVERIFIED, not tested-correct.
- Action verbs alone do not authorize an ambiguous target, save, solve, or
  overwrite. Live changes require explicit user intent, an identified owned
  working copy, current advertised capability and applicable host approval.
  After a change, obtain independent native readback tied to model identity.
- Mesh metrics: null, zero, placeholder, unavailable or uncomputed values are
  UNVERIFIED unless the metric definition, element applicability and computation
  status establish their meaning. Never convert missing evidence into PASS.
  Free edges may be intentional shell boundaries; interpret topology explicitly.
  Use project/solver/element-specific documented thresholds, not universal limits.
  Shape quality alone does not establish QoI mesh convergence or solve acceptance.
'''


def transform(name: str, data: bytes) -> bytes:
    """Idempotent frontmatter-preserving policy injection for official skill files."""
    if not name.startswith('skills/') or not name.endswith('/SKILL.md'):
        return data
    text = data.decode('utf-8')
    if START in text:
        return data
    newline = '\r\n' if '\r\n' in text else '\n'
    text = text.replace('\r\n', '\n')
    # Remove the contradictory standard-library import, not the provided sys use.
    text = re.sub(r'(?m)^    import sys\n', '', text)
    # Gate legacy schema examples at the point of use as well as in the contract.
    text = text.replace('optional `PAGE`', 'optional `PAGE` only if advertised by the current input schema')
    text = text.replace('optional `CURSOR`', 'optional `CURSOR` only if advertised by the current input schema')
    text = text.replace('call again with `PAGE`', 'if the current input schema supports PAGE, call again with `PAGE`')
    text = text.replace('call again with `CURSOR`', 'if the current input schema supports CURSOR, call again with `CURSOR`')
    block = START + '\n' + POLICY + END + '\n\n'
    fm = re.match(r'\A---\n.*?\n---\n', text, re.S)
    if not fm:
        raise RuntimeError('Official skill lacks closed frontmatter: ' + name)
    text = text[:fm.end()] + '\n' + block + text[fm.end():].lstrip('\n')
    return text.replace('\n', newline).encode('utf-8')


def transform_recipe(name: str, data: bytes) -> bytes:
    """Inject the same precedence contract inside the official YAML instructions."""
    if not name.startswith('recipes/'):
        return data
    text = data.decode('utf-8')
    marker = '  FEA integration safety contract v1 takes precedence over legacy instructions.\n'
    if marker in text:
        return data
    newline = '\r\n' if '\r\n' in text else '\n'
    text = text.replace('\r\n', '\n')
    anchor = 'instructions: |\n'
    if text.count(anchor) != 1:
        raise RuntimeError('Cannot locate unique recipe instructions: ' + name)
    policy = marker + '\n'.join('  ' + line if line else '' for line in POLICY.splitlines()) + '\n\n'
    text = text.replace(anchor, anchor + policy, 1)
    # Make the fallback actually reachable from the official documentation agents.
    if 'name: Designcenter Open' in text and 'name: Product Support' not in text:
        text += '\n  - type: ref\n    name: Product Support\n'
    return text.replace('\n', newline).encode('utf-8')
