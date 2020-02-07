import argparse
import networkx as nx
from bokeh.io import show, output_file
from bokeh.models import Plot, Range1d, MultiLine, Circle, HoverTool, TapTool, BoxSelectTool, BoxZoomTool, ResetTool, WheelZoomTool
from bokeh.models.graphs import from_networkx, NodesAndLinkedEdges, EdgesAndLinkedNodes
import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
import copy

def readConjuntos(filename):
    conjuntos = []
    f = open(filename,'rt')
    line = f.readline().strip().lower()
    while line!='':
        conjuntos.append(list(map(str, line.split(', '))))
        line = f.readline().strip().lower()
    return conjuntos

def getMatrix(subsets, tags):
    N = len(tags)
    dict_ = {tags[t]:t for t in range(N)}
    matriz = np.zeros((N,N))
    for C in subsets:
        n = len(C)
        for i in range(n-1):
            for j in range(i+1,n):
                if (C[i] in tags) and (C[j] in tags):
                    matriz[dict_[C[i]]][dict_[C[j]]] += 1
                    matriz[dict_[C[j]]][dict_[C[i]]] += 1
    return matriz

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
    dffrq = pd.DataFrame(data_frq.items(), columns=['ht','frq'])
    dffrq = dffrq.sort_values(by='frq', ascending=False)
    if min_frq > 1:
        return dffrq.query("frq>="+str(min_frq)+"").reset_index(drop=True)
    else: 
        return dffrq.reset_index(drop=True)

def createByParameters(filename, nodeThreshold=1, edgeThreshold=0):
    conjuntos = readConjuntos(filename)
    dict_hs = getHashtagsWithFrequency(conjuntos)
    
    query = setMinFrequency(dict_hs, nodeThreshold)

    matriz = getMatrix(conjuntos,query.ht.values)
    
    if edgeThreshold:
        adjm = np.where(matriz < edgeThreshold, 0, matriz)
    else:
        adjm = matriz

    subgraphs =  graphNetwork(adjm,query)
    
    return subgraphs

def getSubgraphs(G):
    ccs = list(nx.connected_component_subgraphs(G))
    subgraphs = pd.DataFrame(columns=['nodes','subgraph'])
    for i in range(len(ccs)):
        df1 = pd.DataFrame(list(ccs[i].nodes), columns=['nodes'])
        df1['subgraph'] = i
        subgraphs = subgraphs.append(df1, ignore_index=True)
    return subgraphs

def graphNetwork(adjm,data):
    G = nx.from_numpy_matrix(adjm)
    data['degree'] = list(dict(G.degree).values())
    subgraphs = getSubgraphs(G)
    subgraphs = data.join(subgraphs.set_index('nodes'))

    graph_plot = Plot(plot_width=800, plot_height=800,
                x_range=Range1d(-1.1, 1.1), y_range=Range1d(-1.1, 1.1))
    
    graph_plot.title.text = "Graph.\nTotal Nodes: %i\nTotal Edges: %i\t Total subgraphs:%i"%(G.number_of_nodes(),
    G.number_of_edges(), len(subgraphs.subgraph.unique()))

    node_hover_tool = HoverTool(tooltips=[("hashtag", "@hashtag"),("freq", "@frequency"),('degree', '@degree'), ('subgraph', '@subgraph')])
    graph_plot.add_tools(node_hover_tool, BoxZoomTool(), ResetTool(),WheelZoomTool())
    
    graph_renderer = from_networkx(G, nx.spring_layout, scale=1, center=(0, 0))
    graph_renderer.node_renderer.glyph = Circle(size=18, fill_color='#277bb6')
    graph_renderer.node_renderer.hover_glyph = Circle(size=18, fill_color='#E84A5F')
    graph_renderer.node_renderer.glyph.properties_with_values()
    graph_renderer.edge_renderer.glyph = MultiLine(line_color="gray", line_alpha=0.7, line_width=0.3)
    graph_renderer.edge_renderer.hover_glyph = MultiLine(line_color='#e09e8f', line_width=3)
    graph_renderer.node_renderer.data_source.data['hashtag'] = subgraphs.ht.values
    graph_renderer.node_renderer.data_source.data['frequency'] = subgraphs.frq.values
    graph_renderer.node_renderer.data_source.data['degree'] = subgraphs.degree.values
    graph_renderer.node_renderer.data_source.data['subgraph'] = subgraphs.subgraph.values


    graph_renderer.inspection_policy = NodesAndLinkedEdges()
    graph_renderer.selection_policy = NodesAndLinkedEdges()
    graph_plot.toolbar.active_inspect = [node_hover_tool]
    graph_plot.renderers.append(graph_renderer)

    #output_file(path+topic+"_graph_N"+str(nodeThresh)+'E'+str(edgeThresh)+".html")

    show(graph_plot)
    
    subgraphs = subgraphs.sort_values(by='subgraph')
    return subgraphs
    #subgraphs.to_csv(path+topic+'_subgraphs_N'+str(nodeThresh)+'E'+str(edgeThresh)+'.csv')
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Graphs")
    parser.add_argument('--sets', type=str, help='input sets of hastags')
    parser.add_argument('--frq', default=None, type=int, help='input min freq a hashtag appears')
    parser.add_argument('--mw', default=None, type=int, help='input min weight of the network')
    args = parser.parse_args()
    
    conjuntos = readConjuntos(args.sets)
    createByParameters(conjuntos, args.frq, args.mw)
