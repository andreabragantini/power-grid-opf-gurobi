# -*- coding: utf-8 -*-
"""
@author: andrea
"""

    
def _build_constraints_OPF(self):
    
           
    from Lib_Constraints import  \
        build_PowerBalOPF_constr, build_PmaxOPF_constr, build_PminOPF_constr, \
        build_WindmaxOPF_constr, build_flow_to_angleOPF_constr, \
        build_flow_lim_OPF_constr, build_angle_OPF_constr
        
    
    self.constraints.PowerBalOPF = build_PowerBalOPF_constr(self)  
    self.constraints.PmaxOPF = build_PmaxOPF_constr(self)
    self.constraints.PminOPF = build_PminOPF_constr(self)
    self.constraints.WindmaxOPF = build_WindmaxOPF_constr(self)
    self.constraints.flow_to_angleOPF = build_flow_to_angleOPF_constr(self)
    self.constraints.flow_lim_OPF = build_flow_lim_OPF_constr(self)
    self.constraints.angle = build_angle_OPF_constr(self)