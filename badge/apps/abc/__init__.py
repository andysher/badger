"""ABC: a picture alphabet for toddlers.

One letter per screen: a big "A a", a 64x64 picture and the word ("Apple")
with its first letter highlighted. LEFT/RIGHT step through the alphabet
(wrapping Z->A and A->Z); every other play pad makes the picture bounce,
squish or wiggle. HOME is left to the launcher.
"""

import gc
import math
import os
import sys

APP_DIR = "/system/apps/abc"
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

from badgeware import State

badge.mode(LORES | VSYNC)
screen.antialias = image.X2

# --------------------------------------------------------------------------
# Content

WORDS = (
    "Apple", "Ball", "Cat", "Dog", "Elephant", "Fish", "Goat", "Horse",
    "Ink pen", "Juice", "Kite", "Lion", "Monkey", "Nose", "Oranges", "Pig",
    "Queen", "Rabbit", "Sun", "Tree", "Umbrella", "Violin", "Watch",
    "Xylophone", "Yo-yo", "Zebra",
)
COUNT = len(WORDS)
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWER = "abcdefghijklmnopqrstuvwxyz"

# Bright, friendly backgrounds (all light enough for dark INK text) and a
# matching deep accent for the highlighted first letter on the white word pill.
PALETTE = (
    ((255, 214, 10), (200, 30, 40)),     # sunny yellow / red
    ((110, 200, 255), (20, 80, 190)),    # sky / blue
    ((255, 150, 190), (180, 20, 110)),   # pink / magenta
    ((120, 225, 150), (15, 120, 55)),    # mint / green
    ((255, 165, 80), (190, 70, 0)),      # orange / burnt orange
    ((195, 165, 255), (110, 40, 180)),   # lavender / purple
    ((180, 235, 90), (40, 110, 20)),     # lime / leaf
    ((90, 220, 225), (0, 105, 120)),     # aqua / teal
    ((255, 130, 120), (170, 25, 30)),    # coral / deep red
)
INK = (30, 30, 60)
WHITE = (255, 255, 255)

# --------------------------------------------------------------------------
# Layout (160x120 logical screen)

PIC = 64                 # picture size from the asset contract
PIC_X = 90               # picture top-left when at rest
PIC_Y = 6
PIC_CX = PIC_X + PIC // 2
PIC_BOTTOM = PIC_Y + PIC

LETTER_BOX = (4, 4, 82, 70)      # x, y, w, h for "A a"
LETTER_SIZE = 72
WORD_PILL = (4, 80, 152, 36)     # x, y, w, h, white rounded pill for the word
WORD_SIZE = 30
WORD_PAD = 8

TRANSITION_MS = 320
ACTION_MS = 600
SAVE_AFTER_MS = 3000

# --------------------------------------------------------------------------
# Fonts: a vector font scales to big chunky letters; fall back to a built-in
# pixel font (no sizes) if the vector font cannot be loaded.

try:
    BIG_FONT = font.load("/system/assets/fonts/DynaPuff-Medium.af")
    VECTOR = True
except Exception as error:  # noqa: BLE001 - any failure means "use fallback"
    print("abc: vector font unavailable:", error)
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


def pen(rgb, alpha=255):
    screen.pen = color.rgb(rgb[0], rgb[1], rgb[2], alpha)


def clamp(value, low, high):
    return low if value < low else high if value > high else value


def ease_out_cubic(t):
    t = 1.0 - clamp(t, 0.0, 1.0)
    return 1.0 - t * t * t


def ease_out_back(t):
    t = clamp(t, 0.0, 1.0) - 1.0
    return 1.0 + 2.70158 * t * t * t + 1.70158 * t * t


def lerp_rgb(a, b, t):
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


# --------------------------------------------------------------------------
# Pictures: loaded on demand, keeping only the current letter and its two
# neighbours. A missing or broken file is remembered as MISSING so we never
# retry it every frame, and the screen still shows the letter and word.

MISSING = False
pictures = {}


def picture_path(index):
    return "assets/%s.png" % LOWER[index]


def load_picture(index):
    if index in pictures:
        return pictures[index]
    try:
        picture = image.load(picture_path(index))
    except Exception as error:  # noqa: BLE001 - OSError, ValueError, MemoryError...
        print("abc: could not load", picture_path(index), error)
        picture = MISSING
    pictures[index] = picture
    return picture


def keep_pictures(index):
    wanted = (index, (index - 1) % COUNT, (index + 1) % COUNT)
    dropped = False
    for key in list(pictures.keys()):
        if key not in wanted:
            del pictures[key]
            dropped = True
    if dropped:
        gc.collect()


def preload_one_neighbour(index):
    for neighbour in ((index + 1) % COUNT, (index - 1) % COUNT):
        if neighbour not in pictures:
            load_picture(neighbour)
            return


# --------------------------------------------------------------------------
# Layout per letter: worked out once when the letter changes, not every frame.

class Layout:
    def __init__(self, index):
        screen.font = BIG_FONT
        self.upper = UPPER[index]
        self.lower = LOWER[index]
        self.word = WORDS[index]
        self.first = self.word[:1]
        self.rest = self.word[1:]

        # "A a": shrink until both letters fit the letter box.
        bx, by, bw, bh = LETTER_BOX
        size = LETTER_SIZE
        for _ in range(8):
            uw, uh = measure(self.upper, size)
            lw, lh = measure(self.lower, size)
            gap = size * 0.12
            total = uw + gap + lw
            height = max(uh, lh)
            if total <= bw and height <= bh:
                break
            size *= min(bw / max(total, 1), bh / max(height, 1)) * 0.98
        self.letter_size = size
        self.upper_x = bx + (bw - total) / 2
        self.lower_x = self.upper_x + uw + gap
        self.upper_y = by + (bh - uh) / 2
        self.lower_y = by + (bh - lh) / 2

        # Word: shrink to fit inside the white pill.
        px, py, pw, ph = WORD_PILL
        size = WORD_SIZE
        for _ in range(8):
            fw, fh = measure(self.first, size)
            rw, rh = measure(self.rest, size) if self.rest else (0, 0)
            total = fw + rw
            height = max(fh, rh)
            if total <= pw - 2 * WORD_PAD and height <= ph - 4:
                break
            size *= min((pw - 2 * WORD_PAD) / max(total, 1), (ph - 4) / max(height, 1)) * 0.98
        self.word_size = size
        self.first_x = px + (pw - total) / 2
        self.rest_x = self.first_x + fw
        self.word_y = py + (ph - height) / 2
        self.word_w = total


# --------------------------------------------------------------------------
# App state

saved = {"letter": 0}
try:
    State.load("abc", saved)
except Exception as error:  # noqa: BLE001 - corrupt state must not stop the app
    print("abc: could not load state:", error)
letter = saved.get("letter", 0)
if not isinstance(letter, int) or not 0 <= letter < COUNT:
    letter = 0

layout = Layout(letter)
previous_bg = PALETTE[letter % len(PALETTE)][0]
changed_at = -TRANSITION_MS * 10   # no slide-in on launch...
slide_dir = 1
pop_at = badge.ticks               # ...but the first picture pops in gently
action = None                      # "jump", "squish" or "wiggle"
action_at = 0
last_change = badge.ticks
glow = 0.0

load_picture(letter)


def set_letter(index, direction):
    global letter, layout, previous_bg, changed_at, slide_dir, pop_at, action
    global last_change, glow
    previous_bg = current_bg(badge.ticks)
    letter = index % COUNT
    layout = Layout(letter)
    changed_at = badge.ticks
    pop_at = badge.ticks
    slide_dir = direction
    action = None
    last_change = badge.ticks
    glow = 0.35
    keep_pictures(letter)
    load_picture(letter)


def start_action(name):
    global action, action_at, glow
    action = name
    action_at = badge.ticks
    glow = max(glow, 0.25)


def current_bg(now):
    target = PALETTE[letter % len(PALETTE)][0]
    t = (now - changed_at) / TRANSITION_MS
    if t >= 1.0:
        return target
    return lerp_rgb(previous_bg, target, ease_out_cubic(t))


def save_if_settled(now):
    if saved.get("letter") != letter and now - last_change > SAVE_AFTER_MS:
        save_state()


def save_state():
    saved["letter"] = letter
    try:
        State.save("abc", saved)
    except Exception as error:  # noqa: BLE001 - a failed save is not fatal
        print("abc: could not save state:", error)


# --------------------------------------------------------------------------
# Input

def handle_input():
    step = 0
    if badge.pressed(BUTTON_RIGHT):
        step += 1
    if badge.pressed(BUTTON_LEFT):
        step -= 1
    if step:
        set_letter(letter + step, step)
        return

    if badge.pressed(BUTTON_SELECT) or badge.pressed(BUTTON_UP):
        start_action("jump")
    elif badge.pressed(BUTTON_DOWN):
        start_action("squish")
    elif badge.pressed(BUTTON_BACK) or badge.pressed(BUTTON_MENU):
        start_action("wiggle")


# --------------------------------------------------------------------------
# Drawing

def picture_motion(now):
    """Return (dx, dy, scale_x, scale_y) for the picture this frame."""
    dy = math.sin(now / 650) * 2.0          # gentle idle bob
    dx = 0.0
    sx = sy = 1.0

    pop = (now - pop_at) / 450
    if pop < 1.0:
        s = 0.55 + 0.45 * ease_out_back(pop)
        sx *= s
        sy *= s

    if action is not None:
        t = (now - action_at) / ACTION_MS
        if 0.0 <= t < 1.0:
            if action == "jump":
                dy -= 16 * math.sin(math.pi * t)
                squash = 0.12 * math.sin(math.pi * t)
                sx *= 1.0 - squash
                sy *= 1.0 + squash
            elif action == "squish":
                squash = 0.25 * math.sin(math.pi * t)
                sx *= 1.0 + squash * 0.8
                sy *= 1.0 - squash
            else:  # wiggle
                wobble = 0.14 * math.sin(t * math.pi * 6) * (1.0 - t)
                sx *= 1.0 + wobble
                sy *= 1.0 - wobble
                dx += 3 * math.sin(t * math.pi * 4) * (1.0 - t)
    return dx, dy, sx, sy


def draw_picture(now, offset):
    dx, dy, sx, sy = picture_motion(now)
    w = PIC * sx
    h = PIC * sy
    x = PIC_CX - w / 2 + dx + offset
    y = PIC_BOTTOM - h + dy
    picture = pictures.get(letter, MISSING)
    if picture is MISSING or picture is None:
        # Friendly soft blob where the picture would be.
        pen(WHITE, 110)
        screen.shape(shape.circle(int(x + w / 2), int(y + h / 2), int(min(w, h) / 2 - 2)))
        return
    screen.blit(picture, rect(int(x), int(y), max(1, int(w)), max(1, int(h))))


def draw_letters(offset):
    screen.font = BIG_FONT
    # Soft shadow, then ink.
    pen(WHITE, 140)
    write(layout.upper, layout.upper_x + offset + 1, layout.upper_y + 2, layout.letter_size)
    write(layout.lower, layout.lower_x + offset + 1, layout.lower_y + 2, layout.letter_size)
    pen(INK)
    write(layout.upper, layout.upper_x + offset, layout.upper_y, layout.letter_size)
    write(layout.lower, layout.lower_x + offset, layout.lower_y, layout.letter_size)


def draw_word(offset):
    px, py, pw, ph = WORD_PILL
    pen(WHITE)
    screen.shape(shape.rounded_rectangle(px, py, pw, ph, 12))

    screen.font = BIG_FONT
    accent = PALETTE[letter % len(PALETTE)][1]
    pen(accent)
    write(layout.first, layout.first_x + offset, layout.word_y, layout.word_size)
    if layout.rest:
        pen(INK)
        write(layout.rest, layout.rest_x + offset, layout.word_y, layout.word_size)
    # Underline the highlighted first letter.
    fw, _ = measure(layout.first, layout.word_size)
    pen(accent)
    screen.shape(shape.rounded_rectangle(
        int(layout.first_x + offset), py + ph - 7, max(4, int(fw)), 3, 1))


def update_lights(dt):
    global glow
    if glow <= 0.0:
        return
    glow = max(0.0, glow - dt * 0.6)
    try:
        badge.caselights(glow)
    except Exception:  # noqa: BLE001 - lights are a bonus, never fatal
        glow = 0.0


def draw_frame(now):
    bg = current_bg(now)
    pen(bg)
    screen.shape(shape.rectangle(0, 0, screen.width, screen.height))

    t = (now - changed_at) / TRANSITION_MS
    offset = 0
    if t < 1.0:
        offset = int(slide_dir * 28 * (1.0 - ease_out_cubic(t)))

    draw_picture(now, offset)
    draw_letters(offset)
    draw_word(offset)


def draw_fallback():
    """Bare-bones frame used only if the normal frame raised an error."""
    pen(PALETTE[letter % len(PALETTE)][0])
    screen.shape(shape.rectangle(0, 0, screen.width, screen.height))
    screen.font = font.ziplock
    pen(INK)
    text = "%s %s  %s" % (UPPER[letter], LOWER[letter], WORDS[letter])
    w, h = screen.measure_text(text)
    screen.text(text, (screen.width - w) / 2, (screen.height - h) / 2)


def update():
    now = badge.ticks
    dt = min(0.1, badge.ticks_delta / 1000)
    try:
        handle_input()
        draw_frame(now)
        if now - changed_at > TRANSITION_MS:
            preload_one_neighbour(letter)
        update_lights(dt)
        save_if_settled(now)
    except Exception as error:  # noqa: BLE001 - never leave a toddler on a crash screen
        print("abc: frame error:", error)
        draw_fallback()


def on_exit():
    try:
        badge.caselights(0)
    except Exception:  # noqa: BLE001
        pass
    if saved.get("letter") != letter:
        save_state()


run(update)
