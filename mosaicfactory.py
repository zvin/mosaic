from itertools import groupby
from os import listdir, path

from PIL import Image

from cache import Cache
from memoized import memoized
from mosaicimage import MosaicImage


class MosaicFactory(object):
    def __init__(self):
        self.cache = Cache()
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
        pixels = image.get_grid(nb_segments)
        res = []
        for line in pixels:
            res.append([])
            for pixel in line:
                nearest = MosaicFactory.find_nearest_image(pixel, available_images)
                res[-1].append(nearest)
                if not reuse:
                    available_images.remove(nearest)
        return res

    @staticmethod
    def list_image_files(folder):
        return [
            name
            for name in listdir(folder)
            if name.lower().endswith(".jpg")
            or name.lower().endswith(".jpeg")
            or name.lower().endswith(".png")
        ]

    def load(self, folder):
        filenames = MosaicFactory.list_image_files(folder)
        print("calculating average colors:")
        all_images = []
        for i, filename in enumerate(filenames):
            print(" {0}/{1}".format(i + 1, len(filenames)))
            image_path = path.join(folder, filename)
            img = MosaicImage(self.cache, image_path)
            all_images.append(img)
        # group images by ratio
        get_ratio = lambda img: img.ratio
        all_images.sort(key=get_ratio)
        image_groups = []
        for ratio, images in groupby(all_images, key=get_ratio):
            image_groups.append(list(images))
        # take only the largest group
        image_groups.sort(key=len, reverse=True)
        self.images = image_groups[0]
        self.ratio = self.images[0].ratio

    @staticmethod
    def render_mosaic(mosaic, width, height):
        nb_segments = len(mosaic)
        pane_width = width / nb_segments
        pane_height = height / nb_segments
        res = Image.new("RGB", (width, height), (0, 0, 0))
        for i, line in enumerate(mosaic):
            for j, img in enumerate(line):
                with img.open_image() as image:
                    res.paste(
                        image.resize(
                            (pane_width, pane_height), Image.Resampling.LANCZOS
                        ),
                        (j * pane_width, i * pane_height),
                    )
                print("%3d/%3d" % (i * nb_segments + j, nb_segments**2))
        return res


# TODO: remove main
if __name__ == "__main__":
    from sys import argv

    folder = argv[1]
    factory = MosaicFactory.load(folder)
    factory.cache.save()

#    mosaic = factory.mosaic(m.images[0], 40)
#    img = MosaicFactory.render_mosaic(mosaic, 1024, 768)
