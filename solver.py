#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 19:19:07 2019

@author: marcello
"""

import logging
import sys
import argparse
import json
import copy
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as clr

class Group:
    def __init__(self, idx, color):
        self.idx = idx
        self.color = color

    def __str__(self):
        return '%s' % (self.idx)
        #return '<Group %s Color="%s" />' % (self.idx, self.color.name)

    def __eq__(self, other):
        return self.idx == other.idx

    def __hash__(self):
        return self.idx
    
    def __lt__(self, other):
        self.idx < other.idx


class Color:
    def __init__(self, name, rgb):
        self.name = name
        self.rgb = rgb

    def __str__(self):
        return '<Color %s: %s>' % (self.name, self.rgb)

    def __eq__(self, other):
        return self.rgb == other.rgb

    def __hash__(self):
        return int(self.rgb, 16)

    def json(self):
        return [self.rgb]
    

def buildLevelGraph(levelData):
    G = nx.Graph()
    
    groupsMap = dict()
    
    for colorData in levelData['colors']:
        color = Color(colorData['name'], colorData['rgb'])
        for groupData in colorData['groups']:
            group = Group(groupData, color)
            groupsMap[groupData] = group
    
    for (g1, g2) in levelData['edges']:
        G.add_edge(groupsMap[g1], groupsMap[g2])
        #logger.info('Add edge from', g1, 'to', g2)
    
    return G


def reduceGraph(graph):
    g = copy.deepcopy(graph)

    equivalent_node_a = None
    equivalent_node_b = None
    #for (a, b) in sorted(g.edges()):
    for (a, b) in sorted(g.edges()):
        # If we have an set of nodes
        if a.color == b.color:
            equivalent_node_a = a
            equivalent_node_b = b
            # We quit immediately
            break

    # If we didn't find a node, then we return our graph immediately.
    if equivalent_node_a is None:
        return g

    # Otherwise, we need to make the processing and then return
    # reduceGraph(self) in case we missed any nodes (since we broke on first)
    a_neighs = list(nx.all_neighbors(g, equivalent_node_a))
    b_neighs = list(nx.all_neighbors(g, equivalent_node_b))
    # Remove for ease of access
    b_neighs.remove(equivalent_node_a)
    a_neighs.remove(equivalent_node_b)
    to_remove = []
    to_add = []
    for b_neighbour in b_neighs:
        if b_neighbour not in a_neighs:
            to_add.append((equivalent_node_a, b_neighbour))

        to_remove.append((equivalent_node_b, b_neighbour))

        # if a_neighbour not in b_neighs and \
                # a_neighbour != equivalent_node_b:
            # to_add.append((a_neighbour, equivalent_node_b))
        # to_remove.append((a_neighbour, equivalent_node_a))

    for (a, b) in to_remove:
        g.remove_edge(a, b)

    for (a, b) in to_add:
        g.add_edge(a, b)

    g.remove_node(equivalent_node_b)

    return reduceGraph(g)


def solve(new_graph, solution=[], maxSteps=0):    
    global logger
    
    path = len(solution)
    
    #sys.stdout.write('.')
    #sys.stdout.flush()
    
    logger.info('solve step (depth: %s)', path)
    
    if path > maxSteps:
        logger.info('maxStep exceeded: return')
        return

    colors_left = len(set([node.color for node in new_graph.nodes()]))
    
    # We accept at most N moves.
    # If we have gotten to a path of length N, then colorsLeft must == 1.
    if not (maxSteps - path > colors_left - 2):
        logger.info('not enough steps left (steps left: %s colors left: %s', maxSteps - path, colors_left - 2)
        return

    # Start out by reducing same colored nodes
    if len(new_graph.nodes()) == 1:
        logger.info('Solution found! only 1 node left')
        return solution

    # Now we mutate    
    
    #for node in list(sorted(nx.center(new_graph))):
    
    #new_graph_ecc = nx.eccentricity(new_graph)
    #for node in list(sorted(new_graph_ecc, key=lambda x: new_graph_ecc[x])):        
        #logger.info(node, 'ecc:', new_graph_ecc[node])
        
    for (node, degree) in list(sorted(new_graph.degree, key=lambda x: x[1], reverse=True)):
    
    #for node in list(sorted(new_graph)):
        logger.info('Entering node: %s', node.idx)
        
        # Get neighbours
        neighbours = list(nx.all_neighbors(new_graph, node))
        # And their colors
        neigh_colors = set([x.color for x in neighbours])
        # We can be assured they are not like ours due to reduceGraph
        for color in neigh_colors:            
            # We take a copy of our graph, and toggle the color
            tmp_graph = copy.deepcopy(new_graph)
            xnode = [x for x in tmp_graph if x.idx == node.idx][0]
            xnode.color = color

            len_before = len(tmp_graph)
            tmp_graph = reduceGraph(tmp_graph)
            logger.info('Changing color to %s: %s -> %s nodes', color.name, len_before, len(tmp_graph))
            x = solve(tmp_graph, solution=solution + [(node.idx, color)], maxSteps=maxSteps)
            if x is not None:
                return x
            

def drawLevelGraph(g, title):
    plt.figure(figsize=(10,10))
    plt.title(title)

    rgbs = []
    for c in levelData['colors']:
        rgbs.append('#' + c['rgb'])
    level_cmap = clr.ListedColormap(rgbs, name='levelColorMap')      
        
    graph_color_map = []
    for node in g:
        graph_color_map.append('#' + node.color.rgb)
        
    nx.draw(g, node_color = graph_color_map, cmap = level_cmap, node_size = 800, with_labels = True)            
    #plt.show()

def printSolution(levelData, levelGraph, solution):    
    g = copy.deepcopy(levelGraph)    
    
    for step in solution:
        g = applyStep(g, step)
        g = reduceGraph(g)
        #drawLevelGraph(g, 'Move: ' + str(step[0]) + ' ' + step[1].name)
    

def applyStep(graph, solutionStep):
    node = [x for x in graph.nodes() if x.idx == solutionStep[0]][0]
    node.color = solutionStep[1]
    graph = reduceGraph(graph)
    return graph


def setupLogger():
    global logger    
    logger = logging.getLogger('kami_solver')
    #logger.propagate = False
    # create file handler
    fh = logging.FileHandler('output.log')
    fh.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #fh.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.info('test')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('levelData', type=argparse.FileType('r'), help="Path to level json data file")
    args = parser.parse_args()

setupLogger()
levelData = json.load(args.levelData)
levelGraph = buildLevelGraph(levelData)
#drawLevelGraph(levelGraph, 'Initial state')
solution = solve(levelGraph, maxSteps=levelData['steps'])
printSolution(levelData, levelGraph, solution)


