# -*- coding: utf-8 -*-
"""Legacy result extractor wrapper.

The active implementation lives in src.dc_opf.results.
"""

from src.dc_opf.results import build_results as _build_results


def build_results_OPF(self):
    """Build DC OPF result tables through the modular implementation."""
    _build_results(self)