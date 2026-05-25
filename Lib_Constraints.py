# -*- coding: utf-8 -*-
"""Legacy DC constraint wrappers.

The active implementation lives in src.dc_opf.constraints.
These wrappers preserve the original function names for compatibility.
"""

from src.dc_opf.constraints import build_angle_limit_constraints
from src.dc_opf.constraints import build_flow_angle_constraints
from src.dc_opf.constraints import build_flow_limit_constraints
from src.dc_opf.constraints import build_generator_pmax_constraints
from src.dc_opf.constraints import build_generator_pmin_constraints
from src.dc_opf.constraints import build_power_balance_constraints
from src.dc_opf.constraints import build_wind_capacity_constraints


def build_PowerBalOPF_constr(self):
    """Compatibility wrapper for nodal balance constraints."""
    return build_power_balance_constraints(self)


def build_PmaxOPF_constr(self):
    """Compatibility wrapper for generator upper limits."""
    return build_generator_pmax_constraints(self)


def build_PminOPF_constr(self):
    """Compatibility wrapper for generator lower limits."""
    return build_generator_pmin_constraints(self)


def build_WindmaxOPF_constr(self):
    """Compatibility wrapper for wind capacity limits."""
    return build_wind_capacity_constraints(self)


def build_flow_to_angleOPF_constr(self):
    """Compatibility wrapper for flow-angle coupling constraints."""
    return build_flow_angle_constraints(self)


def build_flow_lim_OPF_constr(self):
    """Compatibility wrapper for branch flow limits."""
    return build_flow_limit_constraints(self)


def build_angle_OPF_constr(self):
    """Compatibility wrapper for nodal angle bounds."""
    return build_angle_limit_constraints(self)
