import json
from os import makedirs, path

from platformdirs import user_cache_dir

APP_NAME = "glmosaic"
APP_AUTHOR = "zvin"
CACHE_DIR = user_cache_dir(APP_NAME, APP_AUTHOR)
