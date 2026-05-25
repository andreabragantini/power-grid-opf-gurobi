# power-grid-opf-gurobi

Modular Optimal Power Flow (OPF) framework for power grids using Gurobi. The code implements DC OPF and related formulations for benchmarking, research, and analysis of dispatch, congestion, losses, and voltage behavior in distribution networks.

## Reproducible setup

This repository has been developed in a local conda environment named with Python 3.10.

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

## Notes

- The code expects the data files in `DataInput/`.
- If Gurobi changes behavior in a future release, the solver package version may need to be adjusted as well.
- The repository now uses the current pandas and gurobipy APIs so it can run under the selected conda environment without local code changes.
