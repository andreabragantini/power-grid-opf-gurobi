# power-grid-opf-gurobi

Modular Optimal Power Flow (OPF) framework for power grids using Gurobi.

The project started as an academic prototype and is now organized as a formulation-driven codebase for research, validation, and iterative case-study development.

## Current project status

Implemented formulations:

- `dc_opf`
- `ac_lp_lossless`

Scaffolded (not implemented yet):

- `ac_lp_losses_p`
- `ac_lp_losses_pq`
- `fbs_opf`

## Latest study findings (May 2026)

### AC LP lossless smoke test (default case sequence)

- IEEE_3bus: converged
- custom_6bus: converged
- IEEE_118bus: converged
- ZUG_1600bus: infeasible at full load, feasible with moderate demand scaling

### custom_6bus data tuning result

- The case converges when branch parameters are tuned to realistic values and admittance is derived from resistance/reactance.
- Branch data should use `BR_R_PU` and `BR_X_PU`; explicit custom `B`/`G` columns are not required.

### ZUG_1600bus behavior

- The large reactive-load outlier was corrected in the dataset.
- Full-load run remains locally infeasible (tight bottleneck around branch `(1046, 1045)`).
- The case converges from approximately `OPF_LOAD_SCALER=0.94` downward.
- Transformer-specific fields (`Tap`, `Shift`, etc.) are not used by the current AC LP lossless equations, so this case currently runs with the available R/X-based branch model only.

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

Legacy root wrappers were removed to keep the codebase focused on the modular `src/` implementation.

## Reproducible setup

This repository is developed in a conda environment with Python 3.10.

### 1. Create and activate the environment

```bash
conda create -n gurobi python=3.10
conda activate gurobi
```

### 2. Install Gurobi

Gurobi is not installed from `requirements.txt`; install it first and configure a valid license.

- Installer and license setup: https://support.gurobi.com/hc/en-us/articles/360044290292-How-do-I-install-Gurobi-Optimizer
- Official docs: https://www.gurobi.com/documentation/
- Downloads: https://www.gurobi.com/downloads/gurobi-software/

Common install options:

- `conda install -c gurobi gurobi`
- `python -m pip install gurobipy`

### 3. Install Python dependencies

```bash
python -m pip install -r requirements.txt
```

## Run commands

### List available cases

```bash
python main.py --list-cases
```

### Run one case/formulation

```bash
python main.py --case custom_6bus --formulation ac_lp_lossless
```

### Run smoke sequence

```bash
python examples/run_cases.py --formulation ac_lp_lossless
```

### Environment-variable control (PowerShell)

```powershell
$env:OPF_CASE_NAME = "ZUG_1600bus"
$env:OPF_FORMULATION = "ac_lp_lossless"
$env:OPF_LOAD_SCALER = "1.0"
python main.py
```

`OPF_LOAD_SCALER` applies a global multiplier to both active and reactive nodal demand.

## Data conventions

Each case folder under `data/` should provide:

- `buses.csv`
- `branches.csv`
- `generators.csv`
- optional `windfarms.csv`
- optional `other.csv` (for `BaseMVA`)

The loader supports mixed CSV delimiters and harmonized aliases across custom and MATPOWER-style exports.

## Outputs

Each run writes artifacts under:

- `outputs/<case>/<formulation>/latest/index.html`
- `outputs/<case>/<formulation>/latest/tables/*.csv`
- `outputs/<case>/<formulation>/latest/plots/network_assets.html`
- `outputs/<case>/<formulation>/latest/plots/network_results_heatmap.html`
- `outputs/<case>/<formulation>/latest/kpis.csv`

The `latest` folder is overwritten per case/formulation run.

## Documentation and references

- Architecture notes: `docs/architecture.md`
- Multi-case runner: `examples/run_cases.py`
- Benchmark notes: `benchmarks/README.md`
