"""Build and stage the local Agent Workspace candidate with an installation receipt."""
import argparse
import json
from pathlib import Path
from uuid import uuid4

from install_bundle import install
from package_bundle import ROOT
from package_release import build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--productdata', required=True, type=Path)
    parser.add_argument('--cli', required=True, type=Path)
    parser.add_argument('--receipt-directory', type=Path)
    parser.add_argument('--candidate', type=Path)
    args = parser.parse_args()
    candidate = args.candidate or Path(build()['output_directory'])
    receipts = args.receipt_directory or ROOT / '.work' / 'install-backups' / str(uuid4())
    result = install(args.cli, args.productdata, candidate / 'agents-artefact-windows.zip',
                     candidate / '.sim-ai-agents.toml', receipts)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
