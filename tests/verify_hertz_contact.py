"""Compare the Hertz fixture's F06 center pressure and approach with the half-space solution."""

import argparse
import json
import math
from pathlib import Path

from verify_contact_fixtures import accepted_tables


def verify_hertz(case):
    scope = json.loads((case / 'scope.json').read_text(encoding='utf-8'))
    times = (0.25, 0.50, 1.0)
    states = accepted_tables(case / 'hertz.f06', times)
    radius = 0.05
    reduced_modulus = 70e9 / (2 * (1 - 0.30**2))
    rows = []
    for time in times:
        load = 100 * time
        contact_radius = (3 * load * radius / (4 * reduced_modulus))**(1/3)
        reference_pressure = 3 * load / (2 * math.pi * contact_radius**2)
        reference_approach = contact_radius**2 / radius
        state = states[time]
        center = state['pressure'][scope['upper_origin']]
        displacements = state['displacement']
        approach = displacements[1] - displacements[scope['free_top_node']]
        reaction = 4 * sum(force for node, force in state['reaction'].items() if node <= scope['bottom_last'])
        contact = 4 * sum(state['contact_force'].get(node, 0.0) for node in scope['source_face_nodes'])
        pressure_error = center / reference_pressure - 1
        approach_error = approach / reference_approach - 1
        rows.append({
            'load_N': load, 'pressure_Pa': center, 'approach_m': approach,
            'pressure_error_pct': 100 * pressure_error, 'approach_error_pct': 100 * approach_error,
            'reaction_N': reaction, 'contact_N': contact,
            'pass': abs(pressure_error) < 0.05 and abs(approach_error) < 0.05
            and math.isclose(reaction, load, rel_tol=0.01)
            and math.isclose(contact, load, rel_tol=0.02),
        })
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', nargs='+', type=Path)
    options = parser.parse_args()
    report = {str(case): verify_hertz(case) for case in options.case}
    print(json.dumps(report, indent=2, allow_nan=False))
    raise SystemExit(0 if all(row['pass'] for rows in report.values() for row in rows) else 1)
