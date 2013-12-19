#!/usr/bin/env python

import json
import os

from PIL import Image

from memoized import memoized


class MosaicImage(object):

    def __init__(self):
        self.path = None
        self.average_color = None
        self.ratio = None

    def load(self):
        self.image = Image.open(self.path).convert()

    def free(self):
        self.image = None

    def calculate_ratio(self):
        self.ratio = self.image.size[0] / float(self.image.size[1])

    def calculate_average_color(self):
        self.average_color = self.image.resize(
            (1, 1), Image.ANTIALIAS
        ).getpixel((0, 0))

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

    def to_dict(self):
        return {
            "average_color": self.average_color,
            "ratio": self.ratio,
        }

    @classmethod
    def from_dict(cls, path, dct):
        img = cls()
        img.path = path
        img.average_color = dct["average_color"]
        img.ratio = dct["ratio"]
        return img

    @classmethod
    def from_file(cls, path):
        img = cls()
        img.path = path
        img.load()
        img.calculate_average_color()
        img.calculate_ratio()
        img.free()
        return img

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


class MosaicFactory(object):
    FILENAME = "mosaic.json"

    def __init__(self):
        self.ratio = None
        self.images = []

    @staticmethod
    def find_nearest_image(color, images):
        nearest = None
        nearest_delta = 1000
        for img in images:
            delta = color_difference(color, img.average_color)
            if delta < nearest_delta:
                nearest_delta = delta
                nearest = img
        return nearest

    @memoized
    def mosaic(self, image, nb_segments, reuse=True):
        available_images = set(self.images)
        pixels = image.calculate_grid(nb_segments)
        res = []
        for line in pixels:
            res.append([])
            for pixel in line:
                nearest = MosaicFactory.find_nearest_image(
                    pixel,
                    available_images
                )
                res[-1].append(nearest)
                if not reuse:
                    available_images.remove(nearest)
        return res

    def save(self):
        folder = os.path.dirname(self.images[0].path)
        with open(os.path.join(folder, self.FILENAME), "w") as _file:
            json.dump(
                {
                    "ratio": self.ratio,
                    "images": dict(
                        (os.path.basename(i.path), i.to_dict())
                        for i in self.images
                    ),
                },
                _file,
                indent=4,
                sort_keys=True,
            )

    @classmethod
    def load(cls, folder):
        factory = cls()
        try:
            with open(os.path.join(folder, cls.FILENAME), "r") as _file:
                data = json.load(_file)
        except (IOError, ValueError):
            data = {}
        images_dict = data.get("images", {})
        filenames = [name for name in os.listdir(folder) if name.endswith(".jpg")]  # TODO: png, gif, jpeg
        for filename in filenames:
            print filename
            image_path = os.path.join(folder, filename)
            image_dict = images_dict.get(filename)
            if image_dict:
                img = MosaicImage.from_dict(image_path, image_dict)
            else:
                img = MosaicImage.from_file(image_path)
            factory.images.append(img)
        # TODO: ratio
        factory.ratio = factory.images[0].ratio
        return factory

if __name__ == "__main__":
    from sys import argv
    folder = argv[1]
    factory = MosaicFactory.load(folder)
    factory.save()

#    m = MosaicFactory.load(folder)
#    a = m.mosaic(m.images[0], 40)
#    i = render_mosaic(a, 1024, 768)

