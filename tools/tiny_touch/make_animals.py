#!/usr/bin/env python3
"""Generate badge/apps/tiny_touch/assets/animals.png for Peekaboo Animals.

Each animal is a front-facing, smiling 32x32 face. Faces are symmetric, so
each one is drawn as its LEFT HALF (16 columns x 32 rows) and mirrored. The
blink frame is made automatically by painting over each eye box with the skin
colour and drawing a happy closed eye (^).

Sheet layout: 2 columns (open eyes, blink) x one row per animal, 32x32 each.
The row order must match ANIMALS in badge/apps/tiny_touch/peekaboo.py.

    python3 tools/tiny_touch/make_animals.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pixelart import write_sheet  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "badge", "apps", "tiny_touch", "assets", "animals.png")

LEGEND = {
    "k": (36, 28, 48),       # ink outline, pupils
    "w": (255, 255, 255),    # white
    "p": (255, 140, 170),    # blush / inner ear pink
    "r": (240, 80, 110),     # tongue
    # cat
    "o": (255, 168, 56),
    "O": (226, 116, 30),
    # dog
    "b": (196, 136, 84),
    "d": (122, 78, 48),
    "t": (246, 216, 168),
    # duck
    "y": (255, 214, 40),
    "n": (255, 140, 26),
    "N": (230, 104, 20),
    # cow
    "K": (70, 62, 80),
    "c": (250, 236, 200),
    "m": (255, 186, 196),
    # pig
    "P": (255, 176, 196),
    "q": (240, 120, 156),
    # frog
    "g": (88, 204, 72),
    "l": (184, 236, 120),
    # lion
    "M": (232, 124, 36),
    "Y": (255, 204, 92),
    "C": (255, 240, 200),
    "B": (150, 80, 60),
}

E = "................"

CAT = [
    E,
    E,
    "..kk............",
    "..kok...........",
    "..kpok..........",
    "..kppok.........",
    "..kpppok........",
    "..kppppokkkkkkkk",
    "..kooooooooOoooO",
    ".kooooooooooOooO",
    ".koooooooooooooO",
    ".koooooooooooooo",
    ".koooooooooooooo",
    ".koooo" + "okkko" + "ooooo",
    ".koooo" + "kwkkk" + "ooooo",
    ".kOOoo" + "kkkkk" + "ooooo",
    ".koooo" + "kkkkk" + "ooooo",
    ".kOOoo" + "okkko" + "ooooo",
    ".koooooooooooooo",
    ".koopp" + "ooooooooo" + "p",
    ".kooooooooookook",
    ".koooooooooookko",
    ".koooooooooooooo",
    "..kooooooooooooo",
    "..kooooooooooooo",
    "...koooooooooooo",
    "....kkoooooooooo",
    "......kkkkoooooo",
    "..........kkkkkk",
    E,
    E,
    E,
]

DOG = [
    E,
    E,
    E,
    "........kkkkkkkk",
    "...kkkkkbbbbbbbb",
    "..kdddkbbbbbbbbb",
    ".kddddkbbbbbbbbb",
    ".kddddkbbbbbbbbb",
    "kddddkbbbbbbbbbb",
    "kddddkbbbbbbbbbb",
    "kddddkbbbbbbbbbb",
    "kddddkb" + "bkkkb" + "bbbb",
    "kddddkb" + "kwkkk" + "bbbb",
    "kddddkb" + "kkkkk" + "bbbb",
    "kddddkb" + "kkkkk" + "bbbb",
    "kddddkb" + "bkkkb" + "bbbb",
    "kddddkbbbbbbbbbb",
    "kddddkbbbbbbtttt",
    "kddddkbbbbtttkkk",
    ".kdddkbbbbttttkk",
    "..kkkkbbbbtttttk",
    ".....kbbbbttkttk",
    ".....kbbbbtttkkr",
    ".....kbbbbttttkr",
    "......kbbbtttttk",
    "......kbbbbttttt",
    ".......kbbbbbttt",
    "........kkbbbbbb",
    "..........kkkkkk",
    E,
    E,
    E,
]

DUCK = [
    E,
    "..............kk",
    ".............kyy",
    "..........kkkkyy",
    "........kkyyyyyy",
    "......kkyyyyyyyy",
    ".....kyyyyyyyyyy",
    "....kyyyyyyyyyyy",
    "...kyyyyyyyyyyyy",
    "...kyyyyyyyyyyyy",
    "..kyyyyyyyyyyyyy",
    "..kyyyy" + "ykkky" + "yyyy",
    "..kyyyy" + "kwkkk" + "yyyy",
    ".kyyyyy" + "kkkkk" + "yyyy",
    ".kyyyyy" + "kkkkk" + "yyyy",
    ".kyyyyy" + "ykkky" + "yyyy",
    ".kyyyyyyyyyyyyyy",
    ".kyyppyyykkkkkkk",
    ".kyyppyyknnnnnnn",
    ".kyyyyyyknnnnknn",
    ".kyyyyyyknnnnnnn",
    ".kyyyyyyykkkkkkk",
    "..kyyyyyykNNNNNN",
    "..kyyyyyyykkkkkk",
    "...kyyyyyyyyyyyy",
    "...kyyyyyyyyyyyy",
    "....kyyyyyyyyyyy",
    ".....kkyyyyyyyyy",
    ".......kkkyyyyyy",
    "..........kkkkkk",
    E,
    E,
]

COW = [
    E,
    E,
    "...kk...........",
    "...kck..........",
    "...kcck.........",
    "....kcckkkkkkkkk",
    "....kKKwwwwwwwww",
    "....kKKKwwwwwwww",
    "kkkkkKKKwwwwwwww",
    "kpppkKKKwwwwwwww",
    "kpppkKKwwwwwwwww",
    ".kkkkwwwwwwwwwww",
    "....kww" + "wkkkw" + "wwww",
    "....kww" + "kwkkk" + "wwww",
    "....kww" + "kkkkk" + "wwww",
    "....kww" + "kkkkk" + "wwww",
    "....kww" + "wkkkw" + "wwww",
    "....kwwwwwwwwwww",
    "....kwwwkkkkkkkk",
    "....kwwkmmmmmmmm",
    "....kwkmmmmmmmmm",
    "....kwkmmmkkmmmm",
    "....kwkmmmkkmmmm",
    "....kwkmmmmmmmmm",
    "....kwkmmmmkmmmm",
    "....kkmmmmmmkkkk",
    ".....kmmmmmmmmmm",
    "......kkmmmmmmmm",
    "........kkkkkkkk",
    E,
    E,
    E,
]

PIG = [
    E,
    E,
    "..kkk...........",
    "..kqqkk.........",
    "..kqqqqkk.......",
    "..kqqqqPPkkkkkkk",
    "..kqqqPPPPPPPPPP",
    "..kqqPPPPPPPPPPP",
    "..kqPPPPPPPPPPPP",
    ".kPPPPPPPPPPPPPP",
    ".kPPPPPPPPPPPPPP",
    ".kPPPP" + "PkkkP" + "PPPPP",
    ".kPPPP" + "kwkkk" + "PPPPP",
    ".kPPPP" + "kkkkk" + "PPPPP",
    ".kPPPP" + "kkkkk" + "PPPPP",
    ".kPPPP" + "PkkkP" + "PPPPP",
    ".kPPPPPPPPPPPPPP",
    ".kPPPPPPPkkkkkkk",
    ".kPPppPPkqqqqqqq",
    ".kPPppPPkqqkkqqq",
    ".kPPPPPPkqqkkqqq",
    ".kPPPPPPkqqqqqqq",
    ".kPPPPPPPkkkkkkk",
    ".kPPPPPPPPPPPPPP",
    "..kPPPPPPPPkPPPP",
    "..kPPPPPPPPPkkkk",
    "...kPPPPPPPPPPPP",
    "....kkPPPPPPPPPP",
    "......kkkkPPPPPP",
    "..........kkkkkk",
    E,
    E,
]

FROG = [
    E,
    E,
    E,
    E,
    E,
    E,
    "....kkkkk.......",
    "...kgggggk......",
    "..kg" + "gwwwg" + "gk" + ".....",
    "..kg" + "wwkkw" + "gk" + ".....",
    "..kg" + "wkkkw" + "gk" + "kkkkk",
    ".kgg" + "wkkkw" + "gg" + "ggggg",
    ".kgg" + "gwwwg" + "ggggggg",
    "kggggggggggggggg",
    "kggggggggggggggg",
    "kgggppgggggggggg",
    "kgggppgggggggggg",
    "kggkgggggggggggg",
    "kgggkggggggggggg",
    "kggggkkkkkkkkkkk",
    "kggggggggggggggg",
    ".kggggllllllllll",
    ".kggglllllllllll",
    "..kgg" + "lllllllllll",
    "...kgg" + "llllllllll",
    "....kkllllllllll",
    "......kkkkkkkkkk",
    E,
    E,
    E,
    E,
    E,
]

LION = [
    E,
    "..........kkkkkk",
    "......kkkkMMMMMM",
    "....kkMMMMMMMMMM",
    "...kMMMMMMMMMMMM",
    "..kMMMMMMkkkkkkk",
    "..kMMMMkkYYYYYYY",
    ".kMMMMkYYYYYYYYY",
    ".kMMMkYYYYYYYYYY",
    ".kMMMkYYYYYYYYYY",
    "kMMMkYYYYYYYYYYY",
    "kMMMkYY" + "YkkkY" + "YYYY",
    "kMMMkYY" + "kwkkk" + "YYYY",
    "kMMMkYY" + "kkkkk" + "YYYY",
    "kMMMkYY" + "kkkkk" + "YYYY",
    "kMMMkYY" + "YkkkY" + "YYYY",
    "kMMMkYYYYYYYYYYY",
    "kMMMkYYYYYYCCBBB",
    "kMMMkYYYYYCCCCBB",
    ".kMMkYYYYYCCCCCk",
    ".kMMkYYYYYCCkCCk",
    ".kMMkYYYYYCCCkkC",
    ".kMMMkYYYYYCCCCC",
    "..kMMkYYYYYYCCCC",
    "..kMMMkYYYYYYYYY",
    "...kMMMkkYYYYYYY",
    "....kMMMMkkkkkkk",
    ".....kMMMMMMMMMM",
    "......kkMMMMMMMM",
    "........kkkkkkkk",
    E,
    E,
]

# name, left-half grid, (eye box x, eye box y) of the left eye, skin under eye
ANIMALS = [
    ("cat", CAT, (6, 13), "o"),
    ("dog", DOG, (7, 11), "b"),
    ("duck", DUCK, (7, 11), "y"),
    ("cow", COW, (7, 12), "w"),
    ("pig", PIG, (6, 11), "P"),
    ("frog", FROG, (4, 8), "g"),
    ("lion", LION, (7, 11), "Y"),
]

EYE = 5  # eye boxes are 5x5
CLOSED_EYE = (".....", ".....", ".kkk.", "k...k", ".....")  # happy ^ eye


def mirror(name, half):
    if len(half) != 32:
        raise ValueError("%s has %d rows, expected 32" % (name, len(half)))
    rows = []
    for y, line in enumerate(half):
        if len(line) != 16:
            raise ValueError("%s row %d is %d wide, expected 16" % (name, y, len(line)))
        rows.append(line + line[::-1])
    return rows


def blink(rows, eye, skin):
    grid = [list(line) for line in rows]
    ex, ey = eye
    for x0 in (ex, 32 - ex - EYE):
        for dy in range(EYE):
            for dx in range(EYE):
                ch = CLOSED_EYE[dy][dx]
                grid[ey + dy][x0 + dx] = skin if ch == "." else ch
    return ["".join(line) for line in grid]


def build():
    frames = []
    for name, half, eye, skin in ANIMALS:
        rows = mirror(name, half)
        frames.append([rows, blink(rows, eye, skin)])
    return frames


def main():
    frames = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fw, fh, cols, rows = write_sheet(OUT, frames, LEGEND, scale=1)
    print("wrote %s: %d x %d frames of %dx%d (%d bytes)"
          % (os.path.relpath(OUT, ROOT), cols, rows, fw, fh, os.path.getsize(OUT)))


if __name__ == "__main__":
    main()
