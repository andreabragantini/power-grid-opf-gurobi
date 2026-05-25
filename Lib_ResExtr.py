# -*- coding: utf-8 -*-
"""
Created on Wed Feb 15 11:05:23 2017

@author: stde
"""

import pandas as pd


def build_results_OPF(self):
    
    generators = self.data.generators
    windfarms = self.data.windfarms 
    AC_lines = self.data.AC_lines
    nodes = self.data.nodes
    
    self.results.Pgen = pd.DataFrame(
        [self.variables.Pgen[i].x for i in generators], index=generators, columns=['Pgen'])
        
    self.results.WindOPF = pd.DataFrame(
        [self.variables.WindOPF[j].x for j in windfarms], index=windfarms, columns=['WindGen'])
       
    self.results.lineflow_AC_OPF = pd.DataFrame(
        [[self.variables.lineflow_AC_OPF[l].x] for l in AC_lines], index=AC_lines, columns=['AC_flow'])
       
    self.results.nodeangle = pd.DataFrame(
        [[self.variables.nodeangle[n].x] for n in nodes], index=nodes, columns=['Voltage'])