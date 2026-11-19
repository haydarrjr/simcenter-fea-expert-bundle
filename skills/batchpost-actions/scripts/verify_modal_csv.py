"""Verify exported modal CSV state labels against explicit BatchPost selections."""
import argparse
from collections import Counter
import csv
from pathlib import Path
import re


STATE = re.compile(r'(Load Case \d+)\s*-\s*(Mode \d+)\s*,\s*[-+.\deE]+\s*Hz', re.I)


def verify(paths, expected):
    observed = Counter()
    for path in paths:
        with Path(path).open(encoding='utf-8-sig', newline='') as stream:
            states = [f'{match[1]}:{match[2]}' for row in csv.reader(stream)
                      for field in row if (match := STATE.fullmatch(field.strip()))]
        if not states:
            raise ValueError(f'no recognized modal state labels in {path}')
        observed.update(states)
    desired = Counter(expected)
    if not desired or any(n != 1 for n in desired.values()):
        raise ValueError('supply distinct expected state labels')
    if observed != desired:
        raise ValueError(f'missing states: {dict(desired - observed)}; '
                         f'extra or repeated states: {dict(observed - desired)}')
    return sorted(observed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expect', action='append', required=True, help='e.g. Load Case 1:Mode 7')
    parser.add_argument('csv', nargs='+', type=Path)
    args = parser.parse_args()
    print('\n'.join(verify(args.csv, args.expect)))
