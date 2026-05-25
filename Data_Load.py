# -*- coding: utf-8 -*-
"""
Created on Thu Sep 29 23:01:23 2016

@author: stde
"""

#==============================================================================
#  Data Loading  
#==============================================================================

import pandas as pd
import gurobipy as gb
import defaults
import os
from collections import defaultdict


def _first_existing_column(df, candidates, frame_name, required=True):
    for column in candidates:
        if column in df.columns:
            return column
    if required:
        raise ValueError(
            'Missing required column in {0}. Expected one of: {1}'.format(
                frame_name, candidates
            )
        )
    return None


def _read_optional_base_mva():
    if not os.path.exists(defaults.other_file):
        return defaults.DEFAULT_SBASE

    with open(defaults.other_file, 'r', encoding='utf-8') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            parts = line.replace(',', ' ').split()
            if len(parts) >= 2 and parts[0].lower() == 'basemva':
                return float(parts[1])

    return defaults.DEFAULT_SBASE

def _load_network(self):
    raw_nodedf = pd.read_csv(defaults.nodefile)

    node_id_col = _first_existing_column(raw_nodedf, ['ID', 'Bus_Number'], 'buses.csv')
    node_name_col = _first_existing_column(raw_nodedf, ['name', 'Bus_Name'], 'buses.csv', required=False)
    bus_type_col = _first_existing_column(raw_nodedf, ['Bus_Type'], 'buses.csv', required=False)
    p_load_col = _first_existing_column(raw_nodedf, ['load', 'LoadP', 'PD_MW'], 'buses.csv', required=False)

    nodedf = raw_nodedf.copy()
    if node_name_col is None:
        nodedf['name'] = nodedf[node_id_col]
    else:
        nodedf['name'] = nodedf[node_name_col]

    if bus_type_col is None:
        nodedf['Bus_Type'] = 1
        if not nodedf.empty:
            nodedf.loc[nodedf.index[0], 'Bus_Type'] = 3

    if p_load_col is None:
        nodedf['load'] = 0.0
    else:
        nodedf['load'] = nodedf[p_load_col]

    nodedf = nodedf.rename(columns={node_id_col: 'ID'})
    self.data.nodedf = nodedf.set_index('ID')

    raw_linedf = pd.read_csv(defaults.linefile)
    from_col = _first_existing_column(raw_linedf, ['fromNode', 'From_Bus'], 'branches.csv')
    to_col = _first_existing_column(raw_linedf, ['toNode', 'To_Bus'], 'branches.csv')
    limit_col = _first_existing_column(raw_linedf, ['limit', 'Alimit', 'RateA_MVA'], 'branches.csv', required=False)
    type_col = _first_existing_column(raw_linedf, ['type'], 'branches.csv', required=False)
    b_col = _first_existing_column(raw_linedf, ['B'], 'branches.csv', required=False)
    x_col = _first_existing_column(raw_linedf, ['BR_X_PU'], 'branches.csv', required=False)

    linedf = raw_linedf.copy()
    linedf['fromNode'] = linedf[from_col]
    linedf['toNode'] = linedf[to_col]

    if limit_col is None:
        linedf['limit'] = gb.GRB.INFINITY
    else:
        linedf['limit'] = linedf[limit_col]

    if type_col is None:
        linedf['type'] = 'AC'

    if b_col is not None:
        linedf['B'] = linedf[b_col]
    elif x_col is not None:
        linedf['B'] = linedf[x_col].apply(
            lambda x: 0.0 if abs(float(x)) < 1e-9 else 1.0 / float(x)
        )
    else:
        raise ValueError('branches.csv requires either B or BR_X_PU column')

    self.data.linedf = linedf.set_index(['fromNode', 'toNode'])

    # # Node and edge ordering
    self.data.nodeorder = self.data.nodedf.index.tolist()
    self.data.lineorder = [tuple(x) for x in self.data.linedf.index]
    # # Line limits
    self.data.linelimit = self.data.linedf['limit'].to_dict()
    
    def zero_to_inf(x):
        if x > 0.0001:
            return x
        else:
            return gb.GRB.INFINITY
    
    self.data.linelimit = {k: zero_to_inf(v) for k, v in self.data.linelimit.items()}
    self.data.lineadmittance = self.data.linedf['B'].to_dict()
    # In DC approx line addmittances Y are the same as line susceptances B (no resistance - no losses)

    self.data.nodes = self.data.nodeorder
    
    self.data.nodetooutlines = defaultdict(list)
    self.data.nodetoinlines = defaultdict(list)   

    for l in self.data.lineorder:
        self.data.nodetooutlines[l[0]].append(l)
        self.data.nodetoinlines[l[1]].append(l)
        
    if 'Bus_Type' in self.data.nodedf.columns:
        slack_candidates = self.data.nodedf[self.data.nodedf['Bus_Type'] == 3].index.tolist()
        self.data.slackbuses = slack_candidates if slack_candidates else [self.data.nodeorder[0]]
    else:
        self.data.slackbuses = [self.data.nodeorder[0]]

    # Find AC lines (zip avoids ambiguous lookups when multi-index keys repeat).
    line_types = self.data.linedf['type'].tolist()
    self.data.AC_lines = [line for line, ltype in zip(self.data.lineorder, line_types) if ltype == 'AC']

    self.data.Sbase = _read_optional_base_mva()
    
       
def _load_generator_data(self):
    raw_gendf = pd.read_csv(defaults.generatorfile)
    gen_id_col = _first_existing_column(raw_gendf, ['ID'], 'generators.csv', required=False)
    origin_col = _first_existing_column(raw_gendf, ['origin', 'Gen_Bus'], 'generators.csv')
    pmax_col = _first_existing_column(raw_gendf, ['Pmax', 'Pmax_MW'], 'generators.csv')
    lincost_col = _first_existing_column(raw_gendf, ['lincost', 'CostCoeff_1'], 'generators.csv', required=False)

    gendf = raw_gendf.copy()
    if gen_id_col is None:
        gendf['ID'] = ['g{0}'.format(i + 1) for i in range(len(gendf))]
        gen_id_col = 'ID'

    gendf['origin'] = gendf[origin_col]
    gendf['capacity'] = gendf[pmax_col]
    if lincost_col is None:
        gendf['lincost'] = 0.0
    else:
        gendf['lincost'] = gendf[lincost_col]

    self.data.generatorinfo = gendf.set_index(gen_id_col)
    self.data.generators = self.data.generatorinfo.index.tolist()
    
    # Mapping - Node (Key) to Generator (Value)      
    self.data.Map_N2Gs = defaultdict(list)
    # Mapping - Generator (Key) to Nodes (Value)       
    self.data.Map_G2Ns = defaultdict(list)      
    
    origodict = self.data.generatorinfo['origin']
    for gen, n in origodict.items():
        self.data.Map_G2Ns[gen].append(n)
        self.data.Map_N2Gs[n].append(gen)
        
     
    
            
def _load_wind_data(self):
    if not os.path.exists(defaults.windfarms_file):
        self.data.windinfo = pd.DataFrame(columns=['origin', 'capacity'])
        self.data.windfarms = []
        self.data.Map_N2Ws = defaultdict(list)
        self.data.Map_W2Ns = defaultdict(list)
        return

    self.data.windinfo = pd.read_csv(defaults.windfarms_file, index_col=0)
    self.data.windfarms = self.data.windinfo.index.tolist()
    
    # Mapping - Node (Key) to Wind Farm (Value) 
    self.data.Map_N2Ws = defaultdict(list)
    # Mapping - Wind Farm (Key) to Nodes (Value)
    self.data.Map_W2Ns = defaultdict(list)
    
    origodict = self.data.windinfo['origin']
    for w, n in origodict.items():
        self.data.Map_W2Ns[w].append(n)
        self.data.Map_N2Ws[n].append(w)
    
      
def _load_intial_data(self):
    if 'load' in self.data.nodedf.columns:
        self.data.load = pd.DataFrame(
            {'Load': self.data.nodedf['load']},
            index=self.data.nodedf.index
        )
        return

    if os.path.exists(defaults.load_file):
        self.data.load = pd.read_csv(defaults.load_file).set_index('Node')
    else:
        self.data.load = pd.DataFrame({'Load': 0.0}, index=self.data.nodedf.index)
    
	
