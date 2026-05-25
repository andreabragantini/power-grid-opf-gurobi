"""Run multiple OPF cases sequentially for smoke testing.

This script is intentionally lightweight and useful during refactoring.
"""

import os
import sys
from pathlib import Path

# Ensure repository root is importable when running from examples/.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from main import run


def run_case(case_name):
    """Run DC OPF for one dataset case and print a short summary."""
    os.environ['OPF_CASE_NAME'] = case_name
    os.environ['OPF_FORMULATION'] = 'dc_opf'

    model = run(formulation_name='dc_opf')
    metadata = getattr(model.results, 'metadata', {})
    outputs = getattr(model.results, 'output_paths', {})
    print('case={0}, status={1}, objective={2}'.format(
        case_name,
        metadata.get('status'),
        metadata.get('objective_value'),
    ))
    print('results index: {0}'.format(outputs.get('index_html')))


def main():
    """Execute the default sequence from micro to larger systems."""
    for case in ['IEEE_3bus', 'custom_6bus', 'IEEE_118bus']:
        run_case(case)


if __name__ == '__main__':
    main()
