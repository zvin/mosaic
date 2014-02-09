#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import argparse

from display import Context

parser = argparse.ArgumentParser(description="Photos mosaic visualization")
parser.add_argument(
    "folder",
    type=str,
    help="folder containing photos"
)
parser.add_argument(
    "-t", "--tiles",
    type=int,
    default=40,
    help="number of tiles in each mosaic"
)
parser.add_argument(
    "-p", "--pixels-limit",
    type=int,
    default=640 * 480,
    help="maximum number of pixels for each texture (defaults to 640x480)"
)
parser.add_argument(
    "-d", "--duration",
    type=float,
    default=10.,
    help="zooming out duration in seconds"
)
parser.add_argument(
    "-n", "--no-reuse",
    dest="reuse",
    action="store_false",
    help="a tile can only be used once in a photo (this requires that tiles²"
         " <= #photos in folder"
)
parser.add_argument(
    "-ww", "--window-width",
    type=int,
    default=640,
    help="window width (defaults to 640)"
)
parser.add_argument(
    "-wh", "--window-height",
    type=int,
    default=480,
    help="window height (defaults to 480)"
)

if __name__ == "__main__":
    args = parser.parse_args()
    Context(args)
