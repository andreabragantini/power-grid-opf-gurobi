# power-grid-opf-gurobi

Modular Optimal Power Flow (OPF) framework for power grids using Gurobi.

This repository is being evolved from an academic prototype into a clean, extensible research and engineering framework. The current implemented formulation is DC OPF, with architecture in place for additional formulations.

## Implemented and planned formulations

- Implemented: DC OPF
- Planned: AC LP lossless OPF
- Planned: AC LP active-loss OPF
- Planned: AC LP active/reactive-loss OPF
- Planned: Forward-Backward Sweep OPF

## Repository structure

```text
power-grid-opf-gurobi/
├── data/
├── src/
│   ├── common/
│   ├── dc_opf/
│   ├── ac_lp_lossless/
│   ├── ac_lp_losses_p/
│   ├── ac_lp_losses_pq/
│   └── fbs_opf/
├── docs/
├── examples/
├── benchmarks/
├── notebooks/
├── main.py
└── requirements.txt
```

## Reproducible setup

This repository has been developed in a local conda environment with Python 3.10.

### 1. Create and activate the environment

```bash
conda create -n gurobi python=3.10
conda activate gurobi
```

### 2. Install Gurobi using one of the official methods

Gurobi is not installed from `requirements.txt`. You need the Gurobi optimizer and a valid license first.

Recommended installation options:

- Gurobi installer and license setup: https://support.gurobi.com/hc/en-us/articles/360044290292-How-do-I-install-Gurobi-Optimizer
- Official Gurobi documentation: https://www.gurobi.com/documentation/
- Gurobi downloads page: https://www.gurobi.com/downloads/gurobi-software/

Common ways to install the Python interface and optimizer:

- Conda package: `conda install -c gurobi gurobi`
- Python package: `python -m pip install gurobipy`
- Standalone installer: download and install Gurobi Optimizer from the official site, then configure your license

If you already have a working conda environment with Gurobi, keep using that environment for reproducibility.

### 3. Install the Python dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the model

```bash
python main.py
```

### 5. Select case and formulation

You can choose case and formulation directly from CLI:

```bash
python main.py --list-cases
python main.py --case custom_6bus --formulation dc_opf
```

Environment variables are also supported:

```bash
# Windows PowerShell example
$env:OPF_CASE_NAME = "IEEE_3bus"
$env:OPF_FORMULATION = "dc_opf"
python main.py
```

Optional load scaling knob (DC OPF):

```bash
# Global multiplier applied to all node loads before optimization.
# 1.0 means 100%, 0.9 means 90%, etc.
$env:OPF_LOAD_SCALER = "1.0"
```

Available case folders currently include:

- IEEE_3bus
- custom_6bus
- IEEE_118bus
- ZUG_1600bus

## Data conventions

Each case folder under `data/` should provide:

- `buses.csv`
- `branches.csv`
- `generators.csv`
- optional `windfarms.csv`
- optional `other.csv` (for `BaseMVA`)

The loader supports harmonized aliases across custom and MATPOWER-style exports.

## Documentation

- Architecture notes: `docs/architecture.md`
- Example runner: `examples/run_cases.py`
- Benchmark notes: `benchmarks/README.md`

## Result consultation workflow

Simulation outputs are now saved under `outputs/` for quick inspection.

Per run, the repository writes:

- `outputs/<case>/<formulation>/latest/index.html` (landing page)
- `outputs/<case>/<formulation>/latest/tables/*.csv` (result tables)
- `outputs/<case>/<formulation>/latest/plots/network_assets.html`
- `outputs/<case>/<formulation>/latest/plots/network_results_heatmap.html`
- `outputs/<case>/<formulation>/latest/kpis.csv`

The `latest` folder is overwritten on each run for that case/formulation.

## Notes

- The default case is `IEEE_3bus`; change it via `OPF_CASE_NAME`.
- If Gurobi changes behavior in a future release, the solver package version may need to be adjusted as well.
- The architecture now uses a formulation registry so new OPF variants can be added without rewriting the entrypoint.
