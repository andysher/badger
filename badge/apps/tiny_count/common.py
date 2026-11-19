"""Shared helpers for Tiny Count: pads, easing, shake, fonts and case lights."""

import math

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

ONE_G = 16384
SHAKE_THRESHOLD_G = 0.6
SHAKE_COOLDOWN_MS = 700

# --------------------------------------------------------------------------
# Fonts: DynaPuff is a vector font that scales to any size. If it cannot be
# loaded, fall back to a built-in pixel font (fixed size), as the abc app does.

try:
    BIG_FONT = font.load("/system/assets/fonts/DynaPuff-Medium.af")
    VECTOR = True
except Exception as error:  # noqa: BLE001 - any failure means "use fallback"
    print("tiny_count: vector font unavailable:", error)
    BIG_FONT = font.ziplock
    VECTOR = False


def measure(text, size):
    if VECTOR:
        return screen.measure_text(text, font_size=size)
    return screen.measure_text(text)


def write(text, x, y, size):
    if VECTOR:
        screen.text(text, x, y, size)
    else:
        screen.text(text, x, y)


# DynaPuff digit metrics as fractions of the font size, measured from the y
# passed to screen.text() (same measurements the abc app uses; not confirmed
# on hardware): capitals and digits start at ~0.44 and sit on baseline 1.0.
DIGIT_TOP = 0.44
DIGIT_BASE = 1.0


def draw_numeral(text, cx, cy, size):
    """Draw ``text`` centred on (cx, cy) using the vector font at ``size``."""
    screen.font = BIG_FONT
    w, h = measure(text, size)
    if VECTOR:
        y = cy - (DIGIT_TOP + DIGIT_BASE) / 2 * size
    else:
        y = cy - h / 2
    write(text, int(cx - w / 2), int(y), size)


def clamp(value, low, high):
    return low if value < low else high if value > high else value


def ease_out_cubic(t):
    t = 1.0 - clamp(t, 0.0, 1.0)
    return 1.0 - t * t * t


def ease_out_back(t):
    """Springy 0..1 easing with a small overshoot, nice for drop-in motion."""
    t = clamp(t, 0.0, 1.0) - 1.0
    return 1.0 + 2.70158 * t * t * t + 1.70158 * t * t


class ShakeDetector:
    """Reports True once per shake, using the same rule as Tiny Touch."""

    def __init__(self):
        self._last = -SHAKE_COOLDOWN_MS

    def check(self, now):
        accel = badge.imu()[:3]
        magnitude = math.sqrt(accel[0] * accel[0] + accel[1] * accel[1] + accel[2] * accel[2]) / ONE_G
        # An all-zero reading means no IMU data (for example in a simulator).
        if magnitude and abs(magnitude - 1.0) > SHAKE_THRESHOLD_G:
            if now - self._last > SHAKE_COOLDOWN_MS:
                self._last = now
                return True
        return False


class Lights:
    """Case lights with eased changes: levels glide to their targets (about
    a quarter of a second), so nothing ever flashes."""

    RATE = 6.0  # per second; ~170 ms to cover most of a step

    def __init__(self):
        self.levels = [0.0, 0.0, 0.0, 0.0]

    def update(self, targets, dt):
        k = min(1.0, self.RATE * dt)
        for i in range(4):
            self.levels[i] += (targets[i] - self.levels[i]) * k
            if self.levels[i] < 0.01 and targets[i] == 0:
                self.levels[i] = 0.0
        badge.caselights(*self.levels)

    def off(self):
        self.levels = [0.0, 0.0, 0.0, 0.0]
        badge.caselights(0)
