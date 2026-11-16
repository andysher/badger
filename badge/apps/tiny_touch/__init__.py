"""Tiny Touch: a gentle touch-and-tilt playground for 18-24 month olds.

Launching shows a picker with three activities:
  0  Color Splash      (splash.py)
  1  Peekaboo Animals  (peekaboo.py)
  2  Tilt & Tumble     (tumble.py)

UP/DOWN choose, SELECT starts. A grown-up holds BACK for 3.5 seconds inside an
activity to return to the picker. Every other touch belongs to the toddler.
"""

import gc
import os
import sys

APP_DIR = "/system/apps/tiny_touch"
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

from badgeware import State

from common import Input, lights, WHITE, NIGHT, RAINBOW, clamp

badge.mode(HIRES | VSYNC)

ACTIVITIES = ("splash", "peekaboo", "tumble")
NAMES = ("Color Splash", "Peekaboo Animals", "Tilt & Tumble")
BACK_HOLD_MS = 3500

state = {"activity": 0}
State.load("tiny_touch", state)
if not isinstance(state.get("activity"), int) or not 0 <= state["activity"] < len(ACTIVITIES):
    state["activity"] = 0

inp = Input()
current = None
back_started = None
selected = state["activity"]  # picker highlight, pre-set to the last-played game
in_picker = True


def load_activity(index):
    global current
    unload_activity()
    module = __import__(ACTIVITIES[index])
    current = module.Activity()
    current.enter()
    state["activity"] = index
    State.save("tiny_touch", state)


def unload_activity():
    global current
    if current is not None:
        current.exit()
        current = None
        lights.off()
        gc.collect()


def back_progress():
    """Return 0..1 progress of the BACK hold, leaving the game when it completes."""
    global back_started, in_picker, selected
    if badge.held(BUTTON_BACK):
        if back_started is None:
            back_started = inp.now
        progress = (inp.now - back_started) / BACK_HOLD_MS
        if progress >= 1.0:
            back_started = None
            selected = state["activity"]
            unload_activity()
            in_picker = True
            return 0.0
        return progress
    back_started = None
    return 0.0


def draw_back_hint(progress):
    # A small ring that fills while a grown-up holds BACK.
    if progress <= 0.15:
        return
    cx, cy, r = screen.width - 18, 18, 11
    screen.pen = color.rgb(0, 0, 0, 160)
    screen.shape(shape.circle(cx, cy, r + 3))
    screen.pen = WHITE
    angle = int(360 * clamp(progress, 0.0, 1.0))
    screen.shape(shape.pie(cx, cy, r, 0, angle))


def update_picker():
    global selected, in_picker
    if badge.pressed(BUTTON_UP):
        selected = (selected - 1) % len(ACTIVITIES)
    elif badge.pressed(BUTTON_DOWN):
        selected = (selected + 1) % len(ACTIVITIES)
    elif badge.pressed(BUTTON_SELECT):
        in_picker = False
        load_activity(selected)
        return
    draw_picker()


def draw_picker():
    w, h = screen.width, screen.height
    screen.pen = NIGHT
    screen.rectangle(screen.clip)
    screen.font = font.sins
    screen.pen = WHITE
    title = "Tiny Touch"
    tw, th = screen.measure_text(title)
    screen.text(title, (w - tw) // 2, 10)

    count = len(ACTIVITIES)
    top = 10 + th + 14
    gap = 10
    row_h = clamp((h - top - 24 - gap * (count - 1)) // count, 24, 44)
    row_w = w - 40
    x = 20
    for i in range(count):
        y = top + i * (row_h + gap)
        accent = RAINBOW[(i * 2 + 4) % len(RAINBOW)]
        if i == selected:
            screen.pen = accent
            screen.shape(shape.rounded_rectangle(x - 4, y - 4, row_w + 8, row_h + 8, 8))
        screen.pen = color.rgb(40, 44, 78)
        screen.shape(shape.rounded_rectangle(x, y, row_w, row_h, 6))
        screen.pen = WHITE if i == selected else color.rgb(160, 166, 200)
        name = NAMES[i]
        nw, nh = screen.measure_text(name)
        screen.text(name, x + (row_w - nw) // 2, y + (row_h - nh) // 2)

    screen.font = font.nope
    screen.pen = color.rgb(150, 156, 190)
    hint = "UP/DOWN choose   SELECT play"
    hw, hh = screen.measure_text(hint)
    screen.text(hint, (w - hw) // 2, h - hh - 6)


def update():
    global back_started
    inp.read()
    if in_picker:
        update_picker()
        return
    progress = back_progress()
    if in_picker:
        return
    current.update(inp)
    current.draw()
    draw_back_hint(progress)
    lights.update(inp.dt)


def on_exit():
    lights.off()
    State.save("tiny_touch", state)


run(update)
