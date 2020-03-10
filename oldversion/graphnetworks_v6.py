#!/usr/bin/env python
# coding: utf-8
# version 6
#

# update getMatrix(), graphNetwork(), createByParameters
# remove updateSubsets(), removeIsle
# added updateMatrix(), removeIsolates(), removeEdges(thres)

import argparse
import networkx as nx
from bokeh.io import show, output_file
from bokeh.models import Plot, Range1d, MultiLine, Circle, HoverTool, TapTool, BoxSelectTool, BoxZoomTool, ResetTool, WheelZoomTool
from bokeh.models.graphs import from_networkx, NodesAndLinkedEdges, EdgesAndLinkedNodes
import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd

def readConjuntos(filename):
    global conjuntos
    f = open(filename,'rt')
    line = f.readline().strip().lower()
    while line!='':
        conjuntos.append(list(map(str, line.split(', '))))
        line = f.readline().strip().lower()
    return

def getHashtagsWithFrequency(conjuntos):
    d_freq = {}
    for subset in conjuntos:
        for item in subset:
            if item in d_freq.keys():
                d_freq[item] += 1
            else:
                d_freq[item] = 1
    return d_freq

def setMinFrequency(data_frq,min_frq):
    global network_data

    network_data = pd.DataFrame(data_frq.items(), columns=['ht','frq'])
    network_data = network_data.sort_values(by='frq', ascending=False)
    if min_frq > 1:
         network_data = network_data.query("frq>="+str(min_frq)+"").reset_index(drop=True)
    else: 
         network_data = network_data.reset_index(drop=True)
    return

def getMatrix():
    global conjuntos, network_data, matriz
        
    tags = network_data.ht.values
    N = len(tags)
    dict_ = {tags[t]:t for t in range(N)}
    matriz = np.zeros((N,N))
    v=0
    for C in conjuntos:
        C = list(set(C))
        n = len(C)
        if n>1:
            for i in range(n-1):
                for j in range(i+1,n):
                    if (C[i] in tags) and (C[j] in tags):
                        matriz[dict_[C[i]]][dict_[C[j]]] += 1
                        matriz[dict_[C[j]]][dict_[C[i]]] += 1
    return 

def removeEdges(thres):
    global G, matriz
    
    for i in range(1,thres):
        while list(np.where(np.triu(matriz)==1)[0]):
            ebunch = np.where(np.triu(matriz)==i)
            ebunch = list(zip(ebunch[0],ebunch[1]))
            G.remove_edges_from(ebunch)
            updateMatrix()
    return

def removeIsolates():
    global network_data, G
    
    isolates = list(nx.isolates(G))
    G.remove_nodes_from(isolates)
    for isolate in isolates:
        network_data = network_data.drop(index=isolate)
    return


def getSubgraphs(G):
    ccs = list(nx.connected_component_subgraphs(G))
    subgraphs = pd.DataFrame(columns=['nodes','subgraph'])
    for i in range(len(ccs)):
        df1 = pd.DataFrame(list(ccs[i].nodes), columns=['nodes'])
        df1['subgraph'] = i
        subgraphs = subgraphs.append(df1, ignore_index=True)
        
    return subgraphs

def updateMatrix():
    global matriz, G
    matriz = nx.adjacency_matrix(G)
    matriz = matriz.todense()
    
    return

def graphNetwork():
    global network_data, matriz, G
    
    network_data['degree'] = list(dict(G.degree).values())
    network_data = network_data.join(getSubgraphs(G).set_index('nodes'))
    network_data['strength'] = list(np.array(matriz.sum(axis=0))[0])
    graph_plot = Plot(plot_width=800, plot_height=800,
                x_range=Range1d(-1.1, 1.1), y_range=Range1d(-1.1, 1.1))
    
    graph_plot.title.text = "Graph.\nTotal Nodes: %i\nTotal Edges: %i\t Total subgraphs:%i"%(G.number_of_nodes(),
    G.number_of_edges(), len(network_data.subgraph.unique()))

    node_hover_tool = HoverTool(tooltips=[("hashtag", "@hashtag"),("freq", "@frequency"),('degree', '@degree'),
                                          ('strength','@strength'),('subgraph', '@subgraph'),('ix', '@ix')])
    graph_plot.add_tools(node_hover_tool, BoxZoomTool(), ResetTool(),WheelZoomTool())
    
    graph_renderer = from_networkx(G, nx.spring_layout, scale=1, center=(0, 0))
    graph_renderer.node_renderer.glyph = Circle(size=18, fill_color='#277bb6')
    graph_renderer.node_renderer.hover_glyph = Circle(size=18, fill_color='#E84A5F')
    graph_renderer.node_renderer.glyph.properties_with_values()
    graph_renderer.edge_renderer.glyph = MultiLine(line_color="gray", line_alpha=0.7, line_width=0.3)
    graph_renderer.edge_renderer.hover_glyph = MultiLine(line_color='#e09e8f', line_width=3)
    graph_renderer.node_renderer.data_source.data['hashtag'] = network_data.ht.values
    graph_renderer.node_renderer.data_source.data['frequency'] = network_data.frq.values
    graph_renderer.node_renderer.data_source.data['degree'] = network_data.degree.values
    graph_renderer.node_renderer.data_source.data['subgraph'] = network_data.subgraph.values
    graph_renderer.node_renderer.data_source.data['ix'] = list(network_data.index)
    graph_renderer.node_renderer.data_source.data['strength'] = network_data.strength.values

    graph_renderer.inspection_policy = NodesAndLinkedEdges()
    graph_renderer.selection_policy = NodesAndLinkedEdges()
    graph_plot.toolbar.active_inspect = [node_hover_tool]
    graph_plot.renderers.append(graph_renderer)

    #output_file(path+topic+"_graph_N"+str(nodeThresh)+'E'+str(edgeThresh)+".html")

    show(graph_plot)
    return

def createByParameters(filename, nodeThreshold=1, edgeThreshold=None, isolates=1):
    global network_data, conjuntos, matriz, G
    
    readConjuntos(filename)
    
    dict_hs = getHashtagsWithFrequency(conjuntos)
    
    setMinFrequency(dict_hs, nodeThreshold)
    
    getMatrix()
    
    G = nx.from_numpy_matrix(matriz)

    if edgeThreshold:
        removeEdges(edgeThreshold)
        
    if isolates==0:
        removeIsolates()
        
    updateMatrix()
        
    graphNetwork()

    return

global network_data, conjuntos, matriz, byn, G
network_data = pd.DataFrame()
conjuntos = []
matriz = np.array([])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="graphnetworks")
        
    #explorar

    parser.add_argument('--sets', default=None, type=str, help='input .txt with hashtags subsets')
    parser.add_argument('--nt', default=1, type=int, help='set min node threshold for of graph')
    parser.add_argument('--et', default=None, type=int, help='set min edge threshold of graph')
    parser.add_argument('--i', default=1, type=float, help='remove isolate nodes')
    
    args = parser.parse_args()
    
    createByParameters(args.sets, args.nt,  args.et, args.i)
        
    network_data.to_csv(path+'/'+topic+'_subgraphs_N'+str(args.nt)+'E'+str(args.et)+'.csv')




