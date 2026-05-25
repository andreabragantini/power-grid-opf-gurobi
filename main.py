# -*- coding: utf-8 -*-
"""Repository entrypoint for OPF formulations.

The active default formulation is DC OPF, created through the formulation
registry so additional formulations can be added incrementally.
"""

import argparse
import os
from pathlib import Path

from src.formulation_registry import create_model


# Backward-compatible alias used by older scripts.
DCOPF = create_model


def _available_cases(data_root='data'):
    """Return available case-study folder names under data root."""
    root = Path(data_root)
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])


def run(formulation_name='dc_opf', case_name=None):
    """Run an OPF formulation and persist simulation artifacts.

    Args:
        formulation_name: Formulation key, defaulting to dc_opf.
        case_name: Optional explicit case study folder name.

    Returns:
        The solved model object with output paths in results.output_paths.
    """
    if case_name:
        os.environ['OPF_CASE_NAME'] = case_name

    opf_model = create_model(formulation_name)
    opf_model.optimize()
    opf_model.build_results()
    output_paths = opf_model.save_outputs()
    metadata = getattr(opf_model.results, 'metadata', {})
    case_label = getattr(opf_model.data, 'case_name', os.getenv('OPF_CASE_NAME', 'unknown'))

    # Minimal end-of-run notification for discoverability of saved artifacts.
    print(
        '\n[OPF] Completed | case={0} | formulation={1} | status={2}'.format(
            case_label,
            formulation_name,
            metadata.get('status_label', metadata.get('status')),
        )
    )
    if metadata.get('likely_issue'):
        print('[OPF] Diagnostic: {0}'.format(metadata.get('likely_issue')))
    print('[OPF] Results index: {0}'.format(output_paths['index_html']))

    return opf_model


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run OPF simulation and persist artifacts.')
    parser.add_argument('--formulation', default=os.getenv('OPF_FORMULATION', 'dc_opf'))
    parser.add_argument('--case', dest='case_name', default=os.getenv('OPF_CASE_NAME'))
    parser.add_argument('--list-cases', action='store_true', help='List available case folders and exit.')
    args = parser.parse_args()

    if args.list_cases:
        cases = _available_cases(os.getenv('OPF_DATA_ROOT', 'data'))
        if not cases:
            print('[OPF] No case folders found in data root.')
        else:
            print('[OPF] Available cases:')
            for case in cases:
                print(' - {0}'.format(case))
    else:
        run(formulation_name=args.formulation, case_name=args.case_name)