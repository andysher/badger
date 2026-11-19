"""Themes for Tiny Count: small shape-drawn objects.

Every draw function has the shape ``draw(x, y, size, t, variant)``:
(x, y) is the centre, ``size`` the diameter in pixels, ``t`` seconds (used for
small idle motion such as a wagging tail) and ``variant`` an index so objects of
one theme can differ (only balloons use it).
"""

import math


def rgb(r, g, b, a=255):
    return color.rgb(r, g, b, a)


INK = rgb(40, 36, 56)
WHITE = rgb(255, 255, 255)
SHINE = rgb(255, 255, 255, 150)


def _dot(x, y, r, pen):
    screen.pen = pen
    screen.shape(shape.circle(x, y, r))


def _tri(a, b, c, pen):
    screen.pen = pen
    screen.shape(shape.custom([vec2(a[0], a[1]), vec2(b[0], b[1]), vec2(c[0], c[1])]))


APPLE_RED = rgb(226, 40, 48)
BROWN = rgb(120, 76, 40)
LEAF = rgb(46, 170, 70)


def apple(x, y, s, t, v=0):
    r = s / 2
    screen.pen = APPLE_RED
    screen.shape(shape.circle(x - r * 0.28, y + r * 0.12, r * 0.74))
    screen.shape(shape.circle(x + r * 0.28, y + r * 0.12, r * 0.74))
    screen.pen = BROWN
    screen.shape(shape.rounded_rectangle(x - 1.5, y - r * 0.95, 3, r * 0.5, 1))
    screen.pen = LEAF
    screen.shape(shape.ellipse(x + r * 0.38, y - r * 0.72, r * 0.38, r * 0.17))
    _dot(x - r * 0.4, y - r * 0.12, r * 0.14, SHINE)


STAR_YELLOW = rgb(255, 205, 20)
STAR_EDGE = rgb(255, 150, 20)


def star(x, y, s, t, v=0):
    r = s / 2 * (1.0 + 0.04 * math.sin(t * 3.0))
    screen.pen = STAR_EDGE
    screen.shape(shape.star(x, y, 5, r * 0.5, r * 1.08))
    screen.pen = STAR_YELLOW
    screen.shape(shape.star(x, y, 5, r * 0.46, r * 0.95))
    _dot(x - r * 0.16, y, r * 0.07, INK)
    _dot(x + r * 0.16, y, r * 0.07, INK)


FISH_ORANGE = rgb(255, 120, 30)
FISH_FIN = rgb(240, 80, 20)


def fish(x, y, s, t, v=0):
    r = s / 2
    wag = math.sin(t * 6.0) * r * 0.14
    _tri((x + r * 0.45, y), (x + r * 1.0, y - r * 0.42 + wag), (x + r * 1.0, y + r * 0.42 + wag), FISH_FIN)
    _tri((x - r * 0.2, y - r * 0.35), (x + r * 0.2, y - r * 0.35), (x, y - r * 0.68), FISH_FIN)
    screen.pen = FISH_ORANGE
    screen.shape(shape.ellipse(x - r * 0.1, y, r * 0.72, r * 0.5))
    _dot(x - r * 0.42, y - r * 0.1, r * 0.18, WHITE)
    _dot(x - r * 0.46, y - r * 0.1, r * 0.09, INK)


BALLOONS = (
    rgb(235, 60, 70),
    rgb(50, 130, 240),
    rgb(60, 190, 90),
    rgb(240, 90, 170),
    rgb(250, 190, 20),
    rgb(160, 90, 220),
)


def balloon(x, y, s, t, v=0):
    r = s / 2
    pen = BALLOONS[v % len(BALLOONS)]
    sway = math.sin(t * 2.0) * 2
    screen.pen = INK
    screen.shape(shape.line(x, y + r * 0.7, x + sway, y + r * 0.85, 2))
    screen.shape(shape.line(x + sway, y + r * 0.85, x - sway, y + r * 1.05, 2))
    _tri((x, y + r * 0.5), (x - 3, y + r * 0.72), (x + 3, y + r * 0.72), pen)
    screen.pen = pen
    screen.shape(shape.ellipse(x, y - r * 0.22, r * 0.64, r * 0.76))
    screen.pen = SHINE
    screen.shape(shape.ellipse(x - r * 0.25, y - r * 0.5, r * 0.12, r * 0.22))


DUCK_YELLOW = rgb(255, 214, 30)
DUCK_WING = rgb(240, 170, 10)
BEAK = rgb(255, 120, 20)


def duck(x, y, s, t, v=0):
    r = s / 2
    screen.pen = DUCK_YELLOW
    screen.shape(shape.ellipse(x - r * 0.15, y + r * 0.28, r * 0.78, r * 0.5))
    _dot(x + r * 0.3, y - r * 0.32, r * 0.44, DUCK_YELLOW)
    _tri((x + r * 0.68, y - r * 0.45), (x + r * 1.0, y - r * 0.3), (x + r * 0.68, y - r * 0.15), BEAK)
    screen.pen = DUCK_WING
    screen.shape(shape.ellipse(x - r * 0.25, y + r * 0.3, r * 0.4, r * 0.24))
    _dot(x + r * 0.38, y - r * 0.42, r * 0.07, INK)


PETAL = rgb(250, 110, 170)
PETAL_MID = rgb(255, 215, 40)


def flower(x, y, s, t, v=0):
    r = s / 2
    spin = t * 0.5
    screen.pen = PETAL
    for i in range(5):
        a = spin + i * (2 * math.pi / 5)
        screen.shape(shape.circle(x + math.cos(a) * r * 0.55, y + math.sin(a) * r * 0.55, r * 0.4))
    _dot(x, y, r * 0.32, PETAL_MID)


BUG_RED = rgb(230, 40, 40)


def ladybug(x, y, s, t, v=0):
    r = s / 2
    screen.pen = INK
    screen.shape(shape.line(x - r * 0.15, y - r * 0.85, x - r * 0.35, y - r * 1.05, 2))
    screen.shape(shape.line(x + r * 0.15, y - r * 0.85, x + r * 0.35, y - r * 1.05, 2))
    screen.shape(shape.circle(x, y - r * 0.7, r * 0.33))
    _dot(x, y + r * 0.12, r * 0.8, BUG_RED)
    screen.pen = INK
    screen.shape(shape.line(x, y - r * 0.6, x, y + r * 0.9, 2))
    for dx, dy in ((-0.4, -0.15), (0.4, -0.15), (-0.38, 0.4), (0.38, 0.4)):
        screen.shape(shape.circle(x + dx * r, y + dy * r, r * 0.14))


class Theme:
    def __init__(self, name, draw, bg, accent):
        self.name = name
        self.draw = draw
        self.bg = bg          # soft pastel background (r, g, b)
        self.accent = accent  # deep colour for the big numeral


THEMES = (
    Theme("apple", apple, (219, 242, 216), (188, 36, 44)),
    Theme("star", star, (230, 224, 250), (96, 70, 190)),
    Theme("fish", fish, (214, 236, 250), (20, 108, 168)),
    Theme("balloon", balloon, (255, 244, 212), (196, 88, 20)),
    Theme("duck", duck, (210, 240, 238), (0, 118, 120)),
    Theme("flower", flower, (222, 244, 232), (186, 48, 118)),
    Theme("ladybug", ladybug, (230, 246, 214), (40, 116, 40)),
)
