#!/usr/bin/python

from os import listdir
from os.path import join
import cPickle as pickle
from PIL import Image

from memoized import memoized


class MozaicImage(object):

    def __init__(self, path):
        self.path = path
        self.load()
        self.average_color = self.calculate_average_color()
        self.ratio = self.calculate_ratio()
        self.free()

    def load(self):
        self.image = Image.open(self.path).convert()

    def free(self):
        self.image = None

    def show(self):
        self.load()
        self.image.show()
        self.free()

    def calculate_ratio(self):
        return self.image.size[0] / float(self.image.size[1])

    def calculate_average_color(self):
        return self.image.resize((1, 1), Image.ANTIALIAS).getpixel((0, 0))

    def calculate_grid(self, nb_segments):
        self.load()
        small = self.image.resize((nb_segments, nb_segments), Image.ANTIALIAS)
        data = small.getdata()
        res = []
        for i in xrange(nb_segments):
            res.append([])
            for j in xrange(nb_segments):
                res[-1].append(data[i * nb_segments + j])
        self.free()
        return res


def color_difference(clr1, clr2):
    return sum(map(lambda (x1, x2): abs(x1 - x2), zip(clr1, clr2)))


def render_mosaic(mosaic, width, height):
    nb_segments = len(mosaic)
    pane_width = width / nb_segments
    pane_height = height / nb_segments
    res = Image.new("RGB", (width, height), (0, 0, 0))
    for i, line in enumerate(mosaic):
        for j, img in enumerate(line):
            img.load()
            res.paste(
                img.image.resize((pane_width, pane_height), Image.ANTIALIAS),
                (j * pane_width, i * pane_height)
            )
            img.free()
            print "%3d/%3d" % (i * nb_segments + j, nb_segments**2)
    return res


def find_nearest_image(color, images):
    nearest = None
    nearest_delta = 1000
    for img in images:
        delta = color_difference(color, img.average_color)
        if delta < nearest_delta:
            nearest_delta = delta
            nearest = img
    return nearest


class MozaicFactory(object):
    def __init__(self):
        self.ratio = None
        self.images = []

    @memoized
    def mosaic(self, image, nb_segments):
        available_images = set(self.images)
        pixels = image.calculate_grid(nb_segments)
        res = []
        for line in pixels:
            res.append([])
            for pixel in line:
                nearest = find_nearest_image(pixel, available_images)
                res[-1].append(nearest)
#                available_images.remove(nearest)
        return res

    def save(self, fname):
        with open(fname, "w") as _file:
            pickle.dump(self, _file)

    @staticmethod
    def load(fname):
        with open(fname, "r") as _file:
            return pickle.load(_file)

    def load_folder(self, folder):
        files = listdir(folder)
        for i, fname in enumerate(files):
            path = join(folder, fname)
            try:
                img = MozaicImage(path)
                if self.ratio is None:
                    self.ratio = img.ratio
            except IOError:
                print "Could not load %s" % path
            else:
                print "%3d/%3d" % (i + 1, len(files))
                if img.ratio == self.ratio:
                    self.images.append(img)

if __name__ == "__main__":
    from sys import argv
    folder = argv[1]
    factory = MozaicFactory()
    factory.load_folder(folder)
    factory.save(join(folder, "mosaic.pickle"))

#    m = MozaicFactory.load("mosaic.pickle")
#    a = m.mosaic(m.images[105], 40)
#    i = render_mosaic(a, 1024, 768)

    #for name in listdir(folder):
    #    path = join(folder, name)
    #    if isfile(path):
    #        try:
    #            im = MozaicImage(path)
    ##            print name
    #            average_color = im.average_color2()
    #            print "%s\t%.2f\t(%3d %3d %3d)" % (
    #                im.image.size,
    #                float(im.image.size[0]) / im.image.size[1],
    #                average_color[0],
    #                average_color[1],
    #                average_color[2]
    #            )
    ##            print im.grid(2)[0], im.grid2(2)[0]
    ##            print im.grid(2)[1], im.grid2(2)[1]
    #        except IOError, e:
    #            print "Could not open %s" % path
    ##            print e
