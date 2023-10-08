import hashlib
import json
from contextlib import contextmanager
from os import makedirs, path

from PIL import Image

from cache import CACHE_DIR


def hash_file(fpath):
    with open(fpath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def calculate_ratio(image):
    return image.size[0] / float(image.size[1])


def calculate_average_color(image):
    return image.resize((1, 1), Image.Resampling.LANCZOS).getpixel((0, 0))


def calculate_orientation(image):
    orientations = {1: 0, 3: 180, 6: 270, 8: 90}
    try:
        exif_orientation = image._getexif().get(274)
    except KeyError:
        exif_orientation = 1
    return orientations.get(exif_orientation, 0)


class MosaicImage(object):
    def __init__(self, image_path):
        self.path = image_path
        self.hash = hash_file(self.path)
        thumbnails_dir = path.join(CACHE_DIR, "images", self.hash)
        fpath = path.join(thumbnails_dir, "data.json")
        try:
            with open(fpath, "r") as f:
                data = json.load(f)
                self.average_color = data["average_color"]
                self.ratio = data["ratio"]
                self.orientation = data["orientation"]
                self.width = data["width"]
                self.height = data["height"]
        except (IOError, json.JSONDecodeError):
            with self.open_image() as image:
                self.average_color = calculate_average_color(image)
                self.ratio = calculate_ratio(image)
                self.orientation = calculate_orientation(image)
                width, height = image.size
                self.width = width
                self.height = height
            makedirs(thumbnails_dir, exist_ok=True)
            with open(fpath, "w") as f:
                json.dump(
                    {
                        "average_color": self.average_color,
                        "ratio": self.ratio,
                        "orientation": self.orientation,
                        "width": self.width,
                        "height": self.height,
                    },
                    f,
                    indent=4,
                )

    def __lt__(self, other):
        return self.path < other.path

    @contextmanager
    def open_image(self):
        with Image.open(self.path) as image:
            if image.mode != "RGB":
                image = image.convert("RGB")
            yield image

    @contextmanager
    def resized(self, width, height):
        thumbnails_dir = path.join(CACHE_DIR, "images", self.hash)
        makedirs(thumbnails_dir, exist_ok=True)
        fpath = path.join(thumbnails_dir, "{}x{}".format(width, height))
        try:
            with Image.open(fpath) as image:
                yield image
        except FileNotFoundError:
            with self.open_image() as image:
                resized = image.resize((width, height), Image.Resampling.LANCZOS)
                resized.save(fpath, "PNG")  # TODO: use jpeg for large images
                yield resized

    def get_grid(self, nb_segments):
        # TODO: remove this
        return self.calculate_grid(nb_segments)

    def calculate_grid(self, nb_segments):
        with self.resized(nb_segments, nb_segments) as small:
            data = small.getdata()
        res = []
        for i in range(nb_segments):
            res.append([])
            for j in range(nb_segments):
                res[-1].append(data[i * nb_segments + j])
        return res
