import networkx as nx
from bokeh.io import show, output_file, curdoc
from bokeh.models import Plot, Range1d, MultiLine, Circle, HoverTool,BoxSelectTool, BoxZoomTool, ResetTool, WheelZoomTool, Legend, LegendItem
from bokeh.models.graphs import from_networkx, NodesAndLinkedEdges, EdgesAndLinkedNodes
from bokeh.themes import built_in_themes
import numpy as np
import pandas as pd
import unicodedata
import random
import sknetwork as skn
from scipy.cluster.hierarchy import is_valid_linkage
import re

def removeAccents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode().lower()

def readConjuntos(filename):
    conjuntos = []
    f = open(filename,'rt')
    line = f.readline().strip().lower()
    while line!='':
        conjuntos.append([removeAccents(i) for i in list(map(str, line.split(', ')))])
        line = f.readline().strip().lower()
    return conjuntos

def getFileAndPath(text):
    path = re.findall(r'.*[/$]',text)[0]
    file = text.replace(path, '').replace('.txt','')
    
    return [path,file]
    
def getHashtagsWithFrequency(conjuntos):
    d_freq = {}
    for subset in conjuntos:
        for item in subset:
            if item in d_freq.keys():
                d_freq[item] += 1
            else:
                d_freq[item] = 1
    return d_freq

def getMatrix(conjuntos, tags):
    N = len(tags)
    dict_ = {tags[t]:t for t in range(N)}
    matriz = np.zeros((N,N))
    for C in conjuntos:
        C = list(set(C))
        n = len(C)
        if n>1:
            for i in range(n-1):
                for j in range(i+1,n):
                    if (C[i] in tags) and (C[j] in tags) and C[i] != C[j]:
                        matriz[dict_[C[i]]][dict_[C[j]]] += 1
                        matriz[dict_[C[j]]][dict_[C[i]]] += 1
    return matriz

def random_color():
        rand = lambda: random.randrange(105,252)
        return '#%02X%02X%02X' % (rand(), rand(), rand())

class HashtagsData:
    
    def __init__(self, source, nodeThres, edgeThres, iso):
        self.source = source
        self._nodeThres = (nodeThres,True)
        self._edgeThres = (edgeThres, True)
        self.conjuntos = readConjuntos(self.source)
        self.hts_dict = getHashtagsWithFrequency(self.conjuntos)
        self._path = getFileAndPath(self.source)
        self.isolates = iso
        
        self._setup()

        
    def _setup(self):

        if self._nodeThres[1]:
            self.data = pd.DataFrame(self.hts_dict.items(), columns=['ht','frq']
                            ).sort_values(by='frq',ascending=False).reset_index(drop=True)
            
            self._nodeThres = (self.nodeThres,False)
                        
            self._community = False
            
            self._methood = None
            
            self.partition = None


            if self.nodeThres > 1:
                self.data = self.data.query("frq >= @self.nodeThres")

            self._matrix = getMatrix(self.conjuntos, self.data.ht.values)

            self.G = nx.from_numpy_matrix(self._matrix)
            
            self._edgeThres = (self.edgeThres, True)


        if self._edgeThres[1]:
            
            self._edgeThres = (self.edgeThres, False)

            self._removeEdges()
            
        if self.isolates:
            self.removeBridges()
            self.removeIsolates()
            
            
        self._updateInfo()
        
        return
        
    def _removeEdges(self):
        
        for i in range(1,self.edgeThres):
            ebunch = np.where(np.triu(self.matrix)==i)
            ebunch = list(zip(ebunch[0],ebunch[1]))

            self.G.remove_edges_from(ebunch)
            self.removeBridges()
            self.removeIsolates()
        return
        
    def _updateInfo(self): 
        self.data['degree'] = list(dict(self.G.degree).values())
        self.data['strength'] = list(np.array(self.matrix.sum(axis=0))[0])
    
    def removeBridges(self):
        
        bridges = list(nx.algorithms.bridges(self.G))
        self.G.remove_edges_from(bridges)
                
        return
            
        
    def removeIsolates(self):
        isolates = list(nx.isolates(self.G))
        self.G.remove_nodes_from(isolates)
        
        if isolates:
            self.data = self.data.drop(isolates)
            self.data = self.data.reset_index(drop=True)
        
        self.G = nx.from_numpy_matrix(self.matrix)
        
    @property
    def community(self):
        return self._community
    
    @property
    def matrix(self):
        return nx.adjacency_matrix(self.G).todense()
    
    @property
    def nodeThres(self):
        return self._nodeThres[0]

    @nodeThres.setter
    def nodeThres(self, nodeThres):
        if nodeThres != self.nodeThres:
            self._nodeThres = (nodeThres, True)
            self._setup()
            
    @property

    def edgeThres(self):
        return self._edgeThres[0]
    
    @edgeThres.setter
    def edgeThres(self, edgeThres):
        if edgeThres > self.edgeThres:
            self._edgeThres = (edgeThres, True)
            self._setup()

    def getCommunity(self):
        self._community = True
        
        paris = skn.hierarchy.Paris(engine='python')
        dendrogram = paris.fit_transform(nx.to_scipy_sparse_matrix(self.G))
        
        if is_valid_linkage(dendrogram):
            labels = skn.hierarchy.straight_cut(dendrogram)
            self._methood = 'Paris'
        else:
            louvain = skn.clustering.Louvain(engine='python')
            labels = louvain.fit_transform(nx.to_scipy_sparse_matrix(self.G))
            self._methood = 'Louvian'
        
        number_of_colors = labels.max()
        colors = [random_color() for i in range(number_of_colors+1)]
        
        self.data['community'] = labels
        self.data['color']=''
        for i, c in enumerate(labels):
            self.data.loc[i,'color'] = colors[c]
            
        self.partition = tuple(set(self.data.query('community == @i').index) for i in self.data.community.unique())

        if list(nx.articulation_points(self.G)):
            for ap in list(nx.articulation_points(self.G)):
                self.data.loc[ap,'color'] = '#ffffff'
                self.data.loc[ap,'community'] = -1
        return
    
    def showGraph(self):

        curdoc().theme = 'dark_minimal'
        graph_plot = Plot(plot_width=1600, plot_height=900,
                    x_range=Range1d(-1.1, 1.1), y_range=Range1d(-1.1, 1.1))

        if self._methood:
             graph_plot.title.text = ("Graph %s \nTotal Nodes: %i \nTotal Edges: %i \n Node threshold:"
                        "%i \n edge threshold: %i \n Total COMM: %i  \n Method: %s"%(self._path[1], self.G.number_of_nodes(),
                        self.G.number_of_edges(), self.nodeThres, self.edgeThres, len(self.partition), self._methood))
        else:

            graph_plot.title.text = "Graph %s. \nTotal Nodes: %i \nTotal Edges: %i \n Node threshold: %i \n edge threshold: %i" %(self._path[1],
                self.G.number_of_nodes(), self.G.number_of_edges(), self.nodeThres, self.edgeThres)

        graph_renderer = from_networkx(self.G, nx.spring_layout, scale=1, center=(0, 0))
        graph_renderer.node_renderer.glyph = Circle(size='size', fill_color='colors')
        graph_renderer.node_renderer.hover_glyph = Circle(size=18, fill_color='#E84A5F')
        graph_renderer.node_renderer.glyph.properties_with_values()
        graph_renderer.edge_renderer.glyph = MultiLine(line_color="#f2f2f2", line_alpha=0.8, line_width=0.4)
        graph_renderer.edge_renderer.hover_glyph = MultiLine(line_color='#e09e8f', line_width=3)
        graph_renderer.node_renderer.data_source.data['hashtag'] = self.data.ht.values
        graph_renderer.node_renderer.data_source.data['frequency'] = self.data.frq.values
        graph_renderer.node_renderer.data_source.data['degree'] = self.data.degree.values
        graph_renderer.node_renderer.data_source.data['ix'] = list(self.data.index)
        graph_renderer.node_renderer.data_source.data['strength'] = self.data.strength.values
        graph_renderer.node_renderer.data_source.data['size'] = np.log((self.data.degree.values+1)*3)*6
        
        if self.community:

            graph_renderer.node_renderer.data_source.data['colors'] = self.data.color.values

            graph_renderer.node_renderer.data_source.data['community'] = self.data.community.values

            node_hover_tool = HoverTool(tooltips=[("hashtag", "@hashtag"),("freq", "@frequency"),('degree', '@degree'),
                                          ('strength','@strength'),('community', '@community'),
                                          ('ix', '@ix')])
        else:

            
            graph_renderer.node_renderer.data_source.data['colors'] = ['red']*self.G.number_of_nodes()
            
            node_hover_tool = HoverTool(tooltips=[("hashtag", "@hashtag"),("freq", "@frequency"),('degree', '@degree'),
                                              ('strength','@strength'),('ix', '@ix')])
            
        
        graph_plot.add_tools(node_hover_tool, BoxZoomTool(), ResetTool(),WheelZoomTool())
        
        graph_plot.toolbar.active_scroll = graph_plot.select_one(WheelZoomTool)

        graph_renderer.inspection_policy = NodesAndLinkedEdges()
        graph_renderer.selection_policy = NodesAndLinkedEdges()
        graph_plot.toolbar.active_inspect = [node_hover_tool]
        graph_plot.renderers.append(graph_renderer)

        graph_plot.background_fill_color = '#0d0d0d'
        graph_plot.background = 'black'
        graph_plot.border_fill_color = '#1a1a1a'
        
        if self.partition:        
            legend = Legend(items=[
                LegendItem(label="coverage: %f" %nx.community.coverage(self.G, self.partition), index=0),
                LegendItem(label="performance: %f" %nx.community.performance(self.G, self.partition), index=1),
                LegendItem(label="modularity: %f" %nx.community.modularity(self.G, self.partition), index=2)
                ])
            graph_plot.add_layout(legend)
        
        
        output_file(self._path[0]+"Graph_NT"+str(self.nodeThres)+"ET"+str(self.edgeThres)+".html")
        show(graph_plot)
        return
