#!/usr/bin/env python

import argparse
import sys
from contextlib import contextmanager
from math import exp, sqrt

import glfw
from OpenGL.GL import (
    GL_BLEND,
    GL_CLAMP,
    GL_COLOR_BUFFER_BIT,
    GL_COMPILE,
    GL_DECAL,
    GL_FLAT,
    GL_MODELVIEW,
    GL_NEAREST,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_PROJECTION,
    GL_QUADS,
    GL_REPEAT,
    GL_RGBA,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TEXTURE_ENV,
    GL_TEXTURE_ENV_MODE,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNPACK_ALIGNMENT,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
    glBlendFunc,
    glCallList,
    glClear,
    glClearColor,
    glColor4f,
    glEnable,
    glEnd,
    glEndList,
    glGenLists,
    glGenTextures,
    glLoadIdentity,
    glMatrixMode,
    glNewList,
    glOrtho,
    glPixelStorei,
    glPopMatrix,
    glPushMatrix,
    glRotatef,
    glScalef,
    glShadeModel,
    glTexCoord2f,
    glTexEnvf,
    glTexImage2D,
    glTexParameterf,
    glTranslatef,
    glVertex2f,
    glViewport,
)
from PIL import Image

from graph import image_iterator
from mosaicfactory import MosaicFactory

parser = argparse.ArgumentParser(description="Photos mosaic visualization")
parser.add_argument("folder", type=str, help="folder containing photos")
parser.add_argument(
    "-t", "--tiles", type=int, default=40, help="number of tiles in each mosaic"
)
parser.add_argument(
    "-p",
    "--pixels-limit",
    type=int,
    default=640 * 480,
    help="maximum number of pixels for each texture (defaults to 640x480)",
)
parser.add_argument(
    "-d", "--duration", type=float, default=10.0, help="zooming out duration in seconds"
)
parser.add_argument(
    "-n",
    "--no-reuse",
    dest="reuse",
    action="store_false",
    help="a tile can only be used once in a photo (this requires that tiles²"
    " <= #photos in folder",
)


def find_picture_in_mosaic(picture, mosaic):
    x = -1
    for y, line in enumerate(mosaic):
        if picture in line:
            x = line.index(picture)
            break
    if x == -1:
        raise Exception("picture not in mosaic")
    return (x, len(mosaic) - y - 1)


@contextmanager
def limit_pixels_count(img, limit):
    pixels_count = img.width * img.height
    if pixels_count > limit:
        ratio = sqrt(limit / float(pixels_count))
        new_width = int(round(img.width * ratio))
        new_height = int(round(img.height * ratio))
        with img.resized(new_width, new_height) as image:
            yield image
    else:
        with img.open_image() as image:
            yield image


def load_texture(img):
    with limit_pixels_count(img, args.pixels_limit) as image:
        width, height = image.size
        image = image.tobytes("raw", "RGBX", 0, -1)
        # Create Texture
        _id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, _id)

        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(
            GL_TEXTURE_2D, 0, 3, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image
        )
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
    return _id


def generate_picture_display_list(picture, width, height):
    dl = glGenLists(1)
    picture_display_lists[picture] = dl
    glNewList(dl, GL_COMPILE)
    draw_picture(picture, 0, 0, width, height)
    glEndList()


def generate_mosaic_display_list(picture):
    dl = glGenLists(1)
    mosaic_display_lists[picture] = dl
    glNewList(dl, GL_COMPILE)
    draw_mosaic(picture)
    glEndList()


def draw_mosaic(picture):
    m = mosaic_factory.cached_mosaic(picture, args.tiles, args.reuse)
    for column in range(args.tiles):
        for line in range(args.tiles):
            glPushMatrix()
            glTranslatef(column * mosaic_factory.ratio * size, line * size, 0.0)
            glCallList(picture_display_lists[m[args.tiles - 1 - line][column]])
            glPopMatrix()


def draw_picture(picture, x, y, width, height):
    glBindTexture(GL_TEXTURE_2D, textures[picture])
    glPushMatrix()
    glTranslatef(x, y, 0.0)
    glBegin(GL_QUADS)
    # Bottom Left Of The Texture and Quad:
    glTexCoord2f(0.0, 0.0)
    glVertex2f(0, 0)
    # Bottom Right Of The Texture and Quad:
    glTexCoord2f(1.0, 0.0)
    glVertex2f(width, 0)
    # Top Right Of The Texture and Quad:
    glTexCoord2f(1.0, 1.0)
    glVertex2f(width, height)
    # Top Left Of The Texture and Quad:
    glTexCoord2f(0.0, 1.0)
    glVertex2f(0, height)
    glEnd()
    glPopMatrix()


def sigmoid(value):
    return 1.0 / (1.0 + exp(-float(value)))


def sigmoid_0_1(value):
    return sigmoid(value * 12.0 - 6.0)


def fake_sigmoid(value):
    if value == 0.0 or value == 1.0:
        return value
    delta = sigmoid_0_1(1) - sigmoid_0_1(0)
    res = sigmoid_0_1(value) / delta - sigmoid_0_1(0)
    if res < 0.0:
        return 0.0
    elif res > 1.0:
        return 1.0
    else:
        return res


def angle_difference(a1, a2):
    difference = a1 - a2
    if abs(difference) > 180:
        difference = difference % 180
        if a1 > a2:
            difference = -difference
    return difference


def display():
    start_point = (
        start_picture_coord[0] * HEIGHT * mosaic_factory.ratio / (args.tiles - 1),
        start_picture_coord[1] * HEIGHT / (args.tiles - 1),
    )
    center = (HEIGHT * mosaic_factory.ratio / 2.0, HEIGHT / 2.0)
    reverse_sigmoid_progress = fake_sigmoid(1 - progress)
    sigmoid_progress = 1 - reverse_sigmoid_progress
    max_zoom = args.tiles
    zoom = max_zoom**reverse_sigmoid_progress
    angle = start_orientation + sigmoid_progress * angle_difference(
        current_mosaic_picture.orientation, start_orientation
    )
    if reverse_sigmoid_progress > 0.1:
        alpha = 1.0
    else:
        alpha = reverse_sigmoid_progress * 10.0

    glClear(GL_COLOR_BUFFER_BIT)
    glPushMatrix()

    glTranslatef(center[0], center[1], 0.0)
    glRotatef(angle, 0, 0, 1)
    glTranslatef(-center[0], -center[1], 0.0)

    glTranslatef(start_point[0], start_point[1], 0.0)
    glScalef(zoom, zoom, 1.0)
    glTranslatef(-start_point[0], -start_point[1], 0.0)

    glColor4f(0.0, 0.0, 0.0, alpha)
    glCallList(mosaic_display_lists[current_mosaic_picture])
    glColor4f(0.0, 0.0, 0.0, 1.0 - alpha)

    glScalef(max_zoom, max_zoom, 1.0)
    glCallList(picture_display_lists[current_mosaic_picture])

    glPopMatrix()


def spin_display():
    global progress
    global current_mosaic_picture
    global start_picture_coord
    global start_orientation
    duration = args.duration
    old_progress = progress
    progress = (glfw.get_time() % duration) / duration
    if progress < old_progress:
        current_tile_picture = current_mosaic_picture
        start_orientation = current_mosaic_picture.orientation
        current_mosaic_picture = iterator.__next__()
        start_picture_coord = find_picture_in_mosaic(
            current_tile_picture,
            mosaic_factory.cached_mosaic(
                current_mosaic_picture, args.tiles, args.reuse
            ),
        )


def init():
    width = mosaic_factory.ratio * size
    height = size
    print("loading textures:")
    for i, img in enumerate(mosaic_factory.images.values()):
        print(" {0}/{1}".format(i + 1, len(mosaic_factory.images)))
        textures[img] = load_texture(img)
        generate_picture_display_list(img, width, height)
    print("generating mosaic display lists:")
    for i, img in enumerate(mosaic_factory.images.values()):
        print(" {0}/{1}".format(i + 1, len(mosaic_factory.images)))
        generate_mosaic_display_list(img)

    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glShadeModel(GL_FLAT)


def reshape(window, w, h):
    glViewport(0, 0, w, h)
    ratio = float(w) / h
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    viewport_center = HEIGHT * ratio / 2
    photo_center = HEIGHT * mosaic_factory.ratio / 2
    left = photo_center - viewport_center
    right = photo_center + viewport_center
    glOrtho(left, right, 0.0, HEIGHT, -1.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def main():
    global mosaic_factory, size, args, progress, textures, picture_display_lists, mosaic_display_lists, start_picture_coord, HEIGHT, start_orientation, current_mosaic_picture, iterator
    args = parser.parse_args()

    progress = 0.0
    textures = {}
    picture_display_lists = {}
    mosaic_display_lists = {}

    mosaic_factory = MosaicFactory()
    mosaic_factory.load(args.folder)

    HEIGHT = 100.0
    size = HEIGHT / args.tiles

    iterator = image_iterator(mosaic_factory, args.tiles, args.reuse)
    current_tile_picture = iterator.__next__()
    current_mosaic_picture = iterator.__next__()
    start_orientation = current_tile_picture.orientation

    start_picture_coord = find_picture_in_mosaic(
        current_tile_picture,
        mosaic_factory.cached_mosaic(current_mosaic_picture, args.tiles, args.reuse),
    )

    if not glfw.init():
        return
    window = glfw.create_window(640, 480, "Mosaic for {}".format(args.folder), None, None)
    if not window:
        glfw.terminate()
        return
    glfw.make_context_current(window)
    init()
    reshape(window, 640, 480)
    glfw.set_window_size_callback(window, reshape);

    while not glfw.window_should_close(window):
        spin_display()
        display()
        glfw.swap_buffers(window)
        glfw.poll_events()
    glfw.terminate()


if __name__ == "__main__":
    main()
