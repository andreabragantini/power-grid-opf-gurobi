# -*- coding: utf-8 -*-
"""
Created on Fri May  3 17:48:40 2019

@author: andrbrag
"""


import plotly
import plotly.graph_objs as go
import matplotlib.pyplot as plt

import networkx as nx

def build_networkchart(self):
    G = nx.Graph()
    G.add_nodes_from(self.data.nodes)
    G.add_edges_from(self.data.lineorder)
    nx.draw(G, with_labels=True)