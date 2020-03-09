#!/usr/bin/env python
# coding: utf-8
# version 6.1
#

# update getMatrix(), graphNetwork(), createByParameters
# remove updateSubsets(), removeIsle
# added updateMatrix(), removeIsolates(), removeEdges(thres)

import argparse
import networkx as nx
from bokeh.io import show, output_file, curdoc
from bokeh.models import Plot, Range1d, MultiLine, Circle, HoverTool, TapTool, BoxSelectTool, BoxZoomTool, ResetTool, WheelZoomTool
from bokeh.models.graphs import from_networkx, NodesAndLinkedEdges, EdgesAndLinkedNodes
from bokeh.themes import built_in_themes
import bokeh.palettes as bp
import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
import unicodedata
import random

def removeAccents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode().lower()

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
    matriz = nx.adjacency_matrix(G).todense()
    return

def getComunity():
    global G, network_data
    
    colors = bp.Category20[20]
    random.shuffle(colors)
    
    #clusters = list(nx.algorithms.community.kernighan_lin_bisection(G))
    #clusters = list(nx.algorithms.community.asyn_fluidc(G,2,seed=3))
    girvan_newman = list(nx.algorithms.community.girvan_newman(G))
    for level in girvan_newman:
        if len(level) == 2:
            clusters = level
            break
        else:
            clusters = girvan_newman[0]
            
    partition = {}
    for i in range(len(clusters)):
        for c in clusters[i]:
            partition[c] = i
            
    partition_data=pd.DataFrame(partition.items(), columns=['node','community'])
    partition_data['color']=''
    for i, row in partition_data.iterrows():
        partition_data.loc[i,'color'] = colors[partition[int(row.node)]]
        
    network_data = network_data.join(partition_data.set_index('node'))
    
    if list(nx.articulation_points(G)):
        for ap in list(nx.articulation_points(G)):
            network_data.loc[ap,'color']='#ffffff'
            network_data.loc[ap,'community']=-1
            
    
    return

def removeBridges():
    global G, matriz
    bridges = list(nx.algorithms.bridges(G))
    G.remove_edges_from(bridges)
    updateMatrix()
    return

def removeNoiseInGraph():
    removeBridges()
    removeIsolates()
    updateMatrix()
    return

def graphNetwork():
    global network_data, matriz, G
    removeNoiseInGraph()
    getComunity()
    network_data['degree'] = list(dict(G.degree).values())
    network_data = network_data.join(getSubgraphs(G).set_index('nodes'))
    network_data['strength'] = list(np.array(matriz.sum(axis=0))[0])
    
    curdoc().theme = 'dark_minimal'
    graph_plot = Plot(plot_width=1600, plot_height=900,
                x_range=Range1d(-1.1, 1.1), y_range=Range1d(-1.1, 1.1))
    
    graph_plot.title.text = "Graph.\nTotal Nodes: %i\nTotal Edges: %i"%(G.number_of_nodes(), G.number_of_edges())

    node_hover_tool = HoverTool(tooltips=[("hashtag", "@hashtag"),("freq", "@frequency"),('degree', '@degree'),
                                          ('strength','@strength'),('subgraph', '@subgraph'),('community', '@community'),
                                          ('ix', '@ix')])
    
    graph_plot.add_tools(node_hover_tool, BoxZoomTool(), ResetTool(),WheelZoomTool())
    
    graph_renderer = from_networkx(G, nx.spring_layout, scale=1, center=(0, 0))
    graph_renderer.node_renderer.glyph = Circle(size='size', fill_color='colors')
    graph_renderer.node_renderer.hover_glyph = Circle(size=18, fill_color='#E84A5F')
    graph_renderer.node_renderer.glyph.properties_with_values()
    graph_renderer.edge_renderer.glyph = MultiLine(line_color="#f2f2f2", line_alpha=0.8, line_width=0.4)
    graph_renderer.edge_renderer.hover_glyph = MultiLine(line_color='#e09e8f', line_width=3)
    graph_renderer.node_renderer.data_source.data['hashtag'] = network_data.ht.values
    graph_renderer.node_renderer.data_source.data['frequency'] = network_data.frq.values
    graph_renderer.node_renderer.data_source.data['degree'] = network_data.degree.values
    graph_renderer.node_renderer.data_source.data['subgraph'] = network_data.subgraph.values
    graph_renderer.node_renderer.data_source.data['ix'] = list(network_data.index)
    graph_renderer.node_renderer.data_source.data['strength'] = network_data.strength.values
    graph_renderer.node_renderer.data_source.data['size'] = np.log((network_data.degree.values+1)*3)*6
    
    if 'color' in network_data.keys():
            graph_renderer.node_renderer.data_source.data['colors'] = network_data.color.values
    else:
         graph_renderer.node_renderer.data_source.data['colors'] = ['red']*G.number_of_nodes()
    if 'community' in network_data.keys():
        graph_renderer.node_renderer.data_source.data['community'] = network_data.community.values
    else:
        graph_renderer.node_renderer.data_source.data['community'] = ['NONE']*G.number_of_nodes()


    graph_renderer.inspection_policy = NodesAndLinkedEdges()
    graph_renderer.selection_policy = NodesAndLinkedEdges()
    graph_plot.toolbar.active_inspect = [node_hover_tool]
    graph_plot.renderers.append(graph_renderer)
    
    graph_plot.background_fill_color = '#0d0d0d'
    graph_plot.background = 'black'
    graph_plot.border_fill_color = '#1a1a1a'
    output_file("graph.html")

    show(graph_plot)
    return

def createByParameters(filename, nodeThreshold=1, edgeThreshold=None, isolates=1):
    global network_data, conjuntos, matriz, G, community_data
    
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

    community_data = network_data[['ht','community']]

    return

global network_data, conjuntos, matriz, byn, G, comunity_data
network_data = pd.DataFrame()
comunity_data = pd.DataFrame()
conjuntos = []
matriz = np.array([])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="graphnetworks")
        
    #explorar

    parser.add_argument('--sets', default=None, type=str, help='input .txt with hashtags subsets')
    parser.add_argument('--nt', default=2, type=int, help='set min node threshold for of graph')
    parser.add_argument('--et', default=None, type=int, help='set min edge threshold of graph')
    parser.add_argument('--i', default=1, type=float, help='remove isolate nodes')
    
    args = parser.parse_args()
    
    createByParameters(args.sets, args.nt,  args.et, args.i)
        
    network_data.to_csv('./_subgraphs_N'+str(args.nt)+'E'+str(args.et)+'.csv')

    comunity_data.to_csv('./ht_comunities.csv', index=False)




