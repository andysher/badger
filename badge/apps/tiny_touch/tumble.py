"""Tilt & Tumble: chunky shape friends roll around a box as the badge tilts.

Teaches shapes, colours and gravity. Tilting the badge pulls the shapes that
way, a shake scatters them, and touching a pad makes the shape with that pad's
colour hop up with a happy face. With no tilt reading (simulator, or a badge
lying flat) a gentle default gravity pulls everything towards the bottom.
"""

import math
import random

from common import ease_out_back, clamp, lights

# Sprite sheet rows, in rainbow order (see tools/tiny_touch/make_shapes.py).
CIRCLE, SQUARE, STAR, TRIANGLE, DIAMOND, MOON, HEART = range(7)
SHAPE_COUNT = 7

# Each play pad hops the shape that matches its PAD_COLOURS colour.
PAD_SHAPE = {
    BUTTON_UP: CIRCLE,        # red
    BUTTON_RIGHT: SQUARE,     # orange
    BUTTON_DOWN: STAR,        # yellow
    BUTTON_LEFT: TRIANGLE,    # green
    BUTTON_SELECT: DIAMOND,   # blue
    BUTTON_BACK: MOON,        # purple
    BUTTON_MENU: HEART,       # pink
}

# --- Physics constants (pixels and seconds). Tune these on hardware. ---
GRAVITY = 950.0          # acceleration at a full 1 g tilt
IDLE_GRAVITY = 320.0     # gentle downward pull when tilt reads ~0
DEADZONE = 0.12          # tilt magnitude (g) ignored as noise / "flat"
BLEND = 0.15             # tilt range over which idle gravity fades out
AIR_DRAG = 0.6           # fraction of velocity lost per second
WALL_FRICTION = 5.0      # tangential slow-down per second while on a wall
WALL_BOUNCE = 0.45       # restitution against the walls
BODY_BOUNCE = 0.5        # restitution between shapes
REST_SPEED = 60.0        # impacts slower than this do not bounce (settles)
MAX_SPEED = 650.0        # velocity clamp, keeps every substep small
SUBSTEP = 1 / 60         # max physics step; no tunnelling at large dt
HOP_SPEED = 560.0        # pad touch hop
SHAKE_SPEED = 520.0      # shake scatter
FLASH_SPEED = 260.0      # wall impacts faster than this light the LEDs
SQUASH_MAX = 0.32        # max squash-and-stretch amount


class Body:
    def __init__(self, index, x, y, radius):
        self.index = index
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.r = radius
        self.happy = 0.0      # seconds left showing the happy face
        self.squash = 0.0     # squash amplitude
        self.squash_t = 0.0   # seconds since the squash started
        self.squash_x = False # True: squeezed sideways (hit a side wall)

    def bump(self, amount, sideways):
        amount = min(SQUASH_MAX, amount)
        if amount > self.squash * math.exp(-6.0 * self.squash_t):
            self.squash = amount
            self.squash_t = 0.0
            self.squash_x = sideways


class Activity:
    def __init__(self):
        self.sheet = image.load("assets/shapes.png").spritesheet(2, SHAPE_COUNT)
        w, h = screen.width, screen.height
        self.size = w * 3 // 16                      # 60 px on HIRES
        self.radius = self.size * 0.44
        # Calm sky-to-cream background bands, computed once.
        self.bands = []
        count = 8
        for i in range(count):
            t = i / (count - 1)
            self.bands.append((
                int(h * i / count),
                int(h * (i + 1) / count) - int(h * i / count),
                color.rgb(int(212 + 43 * t), int(230 + 12 * t), int(255 - 30 * t)),
            ))
        self.bodies = []
        self.gx = 0.0
        self.gy = IDLE_GRAVITY
        self.age = 0.0
        self.next_wiggle = 3.0

    def enter(self):
        w, h = screen.width, screen.height
        spots = []
        for i in range(4):
            spots.append((w * (2 * i + 1) / 8, h * 0.33))
        for i in range(3):
            spots.append((w * (i + 1) / 4, h * 0.70))
        self.bodies = []
        for i in range(SHAPE_COUNT):
            x, y = spots[i]
            body = Body(i, x + random.uniform(-6, 6), y + random.uniform(-6, 6), self.radius)
            self.bodies.append(body)
        self.age = 0.0
        self.next_wiggle = 3.0

    def exit(self):
        self.bodies = []
        self.sheet = None

    # --- input -----------------------------------------------------------

    def _gravity(self, inp):
        tx, ty = inp.tilt_x, inp.tilt_y
        mag = math.sqrt(tx * tx + ty * ty)
        k = clamp((mag - DEADZONE) / BLEND, 0.0, 1.0)
        if k > 0:
            scale = GRAVITY * (mag - DEADZONE) / (mag * (1.0 - DEADZONE))
            tilt_gx, tilt_gy = tx * scale, ty * scale
        else:
            tilt_gx, tilt_gy = 0.0, 0.0
        self.gx = tilt_gx * k
        self.gy = tilt_gy * k + IDLE_GRAVITY * (1.0 - k)

    def _up(self):
        """Unit vector pointing against gravity."""
        g = math.sqrt(self.gx * self.gx + self.gy * self.gy)
        if g < 1.0:
            return 0.0, -1.0
        return -self.gx / g, -self.gy / g

    def _hop(self, body):
        ux, uy = self._up()
        side = random.uniform(-0.35, 0.35)
        body.vx += (ux - uy * side) * HOP_SPEED
        body.vy += (uy + ux * side) * HOP_SPEED
        body.happy = 1.2
        body.bump(0.25, abs(ux) > abs(uy))
        lights.flash(1.0)

    def _shake(self):
        ux, uy = self._up()
        for body in self.bodies:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.5, 1.0) * SHAKE_SPEED
            body.vx += math.cos(angle) * speed + ux * SHAKE_SPEED * 0.4
            body.vy += math.sin(angle) * speed + uy * SHAKE_SPEED * 0.4
            body.happy = 1.5
            body.bump(SQUASH_MAX, random.random() < 0.5)
        lights.flash(1.0)

    def update(self, inp):
        dt = inp.dt
        self.age += dt
        self._gravity(inp)

        for pad in inp.pressed:
            index = PAD_SHAPE.get(pad)
            if index is not None:
                self._hop(self.bodies[index])
        if inp.shake:
            self._shake()

        # An occasional idle giggle keeps a still scene alive.
        self.next_wiggle -= dt
        if self.next_wiggle <= 0:
            self.next_wiggle = random.uniform(2.5, 5.0)
            body = self.bodies[random.randrange(len(self.bodies))]
            if body.happy <= 0:
                body.happy = 0.5
                body.bump(0.12, False)

        steps = max(1, int(math.ceil(dt / SUBSTEP)))
        h = dt / steps
        for _ in range(steps):
            self._step(h)

        for body in self.bodies:
            if body.happy > 0:
                body.happy -= dt
            body.squash_t += dt

    # --- physics ---------------------------------------------------------

    def _step(self, dt):
        bodies = self.bodies
        drag = max(0.0, 1.0 - AIR_DRAG * dt)
        gx, gy = self.gx * dt, self.gy * dt
        for b in bodies:
            b.vx = (b.vx + gx) * drag
            b.vy = (b.vy + gy) * drag
            speed2 = b.vx * b.vx + b.vy * b.vy
            if speed2 > MAX_SPEED * MAX_SPEED:
                s = MAX_SPEED / math.sqrt(speed2)
                b.vx *= s
                b.vy *= s
            b.x += b.vx * dt
            b.y += b.vy * dt

        # Shape-vs-shape: equal-mass circles with a soft bounce.
        n = len(bodies)
        for i in range(n):
            a = bodies[i]
            for j in range(i + 1, n):
                b = bodies[j]
                dx = b.x - a.x
                dy = b.y - a.y
                reach = a.r + b.r
                d2 = dx * dx + dy * dy
                if d2 >= reach * reach:
                    continue
                d = math.sqrt(d2)
                if d < 0.001:
                    dx, dy, d = 1.0, 0.0, 1.0
                nx, ny = dx / d, dy / d
                push = (reach - d) * 0.5
                a.x -= nx * push
                a.y -= ny * push
                b.x += nx * push
                b.y += ny * push
                vn = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny
                if vn < 0:
                    bounce = BODY_BOUNCE if -vn > REST_SPEED else 0.0
                    jn = -(1.0 + bounce) * vn * 0.5
                    a.vx -= jn * nx
                    a.vy -= jn * ny
                    b.vx += jn * nx
                    b.vy += jn * ny
                    if -vn > FLASH_SPEED:
                        amount = -vn / 2000
                        a.bump(amount, abs(nx) > abs(ny))
                        b.bump(amount, abs(nx) > abs(ny))

        # Walls: the screen edges.
        w, h = screen.width, screen.height
        friction = max(0.0, 1.0 - WALL_FRICTION * dt)
        for b in bodies:
            r = b.r
            if b.x < r:
                b.x = r
                if b.vx < 0:
                    self._wall(b, -b.vx, True)
                    b.vx = -b.vx * (WALL_BOUNCE if -b.vx > REST_SPEED else 0.0)
                b.vy *= friction
            elif b.x > w - r:
                b.x = w - r
                if b.vx > 0:
                    self._wall(b, b.vx, True)
                    b.vx = -b.vx * (WALL_BOUNCE if b.vx > REST_SPEED else 0.0)
                b.vy *= friction
            if b.y < r:
                b.y = r
                if b.vy < 0:
                    self._wall(b, -b.vy, False)
                    b.vy = -b.vy * (WALL_BOUNCE if -b.vy > REST_SPEED else 0.0)
                b.vx *= friction
            elif b.y > h - r:
                b.y = h - r
                if b.vy > 0:
                    self._wall(b, b.vy, False)
                    b.vy = -b.vy * (WALL_BOUNCE if b.vy > REST_SPEED else 0.0)
                b.vx *= friction

    def _wall(self, body, speed, sideways):
        if speed > REST_SPEED:
            body.bump(speed / 1800, sideways)
        if speed > FLASH_SPEED:
            lights.flash(clamp(speed / MAX_SPEED, 0.2, 0.7))
            if body.happy <= 0:
                body.happy = 0.35

    # --- drawing ---------------------------------------------------------

    def draw(self):
        w = screen.width
        for y, band_h, pen in self.bands:
            screen.pen = pen
            screen.rectangle(0, y, w, band_h)

        size = self.size
        sheet = self.sheet
        for b in self.bodies:
            # Staggered springy pop-in when the activity starts.
            grow = ease_out_back((self.age - b.index * 0.07) / 0.45)
            if grow <= 0.02:
                continue
            s = b.squash * math.exp(-6.0 * b.squash_t) * math.cos(22.0 * b.squash_t)
            if b.squash_x:
                sw, sh = 1.0 - s, 1.0 + s
            else:
                sw, sh = 1.0 + s, 1.0 - s
            dw = int(size * sw * grow)
            dh = int(size * sh * grow)
            if dw < 2 or dh < 2:
                continue
            frame = 1 if b.happy > 0 else 0
            screen.blit(
                sheet.sprite(frame, b.index),
                rect(int(b.x - dw / 2), int(b.y - dh / 2), dw, dh),
            )
