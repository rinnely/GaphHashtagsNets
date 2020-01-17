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
    dict_ = {tags[t]:t for t in range(len(tags))}
    matriz = np.zeros((len(tags),len(tags)))
    for conjunto in copy.deepcopy(subsets):
        while conjunto:
            elemento = conjunto.pop()
            for e in conjunto:
                if e in tags and elemento in tags:
                    if e == elemento:
                        matriz[dict_[e],dict_[elemento]] =0
                        matriz[dict_[elemento],dict_[e]] =0
                    else:
                        matriz[dict_[e],dict_[elemento]] += 1
                        matriz[dict_[elemento],dict_[e]] += 1
                else:
                    pass
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
    dffrq = pd.DataFrame(data_frq.items(), columns=['hs','frq'])
    dffrq = dffrq.sort_values(by='frq', ascending=False)
    query = dffrq.query("frq>="+str(min_frq)+"")
    return query

def createByParameters(conjuntos, frq, mw):
    dict_hs = getHashtagsWithFrequency(conjuntos)
    
    if frq:
        query = setMinFrequency(dict_hs, frq)
        tags = query.hs.values
    else:
        tags = list(dict_hs.keys())
        
    matriz = getMatrix(conjuntos,tags)
    
    if mw:
        data = np.where(matriz < mw, 0, matriz)
    else:
        data = matriz

    graphNetwork(data,tags)

def graphNetwork(data,tags):
    G = nx.from_numpy_matrix(data)
    graph_plot = Plot(plot_width=800, plot_height=800,
                x_range=Range1d(-1.1, 1.1), y_range=Range1d(-1.1, 1.1))
    graph_plot.title.text = "Graph.\nTotal Nodes: %i\nTotal Edges: %i"%(G.number_of_nodes(),
G.number_of_edges())

    node_hover_tool = HoverTool(tooltips=[("hashtag", "@hashtag")])
    graph_plot.add_tools(node_hover_tool, BoxZoomTool(), ResetTool(),WheelZoomTool(), BoxSelectTool())

    graph_renderer = from_networkx(G, nx.spring_layout, scale=1, center=(0, 0))
    graph_renderer.node_renderer.glyph = Circle(size=15, fill_color='#277bb6')
    graph_renderer.node_renderer.hover_glyph = Circle(size=18, fill_color='#E84A5F')
    graph_renderer.edge_renderer.glyph = MultiLine(line_color="gray", line_alpha=0.8, line_width=0.5)
    graph_renderer.edge_renderer.hover_glyph = MultiLine(line_color='#e09e8f', line_width=3)
    graph_renderer.inspection_policy = NodesAndLinkedEdges()
    graph_renderer.selection_policy = EdgesAndLinkedNodes()
    graph_renderer.node_renderer.data_source.data['hashtag'] = tags

    graph_plot.renderers.append(graph_renderer)

    output_file("interactive_graphs.html")

    show(graph_plot)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Graphs")
    parser.add_argument('--sets', type=str, help='input sets of hastags')
    parser.add_argument('--frq', default=None, type=int, help='input min freq a hashtag appears')
    parser.add_argument('--mw', default=None, type=int, help='input min weight of the network')
    args = parser.parse_args()
    
    conjuntos = readConjuntos(args.sets)
    createByParameters(conjuntos, args.frq, args.mw)