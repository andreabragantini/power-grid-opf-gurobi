"""Output management utilities for OPF simulation artifacts.

This module centralizes where and how simulation outputs are stored so users can
inspect results quickly without relying on console logs.
"""

from datetime import datetime
from pathlib import Path
import os

import pandas as pd

import defaults


def _build_run_id():
    """Build a UTC timestamp-based run identifier."""
    return datetime.utcnow().strftime('%Y%m%d_%H%M%S')


def prepare_output_paths(formulation_name):
    """Create output directories for the active run.

    Args:
        formulation_name: Name of the active OPF formulation.

    Returns:
        Dictionary with resolved output paths for run artifacts.
    """
    defaults.refresh_from_env()

    output_root = Path(os.getenv('OPF_OUTPUT_ROOT', 'outputs'))
    run_id = _build_run_id()

    run_dir = output_root / defaults.CASE_NAME / formulation_name / run_id
    tables_dir = run_dir / 'tables'
    plots_dir = run_dir / 'plots'

    tables_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    return {
        'output_root': output_root,
        'run_id': run_id,
        'run_dir': run_dir,
        'tables_dir': tables_dir,
        'plots_dir': plots_dir,
    }


def _write_table(df, path):
    """Write a pandas DataFrame to CSV with index included."""
    df.to_csv(path, index=True)


def compute_kpis(context, formulation_name):
    """Compute simulation KPI values for fast cross-case comparison."""
    total_gen = float(context.results.Pgen['Pgen'].sum()) if not context.results.Pgen.empty else 0.0
    total_wind = float(context.results.WindOPF['WindGen'].sum()) if not context.results.WindOPF.empty else 0.0
    total_load = float(context.data.load['Load'].sum()) if hasattr(context.data, 'load') else 0.0

    return {
        'timestamp_utc': datetime.utcnow().isoformat(timespec='seconds'),
        'case_name': defaults.CASE_NAME,
        'formulation': formulation_name,
        'status': context.results.metadata.get('status'),
        'objective_value': context.results.metadata.get('objective_value'),
        'num_constraints': context.results.metadata.get('num_constraints'),
        'num_variables': context.results.metadata.get('num_variables'),
        'num_buses': len(context.data.nodes),
        'num_lines': len(context.data.AC_lines),
        'num_generators': len(context.data.generators),
        'num_windfarms': len(context.data.windfarms),
        'total_generation_mw': total_gen,
        'total_wind_mw': total_wind,
        'total_load_mw': total_load,
        'net_supply_minus_load_mw': (total_gen + total_wind - total_load),
    }


def save_results_bundle(context, formulation_name, paths, plot_paths):
    """Persist tables, KPI files, and run index for one OPF simulation."""
    _write_table(context.results.Pgen, paths['tables_dir'] / 'pgen.csv')
    _write_table(context.results.WindOPF, paths['tables_dir'] / 'wind.csv')
    _write_table(context.results.lineflow_AC_OPF, paths['tables_dir'] / 'lineflow.csv')
    _write_table(context.results.nodeangle, paths['tables_dir'] / 'nodeangle.csv')

    kpis = compute_kpis(context, formulation_name)
    kpi_df = pd.DataFrame([kpis])
    kpi_df.to_csv(paths['run_dir'] / 'kpis.csv', index=False)

    kpi_history_path = paths['output_root'] / 'kpi_history.csv'
    if kpi_history_path.exists():
        history_df = pd.read_csv(kpi_history_path)
        history_df = pd.concat([history_df, kpi_df], ignore_index=True)
    else:
        history_df = kpi_df
    history_df.to_csv(kpi_history_path, index=False)

    _write_run_index(paths, kpis, plot_paths)


def _write_run_index(paths, kpis, plot_paths):
    """Write an HTML landing page for quick artifact inspection."""
    index_path = paths['run_dir'] / 'index.html'

    rows_html = '\n'.join(
        '<tr><td>{0}</td><td>{1}</td></tr>'.format(key, value)
        for key, value in kpis.items()
    )

    content = """<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>OPF Run Summary</title>
  <style>
        body {{ font-family: Segoe UI, sans-serif; margin: 24px; }}
        h1, h2 {{ margin-bottom: 8px; }}
        table {{ border-collapse: collapse; min-width: 560px; }}
        td, th {{ border: 1px solid #ddd; padding: 8px; }}
        th {{ background: #f5f5f5; }}
        .links a {{ display: block; margin: 6px 0; }}
  </style>
</head>
<body>
  <h1>OPF Simulation Summary</h1>
  <div class=\"links\">
    <a href=\"tables/pgen.csv\">Generator dispatch table</a>
    <a href=\"tables/wind.csv\">Wind dispatch table</a>
    <a href=\"tables/lineflow.csv\">Line flow table</a>
    <a href=\"tables/nodeangle.csv\">Voltage angle table</a>
    <a href=\"{assets_plot}\">Network connectivity plot</a>
    <a href=\"{heatmap_plot}\">Network OPF heatmap plot</a>
  </div>
  <h2>KPIs</h2>
  <table>
    <tbody>
      {rows}
    </tbody>
  </table>
</body>
</html>
""".format(
        assets_plot=plot_paths['assets_plot'].name,
        heatmap_plot=plot_paths['heatmap_plot'].name,
        rows=rows_html,
    )

    index_path.write_text(content, encoding='utf-8')
