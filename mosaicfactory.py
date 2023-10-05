import json
import os

from itertools import groupby
from PIL import Image

from memoized import memoized
from mosaicimage import MosaicImage


class MosaicFactory(object):
    FILENAME = "mosaic.json"

    def __init__(self):
        self.ratio = None
        self.images = []

    @staticmethod
    def color_difference(clr1, clr2):
        return sum(map(lambda c: abs(c[0] - c[1]), zip(clr1, clr2)))

    @staticmethod
    def find_nearest_image(color, images):
        nearest = None
        nearest_delta = 1000
        for img in images:
            delta = MosaicFactory.color_difference(color, img.average_color)
            if delta < nearest_delta:
                nearest_delta = delta
                nearest = img
        return nearest

    @memoized
    def mosaic(self, image, nb_segments, reuse=True):
        available_images = self.images[:]
        pixels = image.calculate_grid(nb_segments, image.get_image())
        res = []
        for line in pixels:
            res.append([])
            for pixel in line:
                nearest = MosaicFactory.find_nearest_image(pixel, available_images)
                res[-1].append(nearest)
                if not reuse:
                    available_images.remove(nearest)
        return res

    def save(self):
        folder = os.path.dirname(self.images[0].path)
        with open(os.path.join(folder, self.FILENAME), "w") as _file:
            json.dump(
                {
                    "images": dict(
                        (os.path.basename(i.path), i.to_dict()) for i in self.images
                    ),
                },
                _file,
                indent=4,
                sort_keys=True,
            )

    @staticmethod
    def list_image_files(folder):
        return [
            name
            for name in os.listdir(folder)
            if name.lower().endswith(".jpg")
            or name.lower().endswith(".jpeg")
            or name.lower().endswith(".png")
        ]

    @classmethod
    def load(cls, folder):
        factory = cls()
        try:
            with open(os.path.join(folder, cls.FILENAME), "r") as _file:
                data = json.load(_file)
        except (IOError, ValueError):
            data = {}
        images_dict = data.get("images", {})
        filenames = MosaicFactory.list_image_files(folder)
        print("calculating average colors:")
        for i, filename in enumerate(filenames):
            print(" {0}/{1}".format(i + 1, len(filenames)))
            image_path = os.path.join(folder, filename)
            image_dict = images_dict.get(filename)
            mtime = os.path.getmtime(image_path)
            if image_dict and image_dict.get("mtime") == mtime:
                img = MosaicImage.from_dict(image_path, image_dict)
            else:
                img = MosaicImage.from_file(image_path, mtime)
            factory.images.append(img)
        # group images by ratio
        get_ratio = lambda img: img.ratio
        factory.images.sort(key=get_ratio)
        image_groups = []
        for ratio, images in groupby(factory.images, key=get_ratio):
            image_groups.append(list(images))
        # take only the largest group
        image_groups.sort(key=len, reverse=True)
        images = image_groups[0]
        factory.ratio = images[0].ratio
        factory.save()
        factory.images = images
        return factory

    @staticmethod
    def render_mosaic(mosaic, width, height):
        nb_segments = len(mosaic)
        pane_width = width / nb_segments
        pane_height = height / nb_segments
        res = Image.new("RGB", (width, height), (0, 0, 0))
        for i, line in enumerate(mosaic):
            for j, img in enumerate(line):
                image = img.get_image()
                res.paste(
                    image.resize((pane_width, pane_height), Image.ANTIALIAS),
                    (j * pane_width, i * pane_height),
                )
                print("%3d/%3d" % (i * nb_segments + j, nb_segments**2))
        return res


# TODO: remove main
if __name__ == "__main__":
    from sys import argv

    folder = argv[1]
    factory = MosaicFactory.load(folder)
    factory.save()

#    mosaic = factory.mosaic(m.images[0], 40)
#    img = MosaicFactory.render_mosaic(mosaic, 1024, 768)
