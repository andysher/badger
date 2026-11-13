"""Shared helpers for Tiny Touch activities.

Every activity module (splash.py, peekaboo.py, tumble.py) defines a class
named ``Activity`` with this shape:

    class Activity:
        def __init__(self):      # load sprites/assets once
        def enter(self):         # reset to a fresh, friendly starting state
        def update(self, inp):   # inp is an Input snapshot (see below)
        def draw(self):          # draw a complete frame on `screen`
        def exit(self):          # release anything big; lights are reset for you

The shell (``__init__.py``) owns the frame loop, the HIRES display mode, the
parent switch gesture, and the case lights. Activities never call ``run()``.
"""

import math

# 16384 raw units of acceleration is roughly 1 g on the LSM6DS3.
ONE_G = 16384

# Touch pads a toddler can play with. HOME belongs to the launcher.
PLAY_PADS = (
    BUTTON_UP,
    BUTTON_DOWN,
    BUTTON_LEFT,
    BUTTON_RIGHT,
    BUTTON_SELECT,
    BUTTON_BACK,
    BUTTON_MENU,
)

# Bright, high-contrast, toddler-friendly colours (one per play pad).
RED = color.rgb(255, 59, 48)
ORANGE = color.rgb(255, 149, 0)
YELLOW = color.rgb(255, 214, 10)
GREEN = color.rgb(52, 199, 89)
BLUE = color.rgb(10, 132, 255)
PURPLE = color.rgb(175, 82, 222)
PINK = color.rgb(255, 55, 135)
WHITE = color.rgb(255, 255, 255)
INK = color.rgb(24, 24, 40)
NIGHT = color.rgb(16, 18, 36)

PAD_COLOURS = {
    BUTTON_UP: RED,
    BUTTON_RIGHT: ORANGE,
    BUTTON_DOWN: YELLOW,
    BUTTON_LEFT: GREEN,
    BUTTON_SELECT: BLUE,
    BUTTON_BACK: PURPLE,
    BUTTON_MENU: PINK,
}
RAINBOW = (RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK)

# Shake detection: how far (in g) the acceleration magnitude must swing away
# from 1 g, and how long to wait before reporting another shake.
SHAKE_THRESHOLD_G = 0.6
SHAKE_COOLDOWN_MS = 700

# Tilt axis mapping from raw IMU axes to screen axes, calibrated on a real
# badge: held upright (screen facing you) raw Y read about -13400, and tilting
# the right edge down drove raw X from about -1100 to -10800. So tilt_x > 0
# when the right edge is lower, and tilt_y ~ +0.8 when held upright (gravity
# pulls towards the bottom of the screen).
TILT_X_AXIS, TILT_X_SIGN = 0, -1
TILT_Y_AXIS, TILT_Y_SIGN = 1, -1


def clamp(value, low, high):
    return low if value < low else high if value > high else value


class Input:
    """A per-frame snapshot of everything an activity needs.

    Attributes:
        now        badge.ticks (ms)
        dt         seconds since the previous frame, capped at 0.1
        pressed    tuple of PLAY_PADS newly touched this frame
        held       tuple of PLAY_PADS currently touched
        any        True if any play pad was newly touched this frame
        tilt_x     -1..1, positive when the right edge is lower
        tilt_y     -1..1, positive when the bottom edge is lower
        shake      True on the frame a shake is detected
    """

    def __init__(self):
        self.now = 0
        self.dt = 0.0
        self.pressed = ()
        self.held = ()
        self.any = False
        self.tilt_x = 0.0
        self.tilt_y = 0.0
        self.shake = False
        self._last_shake = -SHAKE_COOLDOWN_MS

    def read(self):
        self.now = badge.ticks
        self.dt = min(0.1, badge.ticks_delta / 1000)
        self.pressed = tuple(pad for pad in PLAY_PADS if badge.pressed(pad))
        self.held = tuple(pad for pad in PLAY_PADS if badge.held(pad) or badge.touched(pad))
        self.any = bool(self.pressed)

        raw = badge.imu()
        accel = raw[:3]
        self.tilt_x = clamp(TILT_X_SIGN * accel[TILT_X_AXIS] / ONE_G, -1.0, 1.0)
        self.tilt_y = clamp(TILT_Y_SIGN * accel[TILT_Y_AXIS] / ONE_G, -1.0, 1.0)

        magnitude = math.sqrt(accel[0] * accel[0] + accel[1] * accel[1] + accel[2] * accel[2]) / ONE_G
        self.shake = False
        # An all-zero reading means no IMU data (for example in the simulator).
        if magnitude and abs(magnitude - 1.0) > SHAKE_THRESHOLD_G:
            if self.now - self._last_shake > SHAKE_COOLDOWN_MS:
                self.shake = True
                self._last_shake = self.now
        return self


class Lights:
    """Case lights helper. Call flash() on any happy event; the shell calls
    update() every frame so the glow fades smoothly. Levels are 0..1."""

    def __init__(self):
        self.levels = [0.0, 0.0, 0.0, 0.0]

    def flash(self, level=1.0, which=None):
        """Light all four LEDs, or only the indexes in ``which`` (0..3)."""
        for i in range(4) if which is None else which:
            if level > self.levels[i]:
                self.levels[i] = level

    def update(self, dt):
        fade = max(0.0, 1.0 - 3.0 * dt)
        for i in range(4):
            self.levels[i] *= fade
            if self.levels[i] < 0.02:
                self.levels[i] = 0.0
        badge.caselights(*self.levels)

    def off(self):
        self.levels = [0.0, 0.0, 0.0, 0.0]
        badge.caselights(0)


# One shared Lights instance; activities import it and call lights.flash().
lights = Lights()


def ease_out_back(t):
    """Springy 0..1 easing with a small overshoot, nice for pop-in motion."""
    t = clamp(t, 0.0, 1.0) - 1.0
    return 1.0 + 2.70158 * t * t * t + 1.70158 * t * t
