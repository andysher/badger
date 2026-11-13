# Tiny Touch

Tiny Touch is a gentle touch-and-tilt playground for toddlers with color splashes, peekaboo animals, and tumbling shapes.

## Activities

- **Color Splash**: every touch pad paints its own bright color with a splash
  of bubbles, and the case lights glow. Shake the badge for rainbow confetti.
  Name the colors together: "Blue! Red!"
- **Peekaboo Animals**: touch to open the curtains and meet a friendly animal.
  Grown-ups say the name and make the sound ("Moo!"); touch again for a happy
  wiggle, then the curtains close for the next animal.
- **Tilt & Tumble**: big shapes with happy faces roll the way the badge tilts.
  Shake to scatter them; touch to make one hop. Name the shapes together.

There is no text to read, nothing to win or lose, and every touch gets an
instant, cheerful reaction.

## For grown-ups

- **Switch activity**: hold **BACK** and **MENU** together for 1.5 seconds. A
  small ring fills in the top-right corner, then the next activity starts. The
  app remembers the last activity.
- **HOME** returns to the badge menu. Toddlers may touch it by accident; just
  open Tiny Touch again.
- The badge has no speaker, so you provide the sounds.
- Always supervise play: the badge is small, has a battery, and the lanyard is
  not a toy.

## Hardware

Uses the touch pads, the motion sensor (tilt and shake), and the four case
lights. No Wi-Fi or `secrets.py` needed. Tilt and shake need a physical badge;
in the browser simulator the shapes just settle to the bottom.

Pixel-art sprites are generated from `tools/tiny_touch/` (pure Python, no
Pillow): `python3 tools/tiny_touch/make_animals.py`, `make_shapes.py`,
`make_icon.py`.
