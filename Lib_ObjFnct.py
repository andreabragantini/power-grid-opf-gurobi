# -*- coding: utf-8 -*-
"""
Created on Sat Oct 01 13:37:04 2016

Library of Objective Functions

@author: stde
"""
import gurobipy as gb


 # Objective Function - OPF        
def build_objective_OPF(self):        
    
    generators = self.data.generators
    gendata = self.data.generatorinfo   

    m = self.model
           
    m.setObjective(
        gb.quicksum(gendata.lincost[i]*self.variables.Pgen[i] for i in generators),        
        gb.GRB.MINIMIZE)
        
