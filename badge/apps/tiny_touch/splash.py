"""Color Splash: every touch makes a big, joyful splash of that pad's colour.

Each play pad owns a colour (common.PAD_COLOURS) and a home spot on screen,
so a toddler learns "this pad makes red up there". A new touch pops a big
shape, an expanding ring, a burst of droplets and a soft paint stain that
lingers for a few seconds. Holding a pad keeps blowing gentle bubbles. A
shake throws rainbow confetti across the whole screen.

No text, no scores, no fail states, and no full-screen flashing.
"""

import math
import random

from common import NIGHT, lights, ease_out_back

# RGB values matching common.PAD_COLOURS / common.RAINBOW. Kept as tuples here
# so we can fade them with an alpha channel via color.rgb(r, g, b, a).
RGB = (
    (255, 59, 48),    # 0 red     UP
    (255, 149, 0),    # 1 orange  RIGHT
    (255, 214, 10),   # 2 yellow  DOWN
    (52, 199, 89),    # 3 green   LEFT
    (10, 132, 255),   # 4 blue    SELECT
    (175, 82, 222),   # 5 purple  BACK
    (255, 55, 135),   # 6 pink    MENU
)

# pad -> (colour index, home x fraction, home y fraction, case lights)
# Case light indexes are a best guess (0..3 left to right); adjust on hardware.
PADS = {
    BUTTON_UP: (0, 0.50, 0.24, (1, 2)),
    BUTTON_RIGHT: (1, 0.78, 0.50, (2, 3)),
    BUTTON_DOWN: (2, 0.50, 0.76, (1, 2)),
    BUTTON_LEFT: (3, 0.22, 0.50, (0, 1)),
    BUTTON_SELECT: (4, 0.50, 0.50, (0, 1, 2, 3)),
    BUTTON_BACK: (5, 0.20, 0.80, (0,)),
    BUTTON_MENU: (6, 0.80, 0.80, (3,)),
}

MAX_PARTICLES = 120
MAX_SPLASHES = 12
MAX_PAINT = 20

GRAVITY = 140.0          # px/s^2 for burst droplets and confetti
BUBBLE_EVERY = 0.16      # seconds between bubbles while a pad is held
POP_TIME = 0.35          # seconds for the big shape to pop in
SPLASH_LIFE = 2.2        # seconds a big shape lives
PAINT_LIFE = 4.5         # seconds a paint stain lingers
IDLE_HINT_AFTER = 4000   # ms without a touch before home spots glow softly

# Particle slots: [life, max_life, x, y, vx, vy, radius, colour, kind]
P_LIFE, P_MAX, P_X, P_Y, P_VX, P_VY, P_R, P_C, P_KIND = range(9)
KIND_DROP, KIND_BUBBLE, KIND_CONFETTI = 0, 1, 2

# Splash slots: [age, x, y, size, colour, form, spin]
S_AGE, S_X, S_Y, S_SIZE, S_C, S_FORM, S_SPIN = range(7)
FORM_CIRCLE, FORM_STAR, FORM_FLOWER = 0, 1, 2

# Paint slots: [age, x, y, radius, colour]
A_AGE, A_X, A_Y, A_R, A_C = range(5)


def _pen(c, alpha):
    r, g, b = RGB[c]
    a = int(alpha)
    screen.pen = color.rgb(r, g, b, 0 if a < 0 else 255 if a > 255 else a)


class Activity:
    def __init__(self):
        # Fixed pools: nothing is allocated per frame except colour values.
        self.particles = [[0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0] for _ in range(MAX_PARTICLES)]
        self.splashes = [[-1.0, 0.0, 0.0, 0.0, 0, 0, 0.0] for _ in range(MAX_SPLASHES)]
        self.paint = [[-1.0, 0.0, 0.0, 0.0, 0] for _ in range(MAX_PAINT)]
        self.background = NIGHT
        self.enter()

    # ------------------------------------------------------------------ life
    def enter(self):
        for p in self.particles:
            p[P_LIFE] = 0.0
        for s in self.splashes:
            s[S_AGE] = -1.0
        for a in self.paint:
            a[A_AGE] = -1.0
        self.p_next = 0
        self.s_next = 0
        self.a_next = 0
        self.bubble_timer = {}
        self.last_touch = badge.ticks
        self.clock = 0.0

    def exit(self):
        self.bubble_timer = {}

    # --------------------------------------------------------------- spawning
    def _particle(self, kind, x, y, vx, vy, radius, c, life):
        p = self.particles[self.p_next]
        self.p_next = (self.p_next + 1) % MAX_PARTICLES
        p[P_LIFE] = life
        p[P_MAX] = life
        p[P_X] = x
        p[P_Y] = y
        p[P_VX] = vx
        p[P_VY] = vy
        p[P_R] = radius
        p[P_C] = c
        p[P_KIND] = kind

    def _home(self, pad):
        c, fx, fy, leds = PADS[pad]
        w, h = screen.width, screen.height
        x = fx * w + random.uniform(-0.12, 0.12) * w
        y = fy * h + random.uniform(-0.10, 0.10) * h
        margin = 0.14 * h
        x = min(w - margin, max(margin, x))
        y = min(h - margin, max(margin, y))
        return c, x, y, leds

    def splash(self, pad):
        c, x, y, leds = self._home(pad)
        unit = screen.height

        s = self.splashes[self.s_next]
        self.s_next = (self.s_next + 1) % MAX_SPLASHES
        s[S_AGE] = 0.0
        s[S_X] = x
        s[S_Y] = y
        s[S_SIZE] = unit * random.uniform(0.16, 0.22)
        s[S_C] = c
        s[S_FORM] = random.randrange(3)
        s[S_SPIN] = random.uniform(-40.0, 40.0)

        a = self.paint[self.a_next]
        self.a_next = (self.a_next + 1) % MAX_PAINT
        a[A_AGE] = 0.0
        a[A_X] = x + random.uniform(-6, 6)
        a[A_Y] = y + random.uniform(-6, 6)
        a[A_R] = unit * random.uniform(0.18, 0.26)
        a[A_C] = c

        count = random.randint(12, 18)
        for i in range(count):
            angle = (i + random.random() * 0.6) * 2 * math.pi / count
            speed = unit * random.uniform(0.55, 1.1)
            self._particle(
                KIND_DROP, x, y,
                math.cos(angle) * speed, math.sin(angle) * speed - unit * 0.25,
                unit * random.uniform(0.022, 0.045), c, random.uniform(0.7, 1.2),
            )

        lights.flash(1.0, leds)

    def bubble(self, pad):
        c, x, y, _ = self._home(pad)
        unit = screen.height
        self._particle(
            KIND_BUBBLE, x, y,
            random.uniform(-0.15, 0.15) * unit, -unit * random.uniform(0.25, 0.45),
            unit * random.uniform(0.03, 0.06), c, random.uniform(1.4, 2.0),
        )

    def confetti(self):
        w, h = screen.width, screen.height
        for i in range(60):
            self._particle(
                KIND_CONFETTI,
                random.uniform(0, w), random.uniform(-0.15, 0.35) * h,
                random.uniform(-0.3, 0.3) * h, random.uniform(-0.5, 0.1) * h,
                h * random.uniform(0.02, 0.04), i % len(RGB), random.uniform(1.4, 2.4),
            )
        lights.flash(0.8)

    # ----------------------------------------------------------------- update
    def update(self, inp):
        dt = inp.dt
        self.clock += dt

        for pad in inp.pressed:
            if pad in PADS:
                self.splash(pad)
                self.bubble_timer[pad] = BUBBLE_EVERY * 2
        if inp.pressed:
            self.last_touch = inp.now

        if inp.shake:
            self.confetti()
            self.last_touch = inp.now

        timers = self.bubble_timer
        for pad in PADS:
            if pad in inp.held:
                t = timers.get(pad, BUBBLE_EVERY) - dt
                if t <= 0:
                    self.bubble(pad)
                    t += BUBBLE_EVERY
                    lights.flash(0.35, PADS[pad][3])
                timers[pad] = t
                self.last_touch = inp.now
            elif pad in timers:
                del timers[pad]

        h = screen.height
        drag = max(0.0, 1.0 - 1.6 * dt)
        for p in self.particles:
            if p[P_LIFE] <= 0:
                continue
            p[P_LIFE] -= dt
            kind = p[P_KIND]
            if kind == KIND_BUBBLE:
                # Bubbles float up and wobble from side to side.
                p[P_VX] += math.sin(self.clock * 4 + p[P_R]) * h * 0.6 * dt
                p[P_VX] *= drag
            else:
                p[P_VX] *= drag
                p[P_VY] = p[P_VY] * drag + GRAVITY * dt
            p[P_X] += p[P_VX] * dt
            p[P_Y] += p[P_VY] * dt
            if p[P_Y] > h + 20 or p[P_Y] < -40:
                p[P_LIFE] = 0.0

        for s in self.splashes:
            if s[S_AGE] >= 0:
                s[S_AGE] += dt
                if s[S_AGE] > SPLASH_LIFE:
                    s[S_AGE] = -1.0
                elif s[S_AGE] > POP_TIME:
                    s[S_Y] -= h * 0.04 * dt  # gentle drift upward

        for a in self.paint:
            if a[A_AGE] >= 0:
                a[A_AGE] += dt
                if a[A_AGE] > PAINT_LIFE:
                    a[A_AGE] = -1.0

    # ------------------------------------------------------------------- draw
    def draw(self):
        screen.pen = self.background
        screen.rectangle(0, 0, screen.width, screen.height)

        self._draw_hints()

        # Soft paint stains that fade slowly.
        for a in self.paint:
            age = a[A_AGE]
            if age < 0:
                continue
            fade = 1.0 - age / PAINT_LIFE
            grow = min(1.0, age * 4.0)
            _pen(a[A_C], 70 * fade)
            screen.shape(shape.circle(a[A_X], a[A_Y], a[A_R] * (0.6 + 0.4 * grow)))

        # Expanding rings and big shapes.
        for s in self.splashes:
            age = s[S_AGE]
            if age < 0:
                continue
            x, y, size, c = s[S_X], s[S_Y], s[S_SIZE], s[S_C]

            if age < 0.8:
                t = age / 0.8
                _pen(c, 220 * (1.0 - t))
                ring = size * (0.6 + 1.6 * t)
                screen.shape(shape.circle(x, y, ring).stroke(max(1, int(size * 0.12 * (1.0 - t)) + 1)))

            if age < POP_TIME:
                scale = ease_out_back(age / POP_TIME)
                alpha = 255
            else:
                scale = 1.0 + 0.08 * (age - POP_TIME)
                alpha = 255 * (1.0 - (age - POP_TIME) / (SPLASH_LIFE - POP_TIME))
            r = size * scale
            if r < 1:
                continue
            _pen(c, alpha)
            form = s[S_FORM]
            if form == FORM_STAR:
                screen.shape(shape.star(x, y, 5, r * 0.5, r))
            elif form == FORM_FLOWER:
                spin = math.radians(s[S_SPIN] * age)
                petal = r * 0.42
                for i in range(6):
                    ang = spin + i * math.pi / 3
                    screen.shape(shape.circle(x + math.cos(ang) * r * 0.58, y + math.sin(ang) * r * 0.58, petal))
                _pen(2 if c != 2 else 1, alpha)  # contrasting centre
                screen.shape(shape.circle(x, y, r * 0.38))
            else:
                screen.shape(shape.circle(x, y, r))
                # A little shine so it looks like a shiny paint blob.
                screen.pen = color.rgb(255, 255, 255, int(max(0, alpha) * 0.45))
                screen.shape(shape.circle(x - r * 0.35, y - r * 0.35, r * 0.2))

        # Droplets, bubbles and confetti on top.
        for p in self.particles:
            life = p[P_LIFE]
            if life <= 0:
                continue
            t = life / p[P_MAX]
            kind = p[P_KIND]
            x, y, r = p[P_X], p[P_Y], p[P_R]
            if kind == KIND_BUBBLE:
                _pen(p[P_C], 200 * min(1.0, t * 2.0))
                screen.shape(shape.circle(x, y, r).stroke(2))
                screen.pen = color.rgb(255, 255, 255, int(150 * t))
                screen.shape(shape.circle(x - r * 0.35, y - r * 0.35, max(1, r * 0.22)))
            elif kind == KIND_CONFETTI:
                _pen(p[P_C], 255 * min(1.0, t * 2.0))
                screen.shape(shape.regular_polygon(x, y, r, 4 if p[P_C] % 2 else 3))
            else:
                _pen(p[P_C], 255 * min(1.0, t * 1.6))
                screen.shape(shape.circle(x, y, max(1, r * (0.4 + 0.6 * t))))

    def _draw_hints(self):
        # After a quiet spell, each pad's home spot glows softly in its colour,
        # inviting a touch. A slow 0.5 Hz breathe, never a flash.
        quiet = badge.ticks - self.last_touch - IDLE_HINT_AFTER
        if quiet <= 0:
            return
        strength = min(1.0, quiet / 1500)
        breathe = 0.5 + 0.5 * math.sin(self.clock * math.pi)
        w, h = screen.width, screen.height
        r = h * (0.05 + 0.015 * breathe)
        for pad in PADS:
            c, fx, fy, _ = PADS[pad]
            _pen(c, (40 + 50 * breathe) * strength)
            screen.shape(shape.circle(fx * w, fy * h, r))
