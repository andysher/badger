"""Tiny Touch: a gentle touch-and-tilt playground for 18-24 month olds.

Three activities share one shell:
  0  Color Splash      (splash.py)
  1  Peekaboo Animals  (peekaboo.py)
  2  Tilt & Tumble     (tumble.py)

Grown-ups switch activity by holding BACK and MENU together for 1.5 seconds.
Every other touch belongs to the toddler.
"""

import gc
import os
import sys

APP_DIR = "/system/apps/tiny_touch"
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

from badgeware import State

from common import Input, lights, WHITE, clamp

badge.mode(HIRES | VSYNC)

ACTIVITIES = ("splash", "peekaboo", "tumble")
SWITCH_HOLD_MS = 1500

state = {"activity": 0}
State.load("tiny_touch", state)
if not isinstance(state.get("activity"), int) or not 0 <= state["activity"] < len(ACTIVITIES):
    state["activity"] = 0

inp = Input()
current = None
switch_started = None


def load_activity(index):
    global current
    if current is not None:
        current.exit()
        current = None
        lights.off()
        gc.collect()
    module = __import__(ACTIVITIES[index])
    current = module.Activity()
    current.enter()
    state["activity"] = index


def parent_switch():
    """Return 0..1 progress of the BACK+MENU hold, switching when it completes."""
    global switch_started
    if badge.held(BUTTON_BACK) and badge.held(BUTTON_MENU):
        if switch_started is None:
            switch_started = inp.now
        progress = (inp.now - switch_started) / SWITCH_HOLD_MS
        if progress >= 1.0:
            switch_started = None
            load_activity((state["activity"] + 1) % len(ACTIVITIES))
            State.save("tiny_touch", state)
            return 0.0
        return progress
    switch_started = None
    return 0.0


def draw_switch_hint(progress):
    # A small ring that fills while a grown-up holds BACK + MENU.
    if progress <= 0.15:
        return
    cx, cy, r = screen.width - 18, 18, 11
    screen.pen = color.rgb(0, 0, 0, 160)
    screen.shape(shape.circle(cx, cy, r + 3))
    screen.pen = WHITE
    angle = int(360 * clamp(progress, 0.0, 1.0))
    screen.shape(shape.pie(cx, cy, r, 0, angle))


load_activity(state["activity"])


def update():
    inp.read()
    progress = parent_switch()
    current.update(inp)
    current.draw()
    draw_switch_hint(progress)
    lights.update(inp.dt)


def on_exit():
    lights.off()
    State.save("tiny_touch", state)


run(update)
