"""Parent mode picker: two huge picture tiles, no words."""

import math

from common import draw_numeral, clamp

TILE_W = 140
TILE_H = 180
TILE_Y = 36
TILE_X = (14, 166)
PICKER_BG = (238, 234, 250)
TAP_COLOUR = (52, 160, 100)
BOOK_COLOUR = (230, 110, 40)
SKIN = (255, 196, 150)


def _pen(rgb, alpha=255):
    screen.pen = color.rgb(rgb[0], rgb[1], rgb[2], alpha)


def _hand(cx, cy):
    """A pointing hand, index finger up."""
    _pen(SKIN)
    screen.shape(shape.rounded_rectangle(cx - 8, cy - 40, 16, 56, 8))     # index finger
    screen.shape(shape.rounded_rectangle(cx - 26, cy - 4, 52, 44, 14))    # palm
    screen.shape(shape.ellipse(cx - 28, cy + 8, 10, 15))                  # thumb
    _pen((225, 160, 115))
    screen.shape(shape.line(cx - 8, cy + 4, cx + 20, cy + 4, 2))          # knuckle crease


def _poly(cx, cy, points):
    screen.shape(shape.custom([vec2(cx + x, cy + y) for x, y in points]))


def _book(cx, cy):
    """An open book seen from the front: pages dip into a centre spine, a
    stack of page edges and the cover show underneath, a ribbon hangs down.
    One dot on the left page, two on the right."""
    # Ribbon bookmark (drawn first so the book overlaps its top).
    _pen((220, 40, 60))
    _poly(cx, cy, ((3, 30), (15, 30), (15, 56), (9, 50), (3, 56)))
    # Cover.
    _pen((190, 80, 20))
    _poly(cx, cy, ((-62, -24), (0, -14), (62, -24), (62, 34), (0, 44), (-62, 34)))
    # Page stack: cream edges peeking out below the top pages.
    _pen((236, 226, 200))
    _poly(cx, cy, ((-57, -30), (0, -20), (57, -30), (57, 29), (0, 39), (-57, 29)))
    _pen((205, 190, 160))
    screen.shape(shape.line(cx - 55, cy + 26, cx, cy + 35, 1))
    screen.shape(shape.line(cx + 55, cy + 26, cx, cy + 35, 1))
    # Top pages.
    _pen((255, 255, 255))
    _poly(cx, cy, ((-55, -36), (-1, -26), (-1, 31), (-55, 21)))
    _poly(cx, cy, ((1, -26), (55, -36), (55, 21), (1, 31)))
    # Spine shadow.
    _pen((200, 190, 175))
    screen.shape(shape.line(cx, cy - 26, cx, cy + 31, 2))
    # Counting dots: 1 on the left page, 2 on the right.
    _pen((235, 70, 90))
    screen.shape(shape.circle(cx - 28, cy - 3, 8))
    _pen((50, 130, 240))
    screen.shape(shape.circle(cx + 19, cy - 12, 8))
    screen.shape(shape.circle(cx + 37, cy + 7, 8))


def draw_picker(now, selected, remaining):
    """``selected`` 0/1; ``remaining`` 0..1 is the time-out fraction left."""
    _pen(PICKER_BG)
    screen.rectangle(screen.clip)
    for i in range(2):
        x = TILE_X[i]
        base = TAP_COLOUR if i == 0 else BOOK_COLOUR
        y = TILE_Y
        if i == selected:
            y += math.sin(now / 1000 * 2 * math.pi * 1.2) * 3
            _pen(base)
            screen.shape(shape.rounded_rectangle(x - 7, y - 7, TILE_W + 14, TILE_H + 14, 22))
        _pen((255, 255, 255) if i == selected else (225, 222, 238))
        screen.shape(shape.rounded_rectangle(x, y, TILE_W, TILE_H, 16))
        cx = x + TILE_W / 2
        cy = y + TILE_H / 2
        if i == 0:
            _hand(cx - 24, cy + 6)
            _pen(base)
            draw_numeral("1", cx + 38, cy, 80)
        else:
            _book(cx, cy)
    # Time-out ring: fills the whole circle at the start and drains.
    _pen((120, 110, 160))
    screen.shape(shape.pie(160, 14, 9, 0, int(360 * clamp(remaining, 0.0, 1.0))))
