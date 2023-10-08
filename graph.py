#!/usr/bin/env python

import json
from os import makedirs, path

from pygraph.algorithms.accessibility import mutual_accessibility
from pygraph.classes.digraph import digraph
from pygraph.classes.exceptions import AdditionError

from cache import CACHE_DIR
from mosaicfactory import MosaicFactory


def serialize_digraph(gr):
    return {
        "edges": [[edge[0].hash, edge[1].hash] for edge in gr.edges()],
    }


def deserialize_digraph(data, images):
    gr = digraph()
    gr.add_nodes(images.values())
    for edge in data["edges"]:
        img0 = images[edge[0]]
        img1 = images[edge[1]]
        gr.add_edge((img0, img1))
    return gr


def load_from_cache(mosaic_factory, nb_segments, reuse=True):
    dir = path.join(
        CACHE_DIR, "mosaics", mosaic_factory.hash(), str(nb_segments), str(reuse)
    )
    fpath = path.join(dir, "graph.json")
    try:
        with open(fpath, "r") as f:
            return deserialize_digraph(json.load(f), mosaic_factory.images)
    except (IOError, json.JSONDecodeError):
        gr = transition_graph(mosaic_factory, nb_segments, reuse)
        makedirs(dir, exist_ok=True)
        with open(fpath, "w") as f:
            json.dump(serialize_digraph(gr), f)
        return gr


def transition_graph(mosaic_factory, nb_segments, reuse=True):
    gr = digraph()
    gr.add_nodes(mosaic_factory.images.values())
    print("calculating transition graph:")
    for i, img in enumerate(mosaic_factory.images.values()):
        print(" {0}/{1}".format(i + 1, len(mosaic_factory.images)))
        for line in mosaic_factory.cached_mosaic(img, nb_segments, reuse):
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
    gr = load_from_cache(mosaic_factory, nb_segments, reuse)
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
    gr = load_from_cache(mosaic_factory, 4)
    with open("test.dot", "w") as _file:
        _file.write(write(gr))
