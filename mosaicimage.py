import hashlib
from contextlib import contextmanager

from PIL import Image


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
    except:
        exif_orientation = 1
    return orientations.get(exif_orientation, 0)


class MosaicImage(object):
    def __init__(self, cache, path):
        self.path = path
        self.cache = cache
        self.hash = hash_file(path)
        data = self.cache.images.get(self.hash)
        if data is not None:
            self.average_color = data["average_color"]
            self.ratio = data["ratio"]
            self.orientation = data["orientation"]
        else:
            with self.open_image() as image:
                self.average_color = calculate_average_color(image)
                self.ratio = calculate_ratio(image)
                self.orientation = calculate_orientation(image)
            self.cache.images[self.hash] = {
                "average_color": self.average_color,
                "ratio": self.ratio,
                "orientation": self.orientation,
            }

    def __lt__(self, other):
        return self.path < other.path

    def __hash(self):
        return self.hash

    @contextmanager
    def open_image(self):
        with Image.open(self.path) as image:
            if image.mode != "RGB":
                image = image.convert("RGB")
            yield image

    def get_grid(self, nb_segments):
        grid = (
            self.cache.images[self.hash].setdefault("grids", {}).get(str(nb_segments))
        )
        if grid is None:
            grid = self.calculate_grid(nb_segments)
            self.cache.images[self.hash]["grids"][str(nb_segments)] = grid
        return grid

    def calculate_grid(self, nb_segments):
        with self.open_image() as image:
            small = image.resize((nb_segments, nb_segments), Image.Resampling.LANCZOS)
        data = small.getdata()
        res = []
        for i in range(nb_segments):
            res.append([])
            for j in range(nb_segments):
                res[-1].append(data[i * nb_segments + j])
        return res
