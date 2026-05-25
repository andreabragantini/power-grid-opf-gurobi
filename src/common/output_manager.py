"""Output management utilities for OPF simulation artifacts.

This module centralizes where and how simulation outputs are stored so users can
inspect results quickly without relying on console logs.
"""

from pathlib import Path
import os
import shutil

from datetime import datetime

import pandas as pd

import defaults


def prepare_output_paths(formulation_name):
    """Create output directories for the active run.

    Args:
        formulation_name: Name of the active OPF formulation.

    Returns:
        Dictionary with resolved output paths for run artifacts.
    """
    defaults.refresh_from_env()

    output_root = Path(os.getenv('OPF_OUTPUT_ROOT', 'outputs'))
    legacy_kpi_history = output_root / 'kpi_history.csv'
    if legacy_kpi_history.exists():
        legacy_kpi_history.unlink()
    # Use a fixed location per case/formulation so each new run overwrites old artifacts.
    run_dir = output_root / defaults.CASE_NAME / formulation_name / 'latest'
    tables_dir = run_dir / 'tables'
    plots_dir = run_dir / 'plots'

    if run_dir.exists():
        shutil.rmtree(run_dir)

    tables_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    return {
        'output_root': output_root,
        'run_id': 'latest',
        'run_dir': run_dir,
        'tables_dir': tables_dir,
        'plots_dir': plots_dir,
    }


def _write_table(df, path):
    """Write a pandas DataFrame to CSV with index included."""
    df.to_csv(path, index=True)


def compute_kpis(context, formulation_name):
    """Compute simulation KPI values for fast cross-case comparison."""
    total_gen = float(pd.to_numeric(context.results.p_gen['p_gen_mw'], errors='coerce').fillna(0.0).sum()) if not context.results.p_gen.empty else 0.0
    total_wind = float(pd.to_numeric(context.results.p_wind['p_wind_mw'], errors='coerce').fillna(0.0).sum()) if not context.results.p_wind.empty else 0.0
    total_load = float(context.data.load['Load'].sum()) if hasattr(context.data, 'load') else 0.0

    return {
        'timestamp_utc': datetime.utcnow().isoformat(timespec='seconds'),
        'case_name': defaults.CASE_NAME,
        'formulation': formulation_name,
        'status': context.results.metadata.get('status'),
        'status_label': context.results.metadata.get('status_label'),
        'converged': context.results.metadata.get('converged'),
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
        'total_generation_capacity_mw': context.results.metadata.get('total_generation_capacity_mw'),
        'capacity_margin_mw': context.results.metadata.get('capacity_margin_mw'),
        'load_scaler': context.results.metadata.get('load_scaler'),
        'likely_issue': context.results.metadata.get('likely_issue'),
        'net_supply_minus_load_mw': (total_gen + total_wind - total_load),
    }


def save_results_bundle(context, formulation_name, paths, plot_paths):
    """Persist tables, KPI files, and run index for one OPF simulation."""
    _write_table(context.results.p_gen, paths['tables_dir'] / 'p_gen.csv')
    _write_table(context.results.p_wind, paths['tables_dir'] / 'p_wind.csv')
    _write_table(context.results.p_line, paths['tables_dir'] / 'p_line.csv')
    _write_table(context.results.theta, paths['tables_dir'] / 'theta.csv')

    kpis = compute_kpis(context, formulation_name)
    kpi_df = pd.DataFrame([kpis])
    kpi_df.to_csv(paths['run_dir'] / 'kpis.csv', index=False)

    _write_run_index(paths, kpis, plot_paths)


def _write_run_index(paths, kpis, plot_paths):
    """Write an HTML landing page for quick artifact inspection."""
    index_path = paths['run_dir'] / 'index.html'

    rows_html = '\n'.join(
        '<tr><td>{0}</td><td>{1}</td></tr>'.format(key, value)
        for key, value in kpis.items()
    )

    status_label = kpis.get('status_label', kpis.get('status'))
    converged_text = 'YES' if kpis.get('converged') else 'NO'
    likely_issue = kpis.get('likely_issue') or 'No additional diagnostic message.'

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
    <h1>OPF Simulation Summary (Latest Run)</h1>
    <h2>Convergence</h2>
    <table>
        <tbody>
            <tr><td>Converged</td><td>{converged_text}</td></tr>
            <tr><td>Status</td><td>{status_label}</td></tr>
            <tr><td>Diagnostic</td><td>{likely_issue}</td></tr>
        </tbody>
    </table>
  <div class=\"links\">
        <a href=\"tables/p_gen.csv\">Generator dispatch table</a>
        <a href=\"tables/p_wind.csv\">Wind dispatch table</a>
        <a href=\"tables/p_line.csv\">Line flow table</a>
        <a href=\"tables/theta.csv\">Voltage angle table</a>
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
    converged_text=converged_text,
    status_label=status_label,
    likely_issue=likely_issue,
        assets_plot=plot_paths['assets_plot'].name,
        heatmap_plot=plot_paths['heatmap_plot'].name,
        rows=rows_html,
    )

    index_path.write_text(content, encoding='utf-8')
