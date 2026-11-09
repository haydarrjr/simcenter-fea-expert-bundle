"""Offline source/package contract for Simcenter 3D FEA Expert; never operates a CAE/CAD host."""
from pathlib import Path
import json, re
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SUFFIXES = {'.md', '.py', '.json', '.yaml', '.yml', '.txt', '.toml', '.xsd'}
EXPECTED_SKILLS = 38
EXPECTED_SUBRECIPES = [
    'fea-model-inspector',
    'fea-journal-author',
    'fea-solver-diagnostics',
    'fea-results-post',
    'fea-verifier',
    'product-support-agent',
]


def distribution_files(root=ROOT):
    selected = []
    for name in ['.sim-ai-agents.toml', 'README.md', 'RELEASE_NOTES.md', 'LICENSE', 'requirements-test.txt', 'recipes', 'skills', 'docs', 'scripts', 'tests']:
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
    check(all(k in recipe for k in ['version', 'title', 'description', 'instructions', 'extensions', 'sub_recipes']), 'missing recipe fields')
    check({e['name'] for e in recipe['extensions']} == {'skills', 'summon', 'Simcenter 3D', 'Designcenter Open', 'Product Support', 'Simcenter Nastran MCP', 'Batch Post'}, 'unexpected extension or executable binding')
    check(all('cmd' not in e for e in recipe['extensions']), 'machine-local connector execution')

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
        if sub['name'] == 'fea-journal-author':
            dc_ext = next(e for e in sub_doc['extensions'] if e['name'] == 'Designcenter Open')
            check('dcopen-execute-tool' not in dc_ext.get('available_tools', []) and bool(dc_ext.get('available_tools')), 'fea-journal-author must allowlist Designcenter Open tools without dcopen-execute-tool')

    top_level_recipes = sorted(p.name for p in (root / 'recipes').glob('*.yaml'))
    check(top_level_recipes == ['fea-expert-agent.yaml'], 'expected only fea-expert-agent.yaml at top level of recipes/')

    for p in distribution_files(root):
        check(p.stat().st_size <= 512 * 1024, 'oversized source: ' + str(p))
        text = p.read_text(encoding='utf-8')
        check(not re.search(r'-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}', text), 'credential-like source: ' + str(p))
        if p.suffix == '.md':
            body_no_fence = re.sub(r'(?ms)^```.*?^```\s*', '', text)
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', body_no_fence):
                if target.startswith(('http:', 'https:', 'mailto:', '#')):
                    continue
                target_clean = target.split('#')[0].strip()
                if not target_clean:
                    continue
                check((p.parent / target_clean).resolve().exists(), f'broken local link in {p}: {target}')

    check(not (root / '.agents').exists(), 'unexpected .agents directory (use top-level recipes/ and skills/)')
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
