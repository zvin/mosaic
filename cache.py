import json
from os import makedirs, path

from platformdirs import user_cache_dir

APP_NAME = "glmosaic"
APP_AUTHOR = "zvin"
CACHE_DIR = user_cache_dir(APP_NAME, APP_AUTHOR)


class Cache:
    def __init__(self, fname=path.join(CACHE_DIR, "cache.json")):
        self.fname = fname
        self.load()

    def load(self):
        try:
            with open(self.fname, "r") as f:
                self.data = json.load(f)
        except:
            self.data = {"version": 1, "images": {}}

    def save(self):
        makedirs(CACHE_DIR, exist_ok=True)
        with open(self.fname, "w") as f:
            return json.dump(self.data, f, indent=4)

    @property
    def images(self):
        return self.data["images"]
