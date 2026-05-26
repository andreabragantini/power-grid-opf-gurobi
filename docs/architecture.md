# Architecture Overview

This repository is organized to keep OPF math transparent while enabling incremental growth.

## Current status

- Implemented formulations:
  - DC OPF (`src/dc_opf`)
  - AC LP Lossless OPF (`src/ac_lp_lossless`)
- Planned formulations (placeholders created):
  - `src/ac_lp_losses_p`
  - `src/ac_lp_losses_pq`
  - `src/fbs_opf`

## Layers

- `src/common`: shared context objects and data loading/harmonization
- `src/common/output_manager.py`: run artifact persistence and KPI history tracking
- `src/dc_opf`: variables, constraints, objective, results, chart, model
- `src/formulation_registry.py`: formulation factory used by `main.py`

## Data conventions

Each case folder under `data/` should contain:

- `buses.csv`
- `branches.csv`
- `generators.csv`
- optional `windfarms.csv`
- optional `other.csv` with `BaseMVA`

### Slack bus policy

- Use `Bus_Type = 3` when present
- If missing, default to first bus as slack and others as PQ

## Why this structure

- Keeps equations readable and close to implementation
- Avoids overengineering while creating stable extension points
- Allows reproducible case-by-case execution via environment variables
