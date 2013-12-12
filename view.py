#!/usr/bin/python

import sys
import math
import Image

from mozaic import MozaicFactory, MozaicImage
from graph import image_iterator

try:
    from OpenGL.GLUT import *
    from OpenGL.GL import *
    from OpenGL.GLU import *
except:
    print "ERROR: PyOpenGL not installed properly."
    sys.exit()


spin = 0.0
textures = {}
picture_display_lists = {}
mozaic_display_lists = {}
mozaic_factory = MozaicFactory.load("mosaic.pickle")
nb_segments = 45
ratio = 4. / 3.
size = 100 / float(nb_segments)

iterator = image_iterator(mozaic_factory, nb_segments)
current_tile_picture = iterator.next()
current_mozaic_picture = iterator.next()

def findPictureInMozaic(picture, mozaic):
#    print "+" * 80
#    print picture.path
#    for line in mozaic:
#        print " | ".join(map(lambda x: x.path, line))
    x = -1
    for y, line in enumerate(mozaic):
        if picture in line:
            x = line.index(picture)
            break
    if x == -1:
        raise Exception("picture not in mozaic")
#    print len(mozaic) - x - 1, len(mozaic) - y - 1
#    print "-" * 80
    return (x, len(mozaic) - y - 1)

#start_picture_coord = (0, 0)
start_picture_coord = findPictureInMozaic(current_tile_picture, mozaic_factory.mozaic(current_mozaic_picture, nb_segments, fast=True))

def loadTexture(name):
    image = Image.open(name)

    ix = image.size[0]
    iy = image.size[1]
    image = image.tostring("raw", "RGBX", 0, -1)

    # Create Texture
    _id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, _id)   # 2d texture (x and y size)

    glPixelStorei(GL_UNPACK_ALIGNMENT,1)
    glTexImage2D(GL_TEXTURE_2D, 0, 3, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
    
    return _id

def generatePictureDisplayLists():
    width  = ratio * size
    height = size
    for picture in mozaic_factory.images:
        generatePictureDisplayList(picture, width, height)

def generatePictureDisplayList(picture, width, height):
    dl = glGenLists(1)
    picture_display_lists[picture] = dl
    glNewList(dl, GL_COMPILE)
    drawPicture(picture, 0, 0, width, height)
    glEndList()

def generateMozaicDisplayList(picture, fast=False):
    dl = glGenLists(1)
    mozaic_display_lists[picture] = dl
    glNewList(dl, GL_COMPILE)
    drawMozaic(picture, fast=fast)
    glEndList()

def drawMozaic(picture, fast=False):
    m = mozaic_factory.mozaic(picture, nb_segments, fast=fast)
    for column in xrange(nb_segments):
        for line in xrange(nb_segments):
            glPushMatrix()
            glTranslatef(column * ratio * size, line * size, 0.0)
            print column, line
            print column * ratio * size, line * size
#            glCallList(picture_display_lists[m[nb_segments - 1 - line][nb_segments - 1 - column]])
            glCallList(picture_display_lists[m[nb_segments - 1 - line][column]])
            glPopMatrix()

def drawPicture(picture, x, y, width, height):
    glBindTexture(GL_TEXTURE_2D, textures[picture])
    glPushMatrix()
    glTranslatef(x, y, 0.0)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0); glVertex2f(0    , 0     )	# Bottom Left Of The Texture and Quad
    glTexCoord2f(1.0, 0.0); glVertex2f(width, 0     )	# Bottom Right Of The Texture and Quad
    glTexCoord2f(1.0, 1.0); glVertex2f(width, height)	# Top Right Of The Texture and Quad
    glTexCoord2f(0.0, 1.0); glVertex2f(0    , height)
    glEnd()
    glPopMatrix()

def sigmoid(value):
    return 1.0 / (1.0 + math.exp(-float(value)))

def sigmoid_0_1(value):
    return sigmoid(value * 12.0 - 6.0)

def fake_sigmoid(value):
    if value == 0.0 or value == 1.0: return value
    delta = sigmoid_0_1(1) - sigmoid_0_1(0)
    res = sigmoid_0_1(value) / delta - sigmoid_0_1(0)
    if res < 0.0:
        return 0.0
    elif res > 1.0:
        return 1.0
    else:
        return res

def sin_0_1(value):
    return math.sin(value * (math.pi / 2))

def display():
    height = 100.0
    start_point = (
        start_picture_coord[0] * ((height * ratio) / (nb_segments - 1)),
        start_picture_coord[1] * (height / (nb_segments - 1))
    )
#    print start_point
#    start_point = (100.0 * ratio, 100.0 / (nb_segments - 1))
    center = ((height * ratio) / 2, height / 2)
    glClear(GL_COLOR_BUFFER_BIT)
    glPushMatrix()
#    zoom = (0.9 * (1. - (spin / 360.)) + .1) * nb_segments
#    zoom = (0.9 * (1. - (spin / 360.)) + .1)
    progress = 1 - spin / 360.
    max_zoom = nb_segments
    min_zoom = 1.0
#    zoom = progress * (max_zoom - min_zoom) + min_zoom
#    progress = sigmoid_0_1(progress)
    progress = fake_sigmoid(progress)
    cam_center = (
        start_point[0] + (center[0] - start_point[0]) * (1 - progress),
        start_point[1] + (center[1] - start_point[1]) * (1 - progress)
    )
#    print cam_center
#    progress = sin_0_1(progress)
    zoom = max_zoom ** progress
#    print zoom
    glTranslatef(cam_center[0], cam_center[1], 0.0)
#    glRotatef(spin, 0.0, 0.0, 1.0)
    glScalef(zoom, zoom, 1.0)
    glTranslatef(-cam_center[0], -cam_center[1], 0.0)
    if progress > 0.1:
        alpha = 1.0
    else:
        alpha = progress * 10.0
    glColor4f(0.0, 0.0, 0.0, alpha)
#    print glutGet(GLUT_ELAPSED_TIME)
#    glCallList(mozaic_display_lists[mozaic_factory.images[int(spin) % 3]])
    glCallList(mozaic_display_lists[current_mozaic_picture])
#    glCallList(mozaic_display_lists[mozaic_factory.images[1]])
#    glPopMatrix()
#    glPushMatrix()
    glColor4f(0.0, 0.0, 0.0, 1.0 - alpha)
    glScalef(nb_segments, nb_segments, 1.0)
    glCallList(picture_display_lists[current_mozaic_picture])
    glPopMatrix()
    glutSwapBuffers()

def spinDisplay():
    global spin
    global current_mozaic_picture
    global start_picture_coord
    duration = 10000.
#    spin = spin + 2.0
#    if(spin > 360.0):
#        spin = spin - 360.0
    old_spin = spin
    spin = 360. * (glutGet(GLUT_ELAPSED_TIME) % duration) / duration
    if spin < old_spin:
        print "change"
        current_tile_picture = current_mozaic_picture
        current_mozaic_picture = iterator.next()
        start_picture_coord = findPictureInMozaic(current_tile_picture, mozaic_factory.mozaic(current_mozaic_picture, nb_segments, fast=True))
    glutPostRedisplay()

def init():
    for img in mozaic_factory.images:
        textures[img] = loadTexture(img.path)
    generatePictureDisplayLists()
    for i, img in enumerate(mozaic_factory.images):
#        if i == 3:
#            break
        print i, "/", len(mozaic_factory.images)
        generateMozaicDisplayList(img, fast=True)
#    generateMozaicDisplayList(mozaic_factory.images[111], fast=True)
#    generateMozaicDisplayList(mozaic_factory.images[111], fast=False)

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
glutMainLoop()

