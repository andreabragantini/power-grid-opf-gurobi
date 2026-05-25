"""Centralized runtime defaults for dataset and solver configuration."""

import os


# Root data directory containing case-study folders.
DATA_ROOT = os.getenv('OPF_DATA_ROOT', 'data')
# Active case selected at runtime (micro to large systems).
CASE_NAME = os.getenv('OPF_CASE_NAME', 'IEEE_3bus')

filepath = ''
nodefile = ''
linefile = ''
generatorfile = ''
windfarms_file = ''
other_file = ''

# Legacy optional load file support.
load_file = ''

# Value of lost load placeholder for future formulations.
VOLL = 1000
LOAD_SCALER = float(os.getenv('OPF_LOAD_SCALER', '1.0'))
DEFAULT_SBASE = 100.0


def refresh_from_env():
	"""Refresh data paths based on current environment variables."""
	global DATA_ROOT, CASE_NAME
	global filepath, nodefile, linefile, generatorfile, windfarms_file, other_file, load_file

	DATA_ROOT = os.getenv('OPF_DATA_ROOT', 'data')
	CASE_NAME = os.getenv('OPF_CASE_NAME', 'IEEE_3bus')
	global LOAD_SCALER
	LOAD_SCALER = float(os.getenv('OPF_LOAD_SCALER', '1.0'))

	filepath = os.path.join(DATA_ROOT, CASE_NAME)
	nodefile = os.path.join(filepath, 'buses.csv')
	linefile = os.path.join(filepath, 'branches.csv')
	generatorfile = os.path.join(filepath, 'generators.csv')
	windfarms_file = os.path.join(filepath, 'windfarms.csv')
	other_file = os.path.join(filepath, 'other.csv')
	load_file = os.path.join(filepath, 'load_1period.csv')


# Initialize path variables at import time.
refresh_from_env()

