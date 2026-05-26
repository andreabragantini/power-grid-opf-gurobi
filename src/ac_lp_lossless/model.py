"""High-level AC LP lossless OPF model orchestration."""

import os

import gurobipy as gb

from src.ac_lp_lossless import chart
from src.ac_lp_lossless import constraints
from src.ac_lp_lossless import objective
from src.ac_lp_lossless import results
from src.ac_lp_lossless import variables
from src.common import data_loader
from src.common import output_manager
from src.common.model_context import ModelContext


class ACLPLosslessModel:
    """Orchestrator class for the AC LP lossless OPF lifecycle."""

    def __init__(self, formulation_name='ac_lp_lossless'):
        self.formulation_name = formulation_name
        self.context = ModelContext()
        self._load_data()
        self._build_model()

    @property
    def data(self):
        return self.context.data

    @property
    def variables(self):
        return self.context.variables

    @property
    def constraints(self):
        return self.context.constraints

    @property
    def results(self):
        return self.context.results

    @property
    def model(self):
        return self.context.model

    def _load_data(self):
        data_loader.load_network_data(self.context)
        data_loader.load_generator_data(self.context)
        data_loader.load_wind_data(self.context)
        data_loader.load_nodal_demand_data(self.context)

    def _build_model(self):
        self.context.model = gb.Model()
        solver_output = os.getenv('OPF_GUROBI_OUTPUT', '0')
        self.context.model.Params.OutputFlag = 1 if solver_output == '1' else 0

        variables.build_variables(self.context)
        constraints.build_all_constraints(self.context)
        objective.build_objective(self.context)
        self.context.model.update()

    def optimize(self):
        self.context.model.optimize()

    def build_results(self):
        results.build_results(self.context)

    def build_chart(self, output_dir):
        return chart.build_network_charts(self.context, output_dir)

    def save_outputs(self):
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
