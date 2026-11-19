"""The counting board: numeral panel, 5x4 grid of objects, both modes.

One Board object holds all play state. The shell (``__init__.py``) feeds it
input every frame via ``update()`` and asks it to ``draw()``.
"""

import math
import random

from common import clamp, ease_out_back, ease_out_cubic, draw_numeral, measure, VECTOR
from themes import THEMES

MODE_TAP = 0
MODE_BOOK = 1

COLS = 5
ROWS = 4
SLOTS = COLS * ROWS            # 20
MAX_COUNT = SLOTS

DEBOUNCE_MS = 300              # one counted press per 300 ms, across all pads
IDLE_RESET_MS = 90000          # tap mode: a quiet badge starts fresh
POP_MS = 250                   # numeral pop 1.3 -> 1.0
DROP_MS = 300                  # object drop-in
WIGGLE_MS = 600                # milestone / shake wiggle
CELEBRATE_MS = 3000
LEAVE_MS = 900                 # objects float up and away
BOOK_STEP_MS = 350             # number book: time between objects
BOOK_START_MS = 250

# Layout (320x240).
CARD = (4, 10, 98, 220)        # numeral card x, y, w, h
CARD_CX = 53
CARD_CY = 120
NUMERAL_SIZE = 96
NUMERAL_MAX_W = 90
TRAY_X = 108
TRAY_W = 208
TRAY_H = 48
ROW_PITCH = 55
GRID_Y = 10
CELL_W = 41.6
OBJ = 36

CONFETTI = 40
CONFETTI_COLOURS = (
    (255, 59, 48), (255, 149, 0), (255, 214, 10), (52, 199, 89),
    (10, 132, 255), (175, 82, 222), (255, 55, 135),
)

PLAY, CELEBRATE, LEAVE = 0, 1, 2


def slot_xy(i):
    """Centre of grid slot ``i`` (row-major, five per row)."""
    row, col = divmod(i, COLS)
    return TRAY_X + 2 + CELL_W * (col + 0.5), GRID_Y + row * ROW_PITCH + ROW_PITCH / 2 - 3


class Board:
    def __init__(self, theme, mode):
        self.theme = theme
        self.mode = mode
        self.bg = [float(c) for c in THEMES[theme].bg]
        self.born = [0] * SLOTS
        self.confetti = [[0.0, 0.0, 0.0, 0.0, 0, False] for _ in range(CONFETTI)]
        self.width_cache = {}
        self.last_accept = -DEBOUNCE_MS
        self.last_input = 0
        self.theme_changed = False
        self.set_mode(mode, 0)

    # ------------------------------------------------------------------ state

    def set_mode(self, mode, now):
        self.mode = mode
        self.page = 1
        self.reset(now)
        self.last_input = now
        if mode == MODE_BOOK:
            self.start_page(now)

    def reset(self, now):
        self.count = 0
        self.phase = PLAY
        self.phase_start = now
        self.wiggle_until = 0
        self.pop_at = -10000
        self.bump = 0.0
        self.glow = 0.0
        self.target = 0
        self.next_add = 0
        self.advance_theme = False
        for p in self.confetti:
            p[5] = False

    def start_page(self, now):
        """Number Book: clear the page and let the objects appear one by one."""
        self.count = 0
        self.target = self.page
        self.next_add = now + BOOK_START_MS
        self.wiggle_until = 0
        self.pop_at = now

    def add_object(self, now):
        self.born[self.count] = now
        self.count += 1
        self.pop_at = now
        self.bump = 1.0
        if self.mode == MODE_TAP and self.count == MAX_COUNT:
            self.phase = CELEBRATE
            self.phase_start = now
            self.glow = 1.0
            self._burst(now)
        elif self.count % 5 == 0:
            self.wiggle_until = now + WIGGLE_MS
            self.glow = 1.0

    def _begin_leave(self, now, advance_theme):
        self.phase = LEAVE
        self.phase_start = now
        self.advance_theme = advance_theme
        self.last_input = now

    # ----------------------------------------------------------------- update

    def update(self, now, dt, pressed, shake):
        """``pressed`` is the tuple of play pads newly touched this frame."""
        seconds = dt / 1000
        if pressed:
            self.last_input = now
        self.bump = max(0.0, self.bump - dt / 400)
        if self.phase != CELEBRATE:
            self.glow = max(0.0, self.glow - dt / 1000)
        k = min(1.0, seconds * 4)
        target_bg = THEMES[self.theme].bg
        for i in range(3):
            self.bg[i] += (target_bg[i] - self.bg[i]) * k
        self._update_confetti(seconds)

        if self.phase == CELEBRATE:
            self.glow = 0.6 + 0.4 * math.sin((now - self.phase_start) / 1000 * 2 * math.pi * 1.5)
            if now - self.phase_start >= CELEBRATE_MS:
                self._begin_leave(now, True)
            return
        if self.phase == LEAVE:
            if now - self.phase_start >= LEAVE_MS:
                self._finish_leave(now)
            return

        if shake and self.count > 0:
            self.wiggle_until = now + WIGGLE_MS
        if pressed and now - self.last_accept >= DEBOUNCE_MS:
            self.last_accept = now
            if self.mode == MODE_TAP:
                self.add_object(now)
            else:
                self._book_press(now, pressed)

        if self.mode == MODE_BOOK:
            while self.count < self.target and now >= self.next_add:
                self.add_object(now)
                self.next_add += BOOK_STEP_MS
        elif self.count > 0 and now - self.last_input >= IDLE_RESET_MS:
            self._begin_leave(now, False)

    def _book_press(self, now, pressed):
        # Several pads in one frame count once: the first pad decides.
        pad = pressed[0]
        if pad in (BUTTON_RIGHT, BUTTON_DOWN):
            self.page = self.page % MAX_COUNT + 1
        elif pad in (BUTTON_LEFT, BUTTON_UP):
            self.page = (self.page - 2) % MAX_COUNT + 1
        self.start_page(now)

    def _finish_leave(self, now):
        self.count = 0
        self.phase = PLAY
        self.pop_at = now
        self.wiggle_until = 0
        if self.advance_theme:
            self.theme = (self.theme + 1) % len(THEMES)
            self.theme_changed = True

    # --------------------------------------------------------------- confetti

    def _burst(self, now):
        for p in self.confetti:
            p[0] = random.random() * 320
            p[1] = -random.random() * 60
            p[2] = (random.random() - 0.5) * 60
            p[3] = 40 + random.random() * 90
            p[4] = int(random.random() * len(CONFETTI_COLOURS))
            p[5] = True

    def _update_confetti(self, seconds):
        for p in self.confetti:
            if not p[5]:
                continue
            p[0] += p[2] * seconds
            p[1] += p[3] * seconds
            p[3] += 60 * seconds
            if p[1] > 250:
                if self.phase == CELEBRATE:   # keep the shower going gently
                    p[0] = random.random() * 320
                    p[1] = -10
                    p[3] = 40 + random.random() * 60
                else:
                    p[5] = False

    # ------------------------------------------------------------------- leds

    def led_targets(self):
        """Progress bar: LED k lights when count >= 5k, plus a brief bump."""
        out = []
        for k in range(1, 5):
            lit = self.count >= 5 * k
            level = (0.4 + 0.6 * self.bump) if lit else 0.0
            level += 0.5 * self.glow
            out.append(clamp(level, 0.0, 1.0))
        return out

    # ------------------------------------------------------------------- draw

    def draw(self, now):
        theme = THEMES[self.theme]
        screen.pen = color.rgb(int(self.bg[0]), int(self.bg[1]), int(self.bg[2]))
        screen.rectangle(screen.clip)
        self._draw_trays()
        self._draw_objects(now, theme)
        self._draw_numeral(now, theme)
        self._draw_confetti()

    def _draw_trays(self):
        for row in range(ROWS):
            y = GRID_Y + row * ROW_PITCH + (ROW_PITCH - TRAY_H) / 2 - 3
            screen.pen = color.rgb(255, 255, 255, 110)
            screen.shape(shape.rounded_rectangle(TRAY_X, y, TRAY_W, TRAY_H, 12))
        # Very faint outlines for the slots that are still empty.
        screen.pen = color.rgb(90, 90, 120, 55)
        for i in range(self.count, SLOTS):
            x, y = slot_xy(i)
            screen.shape(shape.circle(x, y, 9).stroke(2))

    def _draw_objects(self, now, theme):
        celebrating = self.phase == CELEBRATE
        leave_t = clamp((now - self.phase_start) / LEAVE_MS, 0.0, 1.0) if self.phase == LEAVE else 0.0
        wiggle = clamp((self.wiggle_until - now) / WIGGLE_MS, 0.0, 1.0)
        for i in range(self.count):
            x, y = slot_xy(i)
            age = now - self.born[i]
            size = OBJ
            if age < DROP_MS:
                y -= (1.0 - ease_out_back(age / DROP_MS)) * 70
                size = OBJ * (0.5 + 0.5 * clamp(age / 150, 0.0, 1.0))
            if wiggle > 0:
                x += math.sin(now / 1000 * 2 * math.pi * 3 + i * 0.6) * 4 * wiggle
            if celebrating:
                y -= abs(math.sin((now - self.phase_start) / 1000 * math.pi * 1.5 - i * 0.35)) * 12
            if leave_t > 0:
                y -= leave_t * leave_t * 300
                x += math.sin(leave_t * 5 + i) * 8
            theme.draw(x, y, size, now / 1000 + i * 0.37, i)

    def _draw_numeral(self, now, theme):
        cx, cy, w, h = CARD
        screen.pen = color.rgb(255, 255, 255, 170)
        screen.shape(shape.rounded_rectangle(cx, cy, w, h, 16))
        if self.phase == CELEBRATE:
            r = 42 + 5 * math.sin((now - self.phase_start) / 1000 * 2 * math.pi * 1.5)
            screen.pen = color.rgb(theme.accent[0], theme.accent[1], theme.accent[2], 45)
            screen.shape(shape.circle(CARD_CX, CARD_CY, r))
        text = str(self.count)
        size = self._fit_size(text)
        age = now - self.pop_at
        if age < POP_MS:
            size *= 1.0 + 0.3 * (1.0 - ease_out_cubic(age / POP_MS))
        screen.pen = color.rgb(theme.accent[0], theme.accent[1], theme.accent[2])
        draw_numeral(text, CARD_CX, CARD_CY, int(size))

    def _fit_size(self, text):
        """Largest size up to NUMERAL_SIZE whose text fits the card."""
        if not VECTOR:
            return NUMERAL_SIZE
        width = self.width_cache.get(text)
        if width is None:
            width = measure(text, 100)[0]
            self.width_cache[text] = width
        return min(NUMERAL_SIZE, NUMERAL_MAX_W * 100 / max(1, width))

    def _draw_confetti(self):
        for p in self.confetti:
            if p[5]:
                c = CONFETTI_COLOURS[p[4]]
                screen.pen = color.rgb(c[0], c[1], c[2])
                screen.shape(shape.rectangle(p[0], p[1], 6, 4))
