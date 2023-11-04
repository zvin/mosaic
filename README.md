# Mosaic

## What

Displays pictures made of other pictures.

A video explains it better than a thousand words:


https://github.com/zvin/mosaic/assets/180331/41ff8d8a-1d4d-4335-bfe0-c546e282d898



## Installing

```sh
poetry shell
poetry install
```

## Using

```sh
./mosaic.py A_FOLDER_WITH_PICTURES
```

### Detailed usage

```
usage: mosaic.py [-h] [-t TILES] [-p PIXELS_LIMIT] [-d DURATION] [-n] folder

Photos mosaic visualization

positional arguments:
  folder                folder containing photos

options:
  -h, --help            show this help message and exit
  -t TILES, --tiles TILES
                        number of tiles in each mosaic
  -p PIXELS_LIMIT, --pixels-limit PIXELS_LIMIT
                        maximum number of pixels for each texture (defaults to 640x480)
  -d DURATION, --duration DURATION
                        zooming out duration in seconds
  -n, --no-reuse        a tile can only be used once in a photo (this requires that tiles² <= #photos in folder
```
