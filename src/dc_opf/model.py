"""High-level DC OPF model orchestration.

This module assembles data loading, model build, solve, and result extraction
for the DC OPF formulation.
"""

import gurobipy as gb
import os

from src.common import output_manager
from src.common.model_context import ModelContext
from src.common import data_loader
from src.dc_opf import chart
from src.dc_opf import constraints
from src.dc_opf import objective
from src.dc_opf import results
from src.dc_opf import variables


class DCOPFModel:
    """Orchestrator class for the DC OPF lifecycle."""

    def __init__(self, formulation_name='dc_opf'):
        """Initialize context, load data, and build optimization model."""
        self.formulation_name = formulation_name
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
        # Keep console quiet by default; users inspect saved artifacts instead.
        solver_output = os.getenv('OPF_GUROBI_OUTPUT', '0')
        self.context.model.Params.OutputFlag = 1 if solver_output == '1' else 0
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

    def build_chart(self, output_dir):
        """Build interactive network plots and return generated file paths."""
        return chart.build_network_charts(self.context, output_dir)

    def save_outputs(self):
        """Persist all run artifacts and return the run directory path."""
        paths = output_manager.prepare_output_paths(self.formulation_name)
        plot_paths = self.build_chart(paths['plots_dir'])
        output_manager.save_results_bundle(self.context, self.formulation_name, paths, plot_paths)

        self.results.output_paths = {
            'run_dir': paths['run_dir'],
            'plots_dir': paths['plots_dir'],
            'tables_dir': paths['tables_dir'],
            'index_html': paths['run_dir'] / 'index.html',
            'kpis_csv': paths['run_dir'] / 'kpis.csv',
        }
        return self.results.output_paths
