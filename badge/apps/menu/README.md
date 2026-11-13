# Menu

The badge's home screen: a launcher that lists every installed app and starts the one you pick.

## Usage

Use the LEFT, RIGHT, UP, and DOWN buttons to move between app icons and SELECT to launch the highlighted app. Apps appear automatically when they contain an `__init__.py` and a 24x24 `icon.png`.

## Customisation

- `SHOW_ACHIEVEMENTS` at the top of `app.py` is `False` in this fork: the built-in "Mona's Expedition" tile, IR checkpoint detection and the celebration are off. Set it to `True` to restore them. An existing `/state/achievements.json` is left untouched.
- `tiny_touch` is first in `APP_ORDER`, so Tiny Touch is the first tile and is selected when the menu opens.
