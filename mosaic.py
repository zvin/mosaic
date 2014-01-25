#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import argparse
import math
import sys

from math import sqrt
from PIL import Image

from graph import image_iterator
from mosaicfactory import MosaicFactory

from OpenGL.GL import glGenTextures, glBindTexture, glPixelStorei, glTexImage2D
from OpenGL.GL import glTexParameterf, glTexEnvf, glGenLists, glNewList
from OpenGL.GL import glEndList, glPushMatrix, glPopMatrix, glTranslatef
from OpenGL.GL import glRotatef, glScalef, glBegin, glEnd, glTexCoord2f
from OpenGL.GL import glVertex2f, glCallList, glEnable, glBlendFunc, glColor4f
from OpenGL.GL import glClearColor, glShadeModel, glClear, glViewport
from OpenGL.GL import glMatrixMode, glLoadIdentity, glOrtho

from OpenGL.GL import GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T
from OpenGL.GL import GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER
from OpenGL.GL import GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE
from OpenGL.GL import GL_UNSIGNED_BYTE, GL_CLAMP, GL_UNPACK_ALIGNMENT, GL_RGBA
from OpenGL.GL import GL_DECAL, GL_COMPILE, GL_QUADS, GL_REPEAT, GL_NEAREST
from OpenGL.GL import GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_FLAT
from OpenGL.GL import GL_COLOR_BUFFER_BIT, GL_PROJECTION, GL_MODELVIEW

from OpenGL.GLUT import glutSwapBuffers, glutGet, glutPostRedisplay, glutInit
from OpenGL.GLUT import glutInitDisplayMode, glutInitWindowSize, glutIdleFunc
from OpenGL.GLUT import glutCreateWindow, glutDisplayFunc, glutReshapeFunc
from OpenGL.GLUT import glutMainLoop

from OpenGL.GLUT import GLUT_DOUBLE, GLUT_RGB, GLUT_ELAPSED_TIME

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

args = parser.parse_args()

progress = 0.0
textures = {}
picture_display_lists = {}
mosaic_display_lists = {}

mosaic_factory = MosaicFactory.load(args.folder)
mosaic_factory.save()

HEIGHT = 100.
size = HEIGHT / args.tiles

iterator = image_iterator(mosaic_factory, args.tiles, args.reuse)
current_tile_picture = iterator.next()
current_mosaic_picture = iterator.next()
start_orientation = current_tile_picture.orientation


def find_picture_in_mosaic(picture, mosaic):
    x = -1
    for y, line in enumerate(mosaic):
        if picture in line:
            x = line.index(picture)
            break
    if x == -1:
        raise Exception("picture not in mosaic")
    return (x, len(mosaic) - y - 1)


start_picture_coord = find_picture_in_mosaic(
    current_tile_picture,
    mosaic_factory.mosaic(current_mosaic_picture, args.tiles, args.reuse)
)


def limit_pixels_count(image, limit):
    width, height = image.size
    pixels_count = width * height
    if pixels_count > limit:
        ratio = sqrt(limit / float(pixels_count))
        new_width = int(round(width * ratio))
        new_height = int(round(height * ratio))
        return image.resize((new_width, new_height), Image.ANTIALIAS)
    else:
        return image


def load_texture(image):
    image = limit_pixels_count(image, args.pixels_limit)

    width, height = image.size
    image = image.tostring("raw", "RGBX", 0, -1)

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
    m = mosaic_factory.mosaic(picture, args.tiles, args.reuse)
    for column in xrange(args.tiles):
        for line in xrange(args.tiles):
            glPushMatrix()
            glTranslatef(
                column * mosaic_factory.ratio * size,
                line * size, 0.0
            )
            glCallList(
                picture_display_lists[m[args.tiles - 1 - line][column]]
            )
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
    return 1.0 / (1.0 + math.exp(-float(value)))


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
        start_picture_coord[1] * HEIGHT / (args.tiles - 1)
    )
    center = (HEIGHT * mosaic_factory.ratio / 2., HEIGHT / 2.)
    reverse_sigmoid_progress = fake_sigmoid(1 - progress)
    sigmoid_progress = 1 - reverse_sigmoid_progress
    max_zoom = args.tiles
    zoom = max_zoom ** reverse_sigmoid_progress
    angle = start_orientation + sigmoid_progress * angle_difference(
        current_mosaic_picture.orientation,
        start_orientation
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
    glutSwapBuffers()


def spin_display():
    global progress
    global current_mosaic_picture
    global start_picture_coord
    global start_orientation
    duration = args.duration * 1000.
    old_progress = progress
    progress = (glutGet(GLUT_ELAPSED_TIME) % duration) / duration
    if progress < old_progress:
        current_tile_picture = current_mosaic_picture
        start_orientation = current_mosaic_picture.orientation
        current_mosaic_picture = iterator.next()
        start_picture_coord = find_picture_in_mosaic(
            current_tile_picture,
            mosaic_factory.mosaic(
                current_mosaic_picture,
                args.tiles,
                args.reuse
            )
        )
    glutPostRedisplay()


def init():
    print "loading textures:"
    for i, img in enumerate(mosaic_factory.images):
        print " {0}/{1}".format(i + 1, len(mosaic_factory.images))
        textures[img] = load_texture(img.get_image())
    width = mosaic_factory.ratio * size
    height = size
    print "generating picture display lists:"
    for i, picture in enumerate(mosaic_factory.images):
        print " {0}/{1}".format(i + 1, len(mosaic_factory.images))
        generate_picture_display_list(picture, width, height)
    print "generating mosaic display lists:"
    for i, img in enumerate(mosaic_factory.images):
        print " {0}/{1}".format(i + 1, len(mosaic_factory.images))
        generate_mosaic_display_list(img)

    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glShadeModel(GL_FLAT)


def reshape(w, h):
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


glutInit(sys.argv)
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(640, 480)
glutCreateWindow("Mosaic for " + args.folder)
init()
glutDisplayFunc(display)
glutReshapeFunc(reshape)
glutIdleFunc(spin_display)
glutMainLoop()
