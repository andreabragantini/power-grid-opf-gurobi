# -*- coding: utf-8 -*-
"""Legacy variable builder wrapper.

The active implementation lives in src.dc_opf.variables.
"""

from src.dc_opf.variables import build_variables as _build_variables


def build_variables_OPF(self):
    """Build DC OPF variables through the modular implementation."""
    _build_variables(self)
        
       
