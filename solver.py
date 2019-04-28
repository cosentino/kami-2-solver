#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 19:19:07 2019

@author: marcello
"""

import logging
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


class GroupMeta:
    def __init__(self, score, degree, eccentricity, most_connected_color_counter, most_connected_color, sorted_neighbour_colors):
        self.score = score
        self.degree = degree
        self.eccentricity = eccentricity
        self.most_connected_color_counter = most_connected_color_counter
        self.most_connected_color = most_connected_color
        self.sorted_neighbour_colors = sorted_neighbour_colors

    def __str__(self):
        return '<GroupMeta: score: %s, deg: %s, ecc: %s, most_connected_color: %s (%s)>' % (self.score, self.degree, self.eccentricity, self.most_connected_color.name, self.most_connected_color_counter)

    def __eq__(self, other):
        return self.score == other.score

    def __hash__(self):
        return int(self.score, 16)

    def json(self):
        return [self.score]


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

    for (a, b) in to_remove:
        g.remove_edge(a, b)

    for (a, b) in to_add:
        g.add_edge(a, b)

    g.remove_node(equivalent_node_b)

    return reduceGraph(g)


def getGraphMeta(new_graph):
    scores = []
    diameter = nx.diameter(new_graph)
    eccentricity = nx.eccentricity(new_graph)
    degrees = list(new_graph.degree)
    for (node, degree) in degrees:

        # count the number of neighbour having the same color
        color_neighbour_counters = dict()
        for (a, b) in set(new_graph.edges(node)):
            color_neighbour_counters[b.color] = color_neighbour_counters.get(b.color, 0) + 1

        sorted_neighbour_colors = sorted(color_neighbour_counters, key=lambda x:color_neighbour_counters[x], reverse=True)
        most_connected_color = max(color_neighbour_counters, key=lambda x:color_neighbour_counters[x])

        # node score seek for:
        # - maximum degree (number of edges)
        # - minimum eccentricity (central to the graph)
        # - maximum number of neighbour of the same color
        score = degree + (diameter - eccentricity[node]) + 3 * color_neighbour_counters[most_connected_color]

        scores.append((node, GroupMeta(score, degree, eccentricity[node], color_neighbour_counters[most_connected_color], most_connected_color, sorted_neighbour_colors)))
    return scores


def solve(new_graph, solution=[], maxSteps=0):
    depth = len(solution)

    logging.info('%s solve step (depth: %s)', getLoggingDepthSpaces(depth), depth)
    
    if depth > maxSteps:
        logging.info('%s maxStep exceeded -> return', getLoggingDepthSpaces(depth))
        return

    colors_left = len(set([node.color for node in new_graph.nodes()]))
    
    # We accept at most N moves.
    # If we have gotten to a path of length N, then colorsLeft must == 1.
    if not (maxSteps - depth > colors_left - 2):
        logging.info('%s not enough steps left (steps left: %s colors left: %s)', getLoggingDepthSpaces(depth), maxSteps - depth, colors_left - 2)
        return

    # Start out by reducing same colored nodes
    if len(new_graph.nodes()) == 1:
        logging.info('%s solution found! only 1 node left', getLoggingDepthSpaces(depth))
        return solution

    # Now we mutate:
    # choose the node that have the greatest score
    for (node, group_meta) in list(sorted(getGraphMeta(new_graph), key=lambda x: x[1].score, reverse=True)):

        logging.info('%s entering node %s - %s', getLoggingDepthSpaces(depth), node.idx, group_meta)

        # We can be assured they are not like ours due to reduceGraph
        for color in group_meta.sorted_neighbour_colors:
            # We take a copy of our graph, and toggle the color
            tmp_graph = copy.deepcopy(new_graph)
            xnode = [x for x in tmp_graph if x.idx == node.idx][0]
            xnode.color = color

            len_before = len(tmp_graph)
            tmp_graph = reduceGraph(tmp_graph)
            logging.info('%s changing color to %s: %s -> %s nodes', getLoggingDepthSpaces(depth), color.name, len_before, len(tmp_graph))
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
    plt.show()


def printSolution(levelData, levelGraph, solution):
    g = copy.deepcopy(levelGraph)    
    
    for step in solution:
        g = applyStep(g, step)
        g = reduceGraph(g)
        drawLevelGraph(g, 'Move: ' + str(step[0]) + ' ' + step[1].name)
    

def applyStep(graph, solutionStep):
    node = [x for x in graph.nodes() if x.idx == solutionStep[0]][0]
    node.color = solutionStep[1]
    graph = reduceGraph(graph)
    return graph


def getLoggingDepthSpaces(depth):
    spaces = ''
    for i in range(0, depth):
        spaces += ' '
    return spaces


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('levelData', type=argparse.FileType('r'), help="Path to level json data file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, filename='output.txt', filemode='w')

    levelData = json.load(args.levelData)
    levelGraph = buildLevelGraph(levelData)
    drawLevelGraph(levelGraph, 'Initial state')
    solution = solve(levelGraph, maxSteps=levelData['steps'])
    printSolution(levelData, levelGraph, solution)

