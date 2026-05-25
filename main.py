# -*- coding: utf-8 -*-
"""
@author: andrea
"""

import gurobipy as gb
import Data_Load
import Lib_Variables
import Lib_ObjFnct
import Lib_NetworkChart
import Build_constraints
import Lib_ResExtr
from tabulate import tabulate

# Class which can have attributes set
class expando(object):
    pass


class DCOPF():
    def __init__(self):        
        self.data = expando()        
        self.variables = expando()
        self.constraints = expando()
        self.results = expando()
        self._load_data()            
        self._build_model_OPF()
                      
                   
    def _load_data(self):
        Data_Load._load_network(self)     
        Data_Load._load_generator_data(self)
        Data_Load._load_wind_data(self)
        Data_Load._load_intial_data(self)
        self.data.Sbase = getattr(self.data, 'Sbase', 100)
        
    def _build_model_OPF(self):
        self.model = gb.Model()        

        Lib_Variables.build_variables_OPF(self)
        Build_constraints._build_constraints_OPF(self)   
        Lib_ObjFnct.build_objective_OPF(self)
        
        self.model.update()
        
    def build_results(self):
        Lib_ResExtr.build_results_OPF(self)
        
    def build_chart(self):
        Lib_NetworkChart.build_networkchart(self)
        
    def optimize(self):
        self.model.optimize()        
        
        
def run():
    OPF = DCOPF()
    # mDA.model.params.OutputFlag = 0
    OPF.optimize()
    OPF.build_results()
    OPF.build_chart()

    print('##############################')
    print('#####  DC OPF - Results  #####')
    print('##############################')

    print(tabulate(OPF.results.Pgen, headers='keys', tablefmt='psql'))
    print(tabulate(OPF.results.WindOPF, headers='keys', tablefmt='psql'))
    print(tabulate(OPF.results.lineflow_AC_OPF, headers='keys', tablefmt='psql'))
    print(tabulate(OPF.results.nodeangle, headers='keys', tablefmt='psql'))


if __name__ == '__main__':
    run()

'''
# Print Latex code
print(OPF.results.Pgen.to_latex())
print(OPF.results.WindOPF.to_latex())
print(OPF.results.lineflow_AC_OPF.to_latex())
print(OPF.results.nodeangle.to_latex())
'''