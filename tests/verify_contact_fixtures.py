"""Check the accepted states of the synthetic elastic contact-cycle fixtures."""

from collections import defaultdict
from math import isclose
from pathlib import Path
import argparse
import json
import re


SEPARATION = 'D E F O R M E D  C O N T A C T  S E P A R A T I O N  D I S T A N C E'
HEADINGS = {
    'D I S P L A C E M E N T   V E C T O R': ('displacement', 2),
    'C O N T A C T  F O R C E S': ('contact_force', 2),
    'F O R C E S   O F   S I N G L E - P O I N T   C O N S T R A I N T': ('reaction', 2),
    SEPARATION: ('separation', 0),
}
TIME = re.compile(r'^\s+TIME\s*=\s*([\d.+E-]+)\s*$')
ROW = re.compile(r'^\s+(\d+)\s+G\s+(.+)$')


def accepted_tables(path):
    """Read the fixture's four terminal states by the actual F06 time coordinate."""
    states = defaultdict(lambda: defaultdict(dict))
    time = field = None
    complete = fatal = False
    with path.open() as stream:
        for line in stream:
            if line.startswith('1'):
                time = field = None
            if 'END OF JOB' in line:
                complete = True
            if re.search(r'\bFATAL\b', line):
                fatal = True
            match = TIME.match(line)
            if match:
                time = float(match[1])
                field = None
            if time not in (1., 2., 3., 4.):
                continue
            title = line.strip()
            if title in HEADINGS:
                field, component = HEADINGS[title]
                states[time][field]
            elif field and (match := ROW.match(line)):
                states[time][field][int(match[1])] = float(match[2].split()[component])
    if fatal or not complete:
        raise ValueError('Expected a completed solve without a fatal diagnosis')
    return states


def verify_cycle(path):
    tables = accepted_tables(path)
    area = 0.01**2
    gap = 0.00005
    compliance = 2 * 0.01 / (2e9 * area)
    result = []
    for time, travel in enumerate((0.000025, 0.000075, 0.000100, 0.000025), 1):
        fields = tables[time]
        expected = max(travel - gap, 0) / compliance
        displacement = -fields['displacement'][13]
        separation = fields['separation'][5]
        reaction = sum(fields['reaction'].get(node, 0.0) for node in (1, 2, 3, 4))
        force = abs(sum(fields.get('contact_force', {}).get(node, 0.0) for node in (5, 6, 7, 8)))
        if not isclose(displacement, travel, rel_tol=1e-6):
            raise ValueError(f'Wrong prescribed displacement at time {time}')
        if expected == 0.0:
            if not isclose(separation, gap-travel, rel_tol=1e-5) or max(force, abs(reaction)) > 1.0:
                raise ValueError(f'Open-state gap or force outside tolerance at time {time}')
        else:
            if 'contact_force' not in fields or separation > 1e-11:
                raise ValueError(f'Closed state missing at time {time}')
            if not isclose(force, expected, rel_tol=0.05) or not isclose(force, reaction, rel_tol=0.01):
                raise ValueError(f'Normal force or reaction outside tolerance at time {time}')
        result.append({'time':time, 'travel_mm':displacement*1e3, 'gap_mm':separation*1e3,
                       'force_N':force, 'reaction_N':reaction, 'reference_N':expected})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('f06', type=Path)
    options = parser.parse_args()
    print(json.dumps(verify_cycle(options.f06), indent=2))
