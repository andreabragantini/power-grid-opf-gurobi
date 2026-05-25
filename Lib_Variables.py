# -*- coding: utf-8 -*-
"""
@author: andrea
"""
import gurobipy as gb



#==============================================================================
# OPF variables
#==============================================================================

def build_variables_OPF(self):      

    m = self.model
    var = self.variables
    generators = self.data.generators
    windfarms = self.data.windfarms 
    nodes = self.data.nodes      
                     
   # Dispatchable generators
    var.Pgen = {}
    for i in generators:
        var.Pgen[i] = m.addVar(lb=0.0, name = 'Pgen({0})'.format(i))
              
   # Non-Dispatchable generators (Wind)
    var.WindOPF = {}
    for j in windfarms:
        var.WindOPF[j] = m.addVar(lb=0.0, name = 'WindOPF({0})'.format(j))
                        
   # Nodal phase angles  
    var.nodeangle = {}
    for n in nodes:
        var.nodeangle[n] = m.addVar(lb=-gb.GRB.INFINITY, ub=gb.GRB.INFINITY, name='nodeangle({0})'.format(n))


    m.update()
	
    # Slack bus setting
    for n in self.data.slackbuses:
        var.nodeangle[n].ub = 0
        var.nodeangle[n].lb = 0

    # AC line flow                
    var.lineflow_AC_OPF = {}
    for l in self.data.AC_lines: 
        var.lineflow_AC_OPF[l] = m.addVar(lb=-gb.GRB.INFINITY, ub=gb.GRB.INFINITY, name='lineflow_AC_OPF({0})'.format(l))
          
    m.update()
        
       
