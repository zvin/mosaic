from PIL import Image


class MosaicImage(object):
    def __init__(self):
        self.path = None
        self.mtime = None
        self.average_color = None
        self.ratio = None
        self.orientation = None

    def __lt__(self, other):
        return self.path < other.path

    def get_image(self):
        image = Image.open(self.path)
        if image.mode != "RGB":
            image = image.convert("RGB")
        return image

    def calculate_ratio(self, image):
        self.ratio = image.size[0] / float(image.size[1])

    def calculate_average_color(self, image):
        self.average_color = image.resize((1, 1), Image.ANTIALIAS).getpixel((0, 0))

    def calculate_orientation(self, image):
        orientations = {1: 0, 3: 180, 6: 270, 8: 90}
        try:
            exif_orientation = image._getexif().get(274)
        except:
            exif_orientation = 1
        self.orientation = orientations.get(exif_orientation, 0)

    def calculate_grid(self, nb_segments, image):
        small = image.resize((nb_segments, nb_segments), Image.ANTIALIAS)
        data = small.getdata()
        res = []
        for i in range(nb_segments):
            res.append([])
            for j in range(nb_segments):
                res[-1].append(data[i * nb_segments + j])
        return res

    def to_dict(self):
        return {
            "average_color": self.average_color,
            "ratio": self.ratio,
            "orientation": self.orientation,
            "mtime": self.mtime,
        }

    @classmethod
    def from_dict(cls, path, dct):
        img = cls()
        img.path = path
        img.average_color = dct["average_color"]
        img.ratio = dct["ratio"]
        img.orientation = dct["orientation"]
        img.mtime = dct["mtime"]
        return img

    @classmethod
    def from_file(cls, path, mtime):
        img = cls()
        img.path = path
        img.mtime = mtime
        image = img.get_image()
        img.calculate_average_color(image)
        img.calculate_ratio(image)
        img.calculate_orientation(image)
        return img
