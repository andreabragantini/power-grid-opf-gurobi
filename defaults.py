import os


DATA_ROOT = os.getenv('OPF_DATA_ROOT', 'data')
CASE_NAME = os.getenv('OPF_CASE_NAME', 'IEEE_3bus')

filepath = os.path.join(DATA_ROOT, CASE_NAME)

nodefile = os.path.join(filepath, 'buses.csv')
linefile = os.path.join(filepath, 'branches.csv')
generatorfile = os.path.join(filepath, 'generators.csv')
windfarms_file = os.path.join(filepath, 'windfarms.csv')
other_file = os.path.join(filepath, 'other.csv')

# Legacy optional load file support.
load_file = os.path.join(filepath, 'load_1period.csv')

VOLL = 1000
DEFAULT_SBASE = 100.0

