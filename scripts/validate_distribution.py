"""Offline source/package contract for Simcenter 3D FEA Expert; never operates a CAE/CAD host."""
import json
from pathlib import Path
import re
import tomllib
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SUFFIXES = {'.md', '.py', '.mjs', '.json', '.yaml', '.yml', '.txt', '.toml', '.xsd'}
EXPECTED_SKILLS = 40
PORTABLE_MANIFEST = 'plugin.json'
CODEX_MARKETPLACE = '.agents/plugins/marketplace.json'
COPILOT_MARKETPLACE = '.github/plugin/marketplace.json'
PLUGIN_METADATA = (PORTABLE_MANIFEST, CODEX_MARKETPLACE, COPILOT_MARKETPLACE)
PLUGIN_SCHEMA = 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'
MODEL_EXAMPLE = re.compile(
    r'\b(?:AO_(?:Aeroelastic|GFEM)|Filter_14LCs|MoS_14_LCs|'
    r'Company_MarginOfSafety_Template|NFRCompatModule|P00[1-9])\b', re.I
)
EXPECTED_SUBRECIPES = [
    'fea-model-inspector',
    'fea-journal-author',
    'fea-solver-diagnostics',
    'fea-results-post',
    'fea-verifier',
    'product-support-agent',
]


def missing_recipe_skills(instructions, names):
    refs = re.findall(r'`((?:fea|designcenter-open|simcenter|nastran-sol401)-[a-z0-9-]+|batchpost-actions)`',
                      instructions)
    return set(refs) - set(names) - set(EXPECTED_SUBRECIPES)


def distribution_files(root=ROOT):
    selected = []
    for name in [*PLUGIN_METADATA, '.sim-ai-agents.toml', 'README.md', 'RELEASE_NOTES.md',
                 'LICENSE', 'requirements-test.txt', 'recipes', 'skills', 'docs', 'fea-workflow.md',
                 'com.github.copilot', 'integrations',
                 'scripts', 'tests']:
        path = root / name
        if not path.exists():
            continue
        candidates = path.rglob('*') if path.is_dir() else [path]
        for p in candidates:
            if p.is_symlink():
                raise ValueError('symlink in distribution: ' + str(p))
            if '__pycache__' in p.parts:
                continue
            if p.is_file():
                if p.suffix.lower() not in ALLOWED_SUFFIXES and not p.name.startswith('LICENSE'):
                    raise ValueError('unexpected artifact: ' + str(p))
                selected.append(p)
    return sorted(selected)


def validate(root=ROOT):
    count = 0
    def check(condition, message):
        nonlocal count
        count += 1
        if not condition:
            raise ValueError(message)

    skills = sorted((root / 'skills').glob('*/SKILL.md'))
    check(len(skills) == EXPECTED_SKILLS, f'expected {EXPECTED_SKILLS} canonical skills, found {len(skills)}')
    yaml = YAML(typ='safe')
    for p in skills:
        text = p.read_text(encoding='utf-8')
        fields = yaml.load(text.split('---', 2)[1])
        check(fields['name'] == p.parent.name and bool(fields.get('description')), 'invalid skill frontmatter in ' + str(p))
        check(fields.get('metadata', {}).get('copyright') == 'Unpublished work. Copyright 2026 Siemens', 'missing ADR-086 copyright metadata in ' + str(p))

    recipe = yaml.load((root / 'recipes/fea-expert-agent.yaml').read_text(encoding='utf-8'))
    skill_names = {p.parent.name for p in skills}
    plugin, codex_market, copilot_market = (
        json.loads((root / name).read_text(encoding='utf-8')) for name in PLUGIN_METADATA
    )
    bundle = tomllib.loads((root / '.sim-ai-agents.toml').read_text(encoding='utf-8'))['bundle']
    check(plugin.get('$schema') == PLUGIN_SCHEMA, 'wrong portable plugin schema')
    check(set(plugin) <= {'$schema', 'name', 'version', 'description', 'author',
                          'homepage', 'repository', 'license', 'keywords', 'extensions'},
          'unexpected portable manifest fields')
    check((plugin['name'], plugin['version'], plugin['description'], plugin['homepage'],
           plugin['repository'], plugin['keywords']) ==
          (bundle['id'], str(recipe['version']), bundle['description'], bundle['homepage'],
           bundle['homepage'], bundle['tags']) and bundle['version'] == plugin['version'],
          'portable plugin and bundle metadata differ')
    check(plugin['license'] == 'MIT' and (root / 'LICENSE').read_text(encoding='utf-8').startswith('MIT License'),
          'portable plugin license differs from repository license')
    check(plugin['extensions']['com.openai']['interface']['displayName'] == bundle['name'],
          'Codex display name differs from bundle title')
    check(codex_market['name'] == copilot_market['name'] and
          len(codex_market['plugins']) == len(copilot_market['plugins']) == 1,
          'marketplace names or entry counts differ')
    codex_entry, copilot_entry = codex_market['plugins'][0], copilot_market['plugins'][0]
    check(codex_entry['name'] == copilot_entry['name'] == plugin['name'] and
          codex_entry['source'] == {'source': 'local', 'path': './'} and
          copilot_entry['source'] == '.' and copilot_entry['strict'] is True and
          copilot_entry['version'] == plugin['version'] and
          copilot_entry['description'] == plugin['description'],
          'marketplace entry differs from portable plugin')
    check(all(k in recipe for k in ['version', 'title', 'description', 'instructions', 'extensions', 'sub_recipes']), 'missing recipe fields')
    check({e['name'] for e in recipe['extensions']} == {'skills', 'summon', 'Simcenter 3D', 'Designcenter Open', 'Product Support', 'Simcenter Nastran MCP', 'Batch Post'}, 'unexpected extension or executable binding')
    check(all('cmd' not in e for e in recipe['extensions']), 'machine-local connector execution')
    missing = missing_recipe_skills(recipe['instructions'], skill_names)
    check(not missing, f'orchestrator references missing skills: {sorted(missing)}')

    subrecipes = recipe['sub_recipes']
    check([s['name'] for s in subrecipes] == EXPECTED_SUBRECIPES, 'expected exact 6 subrecipes')
    for sub in subrecipes:
        exp_path = f"./subrecipes/{sub['name']}.yaml"
        check(sub.get('path') == exp_path, 'unexpected subrecipe path: ' + str(sub))
        sub_file = (root / 'recipes' / exp_path.removeprefix('./')).resolve()
        check(sub_file.is_file(), 'missing subrecipe file: ' + str(sub_file))
        sub_doc = yaml.load(sub_file.read_text(encoding='utf-8'))
        check(all(k in sub_doc for k in ['version', 'title', 'description', 'instructions', 'extensions']), 'missing subrecipe fields: ' + sub['name'])
        check(all('cmd' not in e for e in sub_doc['extensions']), 'machine-local connector execution in subrecipe: ' + sub['name'])
        check('sub_recipes' not in sub_doc, 'nested sub_recipes forbidden in subrecipe: ' + sub['name'])
        missing = missing_recipe_skills(sub_doc['instructions'], skill_names)
        check(not missing, f"{sub['name']} references missing skills: {sorted(missing)}")
        if sub['name'] == 'fea-journal-author':
            dc_ext = next(e for e in sub_doc['extensions'] if e['name'] == 'Designcenter Open')
            check('dcopen-execute-tool' not in dc_ext.get('available_tools', []) and bool(dc_ext.get('available_tools')), 'fea-journal-author must allowlist Designcenter Open tools without dcopen-execute-tool')

    top_level_recipes = sorted(p.name for p in (root / 'recipes').glob('*.yaml'))
    check(top_level_recipes == ['fea-expert-agent.yaml'], 'expected only fea-expert-agent.yaml at top level of recipes/')

    for p in distribution_files(root):
        check(p.stat().st_size <= 512 * 1024, 'oversized source: ' + str(p))
        text = p.read_text(encoding='utf-8')
        if p.relative_to(root).parts[0] in {'skills', 'recipes', 'integrations', 'com.github.copilot', 'fea-workflow.md'}:
            check(not MODEL_EXAMPLE.search(text), 'reference model identity in ' + str(p))
            check('FEA integration safety contract (overrides conflicting legacy guidance)' not in text,
                  'duplicated runtime guidance in ' + str(p))
        check(not re.search(r'-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}', text), 'credential-like source: ' + str(p))
        if p.suffix == '.md' and not p.relative_to(root).as_posix().startswith('integrations/'):
            body_no_fence = re.sub(r'(?ms)^```.*?^```\s*', '', text)
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', body_no_fence):
                if target.startswith(('http:', 'https:', 'mailto:', '#')):
                    continue
                target_clean = target.split('#')[0].strip()
                if not target_clean:
                    continue
                check((p.parent / target_clean).resolve().exists(), f'broken local link in {p}: {target}')

    check(all(p.relative_to(root).as_posix() == CODEX_MARKETPLACE
              for p in (root / '.agents').rglob('*') if p.is_file() or p.is_symlink()),
          'unexpected generated .agents resources in source')
    check(not (root / 'overlay').exists(), 'unexpected separate overlay directory (all skills live in skills/)')
    return {
        'scope': 'SOURCE_ONLY',
        'checked_criterion_count': count,
        'skills': len(skills),
        'subrecipes': len(subrecipes),
        'runtime': 'NOT_RUN',
        'installation': 'NOT_RUN',
    }


if __name__ == '__main__':
    print(json.dumps(validate(), indent=2))
