"""Peekaboo Animals: touch to open the curtains and meet a friendly animal.

A grown-up names the animal and makes its sound (the badge has no speaker).

  curtains closed  any touch (or a shake) swooshes them open; the animal
                   pops up and the case lights glow. While waiting, the
                   curtains sway and now and then part a crack to peek.
  animal showing   first touch: a happy wiggle-hop. Next touch, or about six
                   seconds without touches: the curtains close and the next
                   animal is queued (shuffled, never the same one twice).
                   A shake makes the animal jump and hearts and stars float up.

Sprites come from assets/animals.png (tools/tiny_touch/make_animals.py): one
row per animal, column 0 eyes open, column 1 happy closed eyes.

No text is needed, nothing to win or lose, and no strobing.
"""

import math
import random

from common import lights, ease_out_back, clamp

# Row order matches tools/tiny_touch/make_animals.py.
# (name, backdrop rgb)
ANIMALS = (
    ("Cat", (178, 220, 255)),
    ("Dog", (196, 238, 186)),
    ("Duck", (170, 206, 255)),
    ("Cow", (190, 232, 168)),
    ("Pig", (255, 236, 170)),
    ("Frog", (255, 226, 160)),
    ("Lion", (206, 196, 255)),
)

CLOSED, OPENING, SHOWN, CLOSING = 0, 1, 2, 3

CURTAIN_TIME = 0.5      # seconds to open or close
POP_DELAY = 0.12        # animal starts popping this long into the opening
POP_TIME = 0.5
IDLE_CLOSE = 6.0        # close by itself after this long without a touch
WIGGLE_TIME = 0.9
JUMP_TIME = 0.75
MIN_SHOWN = 0.45        # ignore a "close" touch this soon after a wiggle starts
PEEK_EVERY = 4.5        # closed curtains part a crack this often
PEEK_TIME = 1.4
MAX_PARTICLES = 24
OPEN_KEEP = 0.16        # fraction of each curtain still visible when open

CURTAIN = color.rgb(206, 36, 64)
CURTAIN_DARK = color.rgb(150, 20, 46)
CURTAIN_LIGHT = color.rgb(238, 82, 100)
VALANCE = color.rgb(170, 24, 52)
GOLD = color.rgb(255, 200, 60)
FLOOR = color.rgb(196, 128, 70)
FLOOR_DARK = color.rgb(160, 98, 52)
LABEL = color.rgb(255, 250, 235)
SPARKLE_RGB = (
    (255, 80, 130),
    (255, 200, 40),
    (255, 120, 60),
    (180, 100, 255),
    (60, 170, 255),
)

# A chunky 7x6 pixel heart, as (row, first column, length) runs.
HEART_RUNS = (
    (0, 1, 2), (0, 4, 2),
    (1, 0, 7),
    (2, 0, 7),
    (3, 1, 5),
    (4, 2, 3),
    (5, 3, 1),
)


def smoothstep(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


class Activity:
    def __init__(self):
        self.sheet = image.load("assets/animals.png").spritesheet(2, len(ANIMALS))
        self.backdrops = [color.rgb(*rgb) for _, rgb in ANIMALS]
        self.spots = [
            color.rgb(min(255, r + 40), min(255, g + 40), min(255, b + 40))
            for _, (r, g, b) in ANIMALS
        ]
        self.label_font = font.ziplock
        self.particles = []
        self.bag = []
        self.last = -1
        self.current = 0

    # -- lifecycle ---------------------------------------------------------

    def enter(self):
        w, h = screen.width, screen.height
        self.w, self.h = w, h
        self.valance_h = max(14, h // 9)
        self.floor_y = h - max(18, h // 7)
        # Largest whole-number scale of the 32px art that fits the stage.
        scale = int((self.floor_y - self.valance_h - 2) / (0.9 * 32))
        self.size = 32 * max(2, min(6, scale))
        # The faces' chins sit about 29/32 down their frame; stand them on the floor.
        self.base = self.floor_y + self.size * 3 // 32
        self.state = CLOSED
        self.t = 0.0
        self.clock = 0.0
        self.curtain = 0.0
        # Start "popped" so the first peek through the curtains shows an animal.
        self.pop = 1.0
        self.idle = 0.0
        self.wiggled = False
        self.wiggle = -1.0
        self.jump = -1.0
        self.next_blink = 2.0
        self.blink = 0.0
        self.peek = PEEK_EVERY * 0.5
        self.particles = []
        self.current = self._next_animal()

    def exit(self):
        self.particles = []
        self.bag = []

    # -- helpers -----------------------------------------------------------

    def _next_animal(self):
        if not self.bag:
            bag = list(range(len(ANIMALS)))
            for i in range(len(bag) - 1, 0, -1):  # Fisher-Yates
                j = random.randrange(i + 1)
                bag[i], bag[j] = bag[j], bag[i]
            if bag[-1] == self.last:
                bag[0], bag[-1] = bag[-1], bag[0]
            self.bag = bag
        self.last = self.bag.pop()
        return self.last

    def _open(self):
        self.state = OPENING
        self.t = 0.0
        self.pop = 0.0
        self.idle = 0.0
        self.wiggled = False
        self.wiggle = -1.0
        self.jump = -1.0
        self.blink = 0.0
        self.next_blink = random.uniform(1.6, 3.0)
        lights.flash(1.0)
        self._sparkle(5, stars_only=True)

    def _close(self):
        self.state = CLOSING
        self.t = 0.0

    def _sparkle(self, count, stars_only=False):
        cx = self.w / 2
        top = self.base - self.size * 0.75
        for i in range(count):
            if len(self.particles) >= MAX_PARTICLES:
                self.particles.pop(0)
            self.particles.append([
                cx + random.uniform(-0.45, 0.45) * self.size,      # x
                top + random.uniform(0.0, 0.4) * self.size,       # y
                random.uniform(-25.0, 25.0),                       # vx
                -random.uniform(45.0, 80.0),                       # vy
                0.0,                                               # age
                random.uniform(1.3, 2.0),                          # life
                1 if stars_only or i % 2 else 0,                   # 0 heart, 1 star
                random.randrange(len(SPARKLE_RGB)),                # colour
                random.uniform(0.8, 1.3) * self.size / 64,         # size unit
                random.uniform(0.0, 6.28),                         # sway phase
            ])

    # -- update ------------------------------------------------------------

    def update(self, inp):
        dt = inp.dt
        touched = inp.any
        self.clock += dt
        self.t += dt

        if self.state == CLOSED:
            self.curtain = 0.0
            self.peek -= dt
            if self.peek < -PEEK_TIME:
                self.peek = PEEK_EVERY
            if touched or inp.shake:
                self._open()

        elif self.state == OPENING:
            self.curtain = smoothstep(self.t / CURTAIN_TIME)
            if self.t >= CURTAIN_TIME:
                self.state = SHOWN
                self.t = 0.0
                self.curtain = 1.0

        elif self.state == SHOWN:
            self.idle += dt
            if inp.shake:
                self.jump = 0.0
                self.idle = 0.0
                lights.flash(0.8)
                self._sparkle(8)
            if touched:
                self.idle = 0.0
                if not self.wiggled:
                    self.wiggled = True
                    self.wiggle = 0.0
                    lights.flash(0.6)
                    self._sparkle(3)
                elif 0.0 <= self.wiggle < MIN_SHOWN:
                    self.wiggle = 0.0  # quick taps keep the wiggle going
                else:
                    self._close()
            if self.state == SHOWN and self.idle > IDLE_CLOSE:
                self._close()

        elif self.state == CLOSING:
            self.curtain = 1.0 - smoothstep(self.t / CURTAIN_TIME)
            if self.t >= CURTAIN_TIME:
                self.state = CLOSED
                self.curtain = 0.0
                self.peek = PEEK_EVERY
                self.current = self._next_animal()

        # Animal pop-in, actions and blinking.
        if self.state == SHOWN or (self.state == OPENING and self.t >= POP_DELAY):
            self.pop = min(1.0, self.pop + dt / POP_TIME)
        if self.wiggle >= 0.0:
            self.wiggle += dt
            if self.wiggle > WIGGLE_TIME:
                self.wiggle = -1.0
        if self.jump >= 0.0:
            self.jump += dt
            if self.jump > JUMP_TIME:
                self.jump = -1.0
        self.next_blink -= dt
        if self.next_blink <= 0.0:
            self.blink = 0.16
            self.next_blink = random.uniform(2.2, 4.2)
        if self.blink > 0.0:
            self.blink -= dt

        # Float hearts and stars upward.
        alive = []
        for p in self.particles:
            p[4] += dt
            if p[4] < p[5]:
                p[0] += (p[2] + math.sin(p[4] * 4.0 + p[9]) * 18.0) * dt
                p[1] += p[3] * dt
                p[2] *= max(0.0, 1.0 - 1.5 * dt)
                alive.append(p)
        self.particles = alive

    # -- drawing -----------------------------------------------------------

    def draw(self):
        w, h = self.w, self.h
        index = self.current
        screen.pen = self.backdrops[index]
        screen.rectangle(0, 0, w, h)

        curtain = self.curtain
        if self.state == CLOSED and self.peek < 0.0:
            # Gentle "peek": the curtains part a crack, then close again.
            curtain = 0.09 * math.sin(math.pi * (-self.peek / PEEK_TIME))

        if curtain > 0.0:
            # Soft spotlight on the stage behind the animal.
            screen.pen = self.spots[index]
            screen.shape(shape.circle(w / 2, self.base - self.size * 0.45, self.size * 0.55))

        # Floor boards.
        screen.pen = FLOOR
        screen.rectangle(0, self.floor_y, w, h - self.floor_y)
        screen.pen = FLOOR_DARK
        screen.rectangle(0, self.floor_y, w, 3)
        for x in range(0, w, 48):
            screen.rectangle(x, self.floor_y + 3, 2, h - self.floor_y)

        if curtain > 0.0:
            self._draw_animal(index)
            self._draw_label(index, curtain)

        self._draw_particles()
        self._draw_curtains(curtain)

    def _draw_animal(self, index):
        size = self.size
        pop = ease_out_back(self.pop)
        if pop <= 0.02:
            return
        x_off = 0.0
        y_off = math.sin(self.clock * 2.4) * size * 0.015
        breathe = math.sin(self.clock * 2.4 + 1.0) * 0.015
        sx = 1.0 + breathe
        sy = 1.0 - breathe
        happy = self.blink > 0.0

        if self.wiggle >= 0.0:
            p = self.wiggle / WIGGLE_TIME
            fade = 1.0 - p
            swing = math.sin(p * math.pi * 6.0)
            x_off += swing * size * 0.06 * fade
            sx += abs(swing) * 0.07 * fade
            sy -= abs(swing) * 0.05 * fade
            y_off -= math.sin(p * math.pi) * size * 0.12
            happy = True
        if self.jump >= 0.0:
            p = self.jump / JUMP_TIME
            y_off -= math.sin(p * math.pi) * size * 0.32
            if p < 0.15 or p > 0.88:
                sx += 0.08
                sy -= 0.08
            happy = True

        dw = size * sx * pop
        dh = size * sy * pop
        x = int(self.w / 2 + x_off - dw / 2)
        y = int(self.base + y_off - dh)
        screen.blit(self.sheet.sprite(1 if happy else 0, index), rect(x, y, int(dw), int(dh)))

    def _draw_label(self, index, curtain):
        # Small name for the grown-up; the game never depends on reading it.
        if curtain < 0.6:
            return
        name = ANIMALS[index][0]
        screen.font = self.label_font
        tw, th = screen.measure_text(name)
        x = (self.w - tw) // 2
        y = self.floor_y + (self.h - self.floor_y - th) // 2 + 1
        screen.pen = color.rgb(90, 50, 24)
        screen.text(name, x + 1, y + 1)
        screen.pen = LABEL
        screen.text(name, x, y)

    def _draw_particles(self):
        for p in self.particles:
            fade = 1.0 - p[4] / p[5]
            r, g, b = SPARKLE_RGB[p[7]]
            screen.pen = color.rgb(r, g, b, int(255 * clamp(fade * 2.0, 0.0, 1.0)))
            unit = p[8]
            if p[6]:
                screen.shape(shape.star(p[0], p[1], 5, 5 * unit, 11 * unit))
            else:
                px = max(1, int(3 * unit))
                ox = int(p[0]) - px * 7 // 2
                oy = int(p[1]) - px * 3
                for row, col, length in HEART_RUNS:
                    screen.rectangle(ox + col * px, oy + row * px, length * px, px)

    def _draw_curtains(self, opened):
        w, h = self.w, self.h
        half = w / 2
        sway = math.sin(self.clock * 1.3) * 2.0 * (1.0 - opened)
        panel = half * (1.0 - (1.0 - OPEN_KEEP) * opened) + sway
        top = self.valance_h - 2
        self._draw_panel(0, panel, top, False, opened)
        self._draw_panel(w - panel, panel, top, True, opened)

        # Valance with scalloped edge and gold tassels.
        screen.pen = VALANCE
        screen.rectangle(0, 0, w, self.valance_h)
        step = 32
        r = step // 2
        for i in range(w // step + 1):
            cx = i * step + r
            screen.pen = VALANCE
            screen.shape(shape.circle(cx, self.valance_h, r * 0.7))
            screen.pen = GOLD
            screen.shape(shape.circle(cx, self.valance_h + r * 0.7, 3))
        screen.pen = GOLD
        screen.rectangle(0, self.valance_h - 6, w, 3)

    def _draw_panel(self, x, width, top, right_side, opened):
        if width <= 0:
            return
        h = self.h
        screen.pen = CURTAIN
        screen.rectangle(int(x), top, int(width) + 1, h - top)
        # Vertical folds bunch up as the curtain opens.
        folds = 5
        fw = width / folds
        for i in range(folds):
            fx = x + i * fw
            screen.pen = CURTAIN_DARK
            screen.rectangle(int(fx + fw * 0.62), top, max(1, int(fw * 0.26)), h - top)
            screen.pen = CURTAIN_LIGHT
            screen.rectangle(int(fx + fw * 0.2), top, max(1, int(fw * 0.12)), h - top)
        # Shadow along the inner (centre) edge.
        screen.pen = CURTAIN_DARK
        edge = int(x) if right_side else int(x + width) - 3
        screen.rectangle(edge, top, 3, h - top)
        # Gold tie-back once the curtain is gathered.
        if opened > 0.5:
            screen.pen = GOLD
            ty = int(h * 0.58)
            screen.shape(shape.rounded_rectangle(int(x) - 2, ty, int(width) + 4, 7, 3))
