from PIL import Image


class MosaicImage(object):

    def __init__(self):
        self.path = None
        self.average_color = None
        self.ratio = None
        self.orientation = None

    def load(self):
        self.image = Image.open(self.path)

    def free(self):
        self.image = None

    def calculate_ratio(self):
        self.ratio = self.image.size[0] / float(self.image.size[1])

    def calculate_average_color(self):
        self.average_color = self.image.resize(
            (1, 1), Image.ANTIALIAS
        ).getpixel((0, 0))

    def calculate_orientation(self):
        orientations = {1: 0, 3: 180, 6: 270, 8: 90}
        try:
            exif_orientation = self.image._getexif().get(274)
        except:
            exif_orientation = 1
        self.orientation = orientations[exif_orientation]

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
            "orientation": self.orientation,
        }

    @classmethod
    def from_dict(cls, path, dct):
        img = cls()
        img.path = path
        img.average_color = dct["average_color"]
        img.ratio = dct["ratio"]
        img.orientation = dct["orientation"]
        return img

    @classmethod
    def from_file(cls, path):
        img = cls()
        img.path = path
        img.load()
        img.calculate_average_color()
        img.calculate_ratio()
        img.calculate_orientation()
        img.free()
        return img
