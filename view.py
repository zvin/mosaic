#!/usr/bin/env python

import math
import os
import sys

from PIL import Image

from graph import image_iterator
from mosaicfactory import MosaicFactory

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GLUT import *
except:
    print "ERROR: PyOpenGL not installed properly."
    sys.exit()


spin = 0.0
textures = {}
picture_display_lists = {}
mosaic_display_lists = {}
mosaic_factory = MosaicFactory.load(os.path.join(sys.argv[1]))
mosaic_factory.save()
#mosaic_factory.images = mosaic_factory.images[:30]
nb_segments = 40
size = 100 / float(nb_segments)

iterator = image_iterator(mosaic_factory, nb_segments)
current_tile_picture = iterator.next()
current_mosaic_picture = iterator.next()


def findPictureInMosaic(picture, mosaic):
    x = -1
    for y, line in enumerate(mosaic):
        if picture in line:
            x = line.index(picture)
            break
    if x == -1:
        raise Exception("picture not in mosaic")
    return (x, len(mosaic) - y - 1)


start_picture_coord = findPictureInMosaic(
    current_tile_picture,
    mosaic_factory.mosaic(current_mosaic_picture, nb_segments)
)


def loadTexture(name):
    image = Image.open(name)

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


def generatePictureDisplayList(picture, width, height):
    dl = glGenLists(1)
    picture_display_lists[picture] = dl
    glNewList(dl, GL_COMPILE)
    drawPicture(picture, 0, 0, width, height)
    glEndList()


def generateMosaicDisplayList(picture):
    dl = glGenLists(1)
    mosaic_display_lists[picture] = dl
    glNewList(dl, GL_COMPILE)
    drawMosaic(picture)
    glEndList()


def drawMosaic(picture):
    m = mosaic_factory.mosaic(picture, nb_segments)
    for column in xrange(nb_segments):
        for line in xrange(nb_segments):
            glPushMatrix()
            glTranslatef(
                column * mosaic_factory.ratio * size,
                line * size, 0.0
            )
            glCallList(
                picture_display_lists[m[nb_segments - 1 - line][column]]
            )
            glPopMatrix()


def drawPicture(picture, x, y, width, height):
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


def display():
    height = 100.0
    start_point = (
        start_picture_coord[0] * ((height * mosaic_factory.ratio) / (nb_segments - 1)),
        start_picture_coord[1] * (height / (nb_segments - 1))
    )
    center = ((height * mosaic_factory.ratio) / 2, height / 2)
    glClear(GL_COLOR_BUFFER_BIT)
    glPushMatrix()
    progress = 1 - spin
    max_zoom = nb_segments
    progress = fake_sigmoid(progress)
    cam_center = (
        start_point[0] + (center[0] - start_point[0]) * (1 - progress),
        start_point[1] + (center[1] - start_point[1]) * (1 - progress)
    )
    zoom = max_zoom ** progress
    glTranslatef(cam_center[0], cam_center[1], 0.0)
    glScalef(zoom, zoom, 1.0)
    glTranslatef(-cam_center[0], -cam_center[1], 0.0)
    if progress > 0.1:
        alpha = 1.0
    else:
        alpha = progress * 10.0
    glColor4f(0.0, 0.0, 0.0, alpha)
    glCallList(mosaic_display_lists[current_mosaic_picture])
    glColor4f(0.0, 0.0, 0.0, 1.0 - alpha)
    glScalef(nb_segments, nb_segments, 1.0)
    glCallList(picture_display_lists[current_mosaic_picture])
    glPopMatrix()
    glutSwapBuffers()


def spinDisplay():
    global spin
    global current_mosaic_picture
    global start_picture_coord
    duration = 10000.
    old_spin = spin
    spin = (glutGet(GLUT_ELAPSED_TIME) % duration) / duration
    if spin < old_spin:
        current_tile_picture = current_mosaic_picture
        current_mosaic_picture = iterator.next()
        start_picture_coord = findPictureInMosaic(
            current_tile_picture,
            mosaic_factory.mosaic(current_mosaic_picture, nb_segments)
        )
    glutPostRedisplay()


def init():
    print "loading textures:"
    for i, img in enumerate(mosaic_factory.images):
        print " {0}/{1}".format(i + 1, len(mosaic_factory.images))
        textures[img] = loadTexture(img.path)
    width = mosaic_factory.ratio * size
    height = size
    print "generating picture display lists:"
    for i, picture in enumerate(mosaic_factory.images):
        print " {0}/{1}".format(i + 1, len(mosaic_factory.images))
        generatePictureDisplayList(picture, width, height)
    print "generating mosaic display lists:"
    for i, img in enumerate(mosaic_factory.images):
        print " {0}/{1}".format(i + 1, len(mosaic_factory.images))
        generateMosaicDisplayList(img)

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
#    glOrtho(-50.0, 50.0, -50.0, 50.0, -1.0, 1.0)
    glOrtho(0.0, 100.0 * ratio, 0.0, 100.0, -1.0, 1.0)
#    glOrtho(0.0, w, 0.0, h, -1.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def mouse(button, state, x, y):
    if button == GLUT_LEFT_BUTTON:
        if(state == GLUT_DOWN):
            glutIdleFunc(spinDisplay)
    elif button == GLUT_MIDDLE_BUTTON or button == GLUT_RIGHT_BUTTON:
        if(state == GLUT_DOWN):
            glutIdleFunc(None)


#  Request double buffer display mode.
#  Register mouse input callback functions
glutInit(sys.argv)
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(640, 480)
glutInitWindowPosition(100, 100)
glutCreateWindow('View')
init()
glutDisplayFunc(display)
glutReshapeFunc(reshape)
glutMouseFunc(mouse)
glutIdleFunc(spinDisplay)
glutMainLoop()
