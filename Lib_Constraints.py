# -*- coding: utf-8 -*-
"""
Created on Wed Sep 07 19:00:51 2016

@author: stde
"""
import gurobipy as gb
import math

    
#===========================================================================
# OPF problem constraints
#==============================================================================

def build_PowerBalOPF_constr(self):
    PowerBalOPF = {}
    var = self.variables
    
    for n in self.data.nodes:
        PowerBalOPF[n] = self.model.addConstr(
            gb.quicksum(var.WindOPF[w] for w in self.data.Map_N2Ws[n]) +
            gb.quicksum(var.Pgen[g] for g in self.data.Map_N2Gs[n]) ==
            self.data.load.Load[n] +
            gb.quicksum(var.lineflow_AC_OPF[l] for l in self.data.nodetooutlines[n]) -
            gb.quicksum(var.lineflow_AC_OPF[l] for l in self.data.nodetoinlines[n]),
            name='Power_Balance_OPF({0})'.format(n))

    
    return PowerBalOPF


def build_PmaxOPF_constr(self):
    PmaxOPF = {}
    m = self.model
    var = self.variables    
    generators = self.data.generators
    gendata = self.data.generatorinfo
    
    for gen in generators:  
            PmaxOPF[gen] = m.addConstr(
                var.Pgen[gen] <= gendata.capacity[gen],
                name='Pmax_OPF({0})'.format(gen))                

    return PmaxOPF
        
def build_PminOPF_constr(self):
    PminOPF = {}
    var = self.variables
    m = self.model
    generators = self.data.generators   
        
    for gen in generators:
        PminOPF[gen] = m.addConstr(
            var.Pgen[gen] >= 0,
            name='Pmin_OPF({0})'.format(gen))
                
    return PminOPF
        
def build_WindmaxOPF_constr(self):
    WindmaxOPF = {}
    var = self.variables
    windfarms = self.data.windfarms
    wfdata = self.data.windinfo
	
    for j in windfarms:
        WindmaxOPF[j] = self.model.addConstr(
            var.WindOPF[j] <= wfdata.capacity[j],
            name='Wind_Max_OPF({0})'.format(j))
                
    return WindmaxOPF


def build_flow_to_angleOPF_constr(self):
    var = self.variables
    flow_to_angleOPF = {}
    for l in self.data.AC_lines:
        n1, n2 = l
        flow_to_angleOPF[l] = self.model.addConstr(
            var.lineflow_AC_OPF[l] ==
            self.data.Sbase*self.data.lineadmittance[l]*(var.nodeangle[n1] - var.nodeangle[n2]),
            name='Line_flow_definition_OPF{0}'.format(l))
    return flow_to_angleOPF
    
	# DC approximation for power flows is used
	
def build_flow_lim_OPF_constr(self):   
    var = self.variables
    flow_lim_upper_AC_OPF={}
    flow_lim_lower_AC_OPF={}
     
     
    for l in self.data.AC_lines:         
         flow_lim_upper_AC_OPF[l] = self.model.addConstr(
         var.lineflow_AC_OPF[l] <=  self.data.linelimit[l],
         name = 'Line_flow_upper_limit_AC_OPF{0}'.format(l))
         
         flow_lim_lower_AC_OPF[l] = self.model.addConstr(
         var.lineflow_AC_OPF[l] >= -self.data.linelimit[l],
         name = 'Line_flow_lower_limit_AC_OPF{0}'.format(l))        

    return flow_lim_upper_AC_OPF, flow_lim_lower_AC_OPF
                
def build_angle_OPF_constr(self):
    var = self.variables
    angle_lim_upper_OPF={}
    angle_lim_lower_OPF={}
    
    for n in self.data.nodes:
        angle_lim_upper_OPF[n] = self.model.addConstr(
        var.nodeangle[n] <= math.pi,
        name = 'Angle_lim_upper{0}'.format(n))

    for n in self.data.nodes:
        angle_lim_lower_OPF[n] = self.model.addConstr(
        var.nodeangle[n] >= -math.pi,
        name = 'Angle_lim_upper{0}'.format(n))

    return angle_lim_lower_OPF, angle_lim_upper_OPF
