"""Tiny pixel-art PNG writer for the Tiny Touch badge app (no Pillow needed).

Draw sprites as lists of strings, one character per pixel, and map each
character to an RGBA colour in a legend. ``.`` is always transparent.

    from pixelart import write_sheet
    DUCK = [
        "..yy..",
        ".yyyy.",
        ...
    ]
    write_sheet("badge/apps/tiny_touch/assets/animals.png",
                [[DUCK, DUCK_BLINK]], LEGEND, scale=2)

``write_sheet`` takes rows of frames (``frames[row][column]``); every frame
must have the same width and height. Each pixel is scaled up by ``scale``. The
result is an indexed (paletted) PNG with a tRNS chunk, which the badge loads
efficiently with ``image.load(path).spritesheet(columns, rows)``.
"""

import struct
import zlib

TRANSPARENT = (0, 0, 0, 0)


def _chunk(kind, data):
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def write_indexed_png(path, width, height, indices, palette):
    """Write an 8-bit indexed PNG. ``palette`` is a list of (r, g, b, a)."""
    if len(palette) > 256:
        raise ValueError("palette has more than 256 colours")
    if len(indices) != width * height:
        raise ValueError("pixel count does not match size")
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter: none
        raw.extend(indices[y * width:(y + 1) * width])
    plte = b"".join(bytes(c[:3]) for c in palette)
    alphas = bytes(c[3] for c in palette)
    # tRNS may stop after the last non-opaque entry.
    last = max((i for i, a in enumerate(alphas) if a != 255), default=-1)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 3, 0, 0, 0))
    png += _chunk(b"PLTE", plte)
    if last >= 0:
        png += _chunk(b"tRNS", alphas[:last + 1])
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as handle:
        handle.write(png)


def _rgba(value):
    if len(value) == 3:
        return (value[0], value[1], value[2], 255)
    return tuple(value)


def write_sheet(path, frames, legend, scale=1):
    """Write a sprite sheet. ``frames`` is a list of rows of string-grid frames.

    Returns (frame_width, frame_height, columns, rows) in output pixels.
    """
    legend = {key: _rgba(val) for key, val in legend.items()}
    legend["."] = TRANSPARENT
    rows = len(frames)
    cols = len(frames[0])
    fh = len(frames[0][0])
    fw = len(frames[0][0][0])
    for r, row in enumerate(frames):
        if len(row) != cols:
            raise ValueError("row %d has %d frames, expected %d" % (r, len(row), cols))
        for c, frame in enumerate(row):
            if len(frame) != fh or any(len(line) != fw for line in frame):
                raise ValueError("frame (%d,%d) is not %dx%d" % (r, c, fw, fh))
            for line in frame:
                for ch in line:
                    if ch not in legend:
                        raise ValueError("frame (%d,%d) uses %r, not in legend" % (r, c, ch))

    palette = [TRANSPARENT]
    index_of = {TRANSPARENT: 0}
    for colour in legend.values():
        if colour not in index_of:
            index_of[colour] = len(palette)
            palette.append(colour)

    width = cols * fw * scale
    height = rows * fh * scale
    indices = bytearray(width * height)
    for r, row in enumerate(frames):
        for c, frame in enumerate(row):
            for y, line in enumerate(frame):
                for x, ch in enumerate(line):
                    idx = index_of[legend[ch]]
                    if not idx:
                        continue
                    ox = (c * fw + x) * scale
                    oy = (r * fh + y) * scale
                    for sy in range(scale):
                        start = (oy + sy) * width + ox
                        indices[start:start + scale] = bytes([idx]) * scale
    write_indexed_png(path, width, height, indices, palette)
    return fw * scale, fh * scale, cols, rows
