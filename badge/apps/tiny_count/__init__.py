"""Tiny Count: a gentle counting game for 18-24 month olds.

Tap & Count: every touch adds one object and the numeral grows by one (up to
20, then a celebration). Number Book: pages 1..20 count themselves up. A grown-up
holds BACK for 3.5 seconds to open the mode picker. HOME is left to the
launcher; there is no text, no timer and no way to lose.
"""

import os
import sys

APP_DIR = "/system/apps/tiny_count"
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

from badgeware import State

from board import Board, MODE_TAP, MODE_BOOK
from common import PLAY_PADS, Lights, ShakeDetector, clamp
from picker import draw_picker
from themes import THEMES

badge.mode(HIRES | VSYNC)
screen.antialias = image.X2

BACK_HOLD_MS = 3500
PICKER_TIMEOUT_MS = 15000

# Saved between launches (key "tiny_count"): the last chosen mode and theme.
state = {"mode": MODE_TAP, "theme": 0}
State.load("tiny_count", state)
if not isinstance(state.get("mode"), int) or state["mode"] not in (MODE_TAP, MODE_BOOK):
    state["mode"] = MODE_TAP
if not isinstance(state.get("theme"), int) or not 0 <= state["theme"] < len(THEMES):
    state["theme"] = 0
# A new theme on each launch.
state["theme"] = (state["theme"] + 1) % len(THEMES)
State.save("tiny_count", state)

# Always start in Tap & Count; the picker pre-selects the last chosen mode.
board = Board(state["theme"], MODE_TAP)
lights = Lights()
shake = ShakeDetector()

in_picker = False
picker_choice = state["mode"]
picker_since = 0
back_started = None
back_lock = False  # after the picker, wait for BACK to be released


def save():
    State.save("tiny_count", state)


def open_picker(now):
    global in_picker, picker_choice, picker_since, back_lock, back_started
    in_picker = True
    picker_choice = board.mode
    picker_since = now
    back_lock = True
    back_started = None


def update_picker(now):
    """Handle picker input and draw it; clears ``in_picker`` when done."""
    global in_picker, picker_choice, picker_since
    if badge.pressed(BUTTON_LEFT):
        picker_choice = MODE_TAP
        picker_since = now
    elif badge.pressed(BUTTON_RIGHT):
        picker_choice = MODE_BOOK
        picker_since = now
    elif badge.pressed(BUTTON_SELECT):
        in_picker = False
        if picker_choice != board.mode:
            board.set_mode(picker_choice, now)
            state["mode"] = picker_choice
            save()
        return
    if now - picker_since >= PICKER_TIMEOUT_MS:
        in_picker = False  # back to the current mode, unchanged
        return
    draw_picker(now, picker_choice, 1.0 - (now - picker_since) / PICKER_TIMEOUT_MS)


def back_progress(now):
    """0..1 progress of the BACK hold; opens the picker when it completes."""
    global back_started, back_lock
    if not badge.held(BUTTON_BACK):
        back_started = None
        back_lock = False
        return 0.0
    if back_lock:
        return 0.0
    if back_started is None:
        back_started = now
    progress = (now - back_started) / BACK_HOLD_MS
    if progress >= 1.0:
        open_picker(now)
        return 0.0
    return progress


def draw_back_hint(progress):
    # A small ring that fills while a grown-up holds BACK.
    if progress <= 0.15:
        return
    cx, cy, r = screen.width - 18, screen.height - 18, 11
    screen.pen = color.rgb(0, 0, 0, 120)
    screen.shape(shape.circle(cx, cy, r + 3))
    screen.pen = color.rgb(255, 255, 255)
    screen.shape(shape.pie(cx, cy, r, 0, int(360 * clamp(progress, 0.0, 1.0))))


def update():
    now = badge.ticks
    dt = min(100, badge.ticks_delta)
    pressed = tuple(pad for pad in PLAY_PADS if badge.pressed(pad))
    if in_picker:
        update_picker(now)
        pressed = ()  # the picker consumes this frame's touches
        if in_picker:
            lights.update((0, 0, 0, 0), dt / 1000)
            return
        board.last_input = now
    progress = back_progress(now)
    if in_picker:
        update_picker(now)
        return
    board.update(now, dt, pressed, shake.check(now))
    if board.theme_changed:
        board.theme_changed = False
        state["theme"] = board.theme
        save()
    board.draw(now)
    draw_back_hint(progress)
    lights.update(board.led_targets(), dt / 1000)


def on_exit():
    lights.off()
    save()


run(update)
