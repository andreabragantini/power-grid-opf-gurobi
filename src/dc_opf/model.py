"""High-level DC OPF model orchestration.

This module assembles data loading, model build, solve, and result extraction
for the DC OPF formulation.
"""

import gurobipy as gb

from src.common.model_context import ModelContext
from src.common import data_loader
from src.dc_opf import chart
from src.dc_opf import constraints
from src.dc_opf import objective
from src.dc_opf import results
from src.dc_opf import variables


class DCOPFModel:
    """Orchestrator class for the DC OPF lifecycle."""

    def __init__(self):
        """Initialize context, load data, and build optimization model."""
        self.context = ModelContext()
        self._load_data()
        self._build_model()

    @property
    def data(self):
        """Compatibility property exposing context data namespace."""
        return self.context.data

    @property
    def variables(self):
        """Compatibility property exposing context variables namespace."""
        return self.context.variables

    @property
    def constraints(self):
        """Compatibility property exposing context constraints namespace."""
        return self.context.constraints

    @property
    def results(self):
        """Compatibility property exposing context results namespace."""
        return self.context.results

    @property
    def model(self):
        """Compatibility property exposing the Gurobi model instance."""
        return self.context.model

    def _load_data(self):
        """Load all data components needed by the DC OPF model."""
        data_loader.load_network_data(self.context)
        data_loader.load_generator_data(self.context)
        data_loader.load_wind_data(self.context)
        data_loader.load_nodal_demand_data(self.context)

    def _build_model(self):
        """Build optimization model variables, constraints, and objective."""
        self.context.model = gb.Model()
        variables.build_variables(self.context)
        constraints.build_all_constraints(self.context)
        objective.build_objective(self.context)
        self.context.model.update()

    def optimize(self):
        """Run the optimization solver."""
        self.context.model.optimize()

    def build_results(self):
        """Extract post-solve result tables and metadata."""
        results.build_results(self.context)

    def build_chart(self):
        """Draw simple network topology visualization."""
        chart.build_network_chart(self.context)
