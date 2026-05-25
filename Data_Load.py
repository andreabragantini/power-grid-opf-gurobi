# -*- coding: utf-8 -*-
"""Legacy compatibility wrappers for data loading.

The active implementation lives in src.common.data_loader.
This module keeps the historical API to avoid breaking existing scripts.
"""

from src.common import data_loader


def _load_network(self):
    """Load canonical network data into the legacy model object."""
    data_loader.load_network_data(self)


def _load_generator_data(self):
    """Load generator records into the legacy model object."""
    data_loader.load_generator_data(self)


def _load_wind_data(self):
    """Load optional wind records into the legacy model object."""
    data_loader.load_wind_data(self)


def _load_intial_data(self):
    """Load nodal demand using bus fields or legacy fallback files."""
    data_loader.load_nodal_demand_data(self)
    
	
