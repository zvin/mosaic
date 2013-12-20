#!/usr/bin/env python

from pygraph.algorithms.accessibility import mutual_accessibility
from pygraph.classes.digraph import digraph
from pygraph.classes.exceptions import AdditionError

from mosaicfactory import MosaicFactory


def transition_graph(mosaic_factory, nb_segments, reuse=True):
    gr = digraph()
    gr.add_nodes(mosaic_factory.images)
    print "calculating transition graph:"
    for i, img in enumerate(mosaic_factory.images):
        print " {0}/{1}".format(i + 1, len(mosaic_factory.images))
        for line in mosaic_factory.mosaic(img, nb_segments, reuse):
            for pic in line:
                try:
                    gr.add_edge((pic, img))
                except AdditionError:
                    pass
    return gr


def biggest_strongly_connected_component(g):
    ma = mutual_accessibility(g)
    max_component = []
    for component in ma.values():
        if len(component) > len(max_component):
            max_component = component
    g2 = digraph()
    g2.add_nodes(max_component)
    for edge in g.edges():
        if edge[0] in max_component and edge[1] in max_component:
            g2.add_edge(edge)
    return g2


def init_visited(g):
    for node in g.nodes():
        g.add_node_attribute(node, ("visited", 0))


def next_node(g, node):
    next = None
    min_visited = float("inf")
    for n in g.neighbors(node):
        if g.node_attributes(n)[0][1] < min_visited:
            min_visited = g.node_attributes(n)[0][1]
            next = n
    g.node_attributes(next)[0] = ("visited", g.node_attributes(next)[0][1] + 1)
    return next


def image_iterator(mosaic_factory, nb_segments, reuse=True):
    gr = transition_graph(mosaic_factory, nb_segments, reuse)
    c = biggest_strongly_connected_component(gr)
    init_visited(c)

    def it(graph, node):
        while True:
            yield node
            node = next_node(graph, node)

    return it(c, c.nodes()[0])


if __name__ == "__main__":
    from sys import argv
    from pygraph.readwrite.dot import write
    mosaic_factory = MosaicFactory.load(argv[1])
    gr = transition_graph(mosaic_factory, 4)
    with open("test.dot", "w") as _file:
        _file.write(write(gr))
