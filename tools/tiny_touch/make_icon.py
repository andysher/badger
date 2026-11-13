#!/usr/bin/env python3
"""Generate badge/apps/tiny_touch/icon.png: a happy duck face on a sky disc.

The design is 24x24 (left half mirrored) written at scale=2, so the icon is
48x48 and stays crisp in the badge menu.

    python3 tools/tiny_touch/make_icon.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pixelart import write_sheet  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "badge", "apps", "tiny_touch", "icon.png")

LEGEND = {
    "s": (90, 190, 255),    # sky disc
    "k": (36, 28, 48),      # ink
    "w": (255, 255, 255),
    "y": (255, 214, 40),    # duck yellow
    "p": (255, 140, 170),   # blush
    "n": (255, 140, 26),    # beak
    "N": (230, 104, 20),    # lower beak
}

# Left half, 12 columns x 24 rows. Mirrored to 24x24.
HALF = [
    "....ssssssss",
    "..ssssssssss",
    ".sssssssssks",
    ".ssssssssksk",
    "sssssssskkyy",
    "sssssskkyyyy",
    "sssskkyyyyyy",
    "ssskyyyyyyyy",
    "sskyyyyyyyyy",
    "sskyykkyyyyy",
    "skyyykkyyyyy",
    "skyyykkyyyyy",
    "skyyyyyyyyyy",
    "skyppykkkkkk",
    "skyppknnnnnn",
    "skyyyknnnnnn",
    "skyyyykkkkkk",
    "sskyyyykNNNN",
    "sskyyyyykkkk",
    ".sskyyyyyyyy",
    ".ssskkyyyyyy",
    "..ssssskkkyy",
    "....sssssskk",
    "......ssssss",
]


def build():
    assert len(HALF) == 24 and all(len(line) == 12 for line in HALF)
    return [line + line[::-1] for line in HALF]


def main():
    write_sheet(OUT, [[build()]], LEGEND, scale=2)
    print("wrote %s (%d bytes)" % (os.path.relpath(OUT, ROOT), os.path.getsize(OUT)))


if __name__ == "__main__":
    main()
