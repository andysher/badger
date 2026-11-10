# Claude Code instructions for GitHub Universe badge development

This file is the Claude Code counterpart of `.github/copilot-instructions.md`.
Keep the two aligned.

The repository targets the **GitHub Universe 2026 badge** by default.

- Work in `badge/` for current firmware and applications.
- Read `badge/AGENTS.md` before changing a 2026 app.
- Read `hardware/README.md` before using raw GPIO, I2C, ADC, IR, power,
  wireless, display, touch, switch, or interrupt hardware.
- Read `hardware/USB_SERIAL.md` before communicating with a connected badge or
  modifying its filesystem.
- `badge25/` is the preserved Universe 2025 source tree. Read
  `badge25/AGENTS.md` only when intentionally maintaining that badge.
- `badge25/simulator/` and `badge25/badgerware/` document the legacy 2025
  runtime and must not be treated as authoritative for 2026 apps.

## Skill

Use the project skill `.claude/skills/hyb26-skill` (`/hyb26-skill`) for any
request to create, change, port, validate, debug, or deploy a badge app, or to
talk to a connected badge. Its scripts handle scaffolding
(`scaffold_app.py`), static checks (`validate_app.py`), serial and USB Disk
Mode (`badge_serial.py`), safe deployment (`deploy_app.py`), and the menu icon
patch (`patch_menu_icons.py`). The guide for people building apps with Claude
is `docs/building-apps-with-claude.md`.

## Universe 2026 essentials

- The RP2350B firmware supplies `badge`, `screen`, `image`, `font`, `color`,
  `shape`, `brush`, `vec2`, `rect`, `mat3`, `run`, button constants, display
  mode constants, and filesystem helpers as globals. Do not `import badge`.
- Prefer orientation-aware logical actions such as `BUTTON_SELECT`,
  `BUTTON_LEFT`, and `BUTTON_RIGHT`.
- Read input with `badge.pressed()`, `badge.held()`, `badge.released()`, and
  `badge.touched()`.
- Use `badge.ticks` and `badge.ticks_delta`; movement must be frame-rate
  independent.
- Draw with `screen.pen`, `color.rgb()`, `screen.shape()`, and
  `screen.blit()`.
- Load sprites with `image.load(path).spritesheet(columns, rows)`.
- Use `screen.width` and `screen.height`; HIRES mode is 320x240 and the common
  logical mode is 160x120.
- Keep `badge/secrets.py` empty in source control. Never read, print, copy, or
  commit a filled one.
- New apps need `badge/apps/<name>/__init__.py`, a 24x24 (48x48 looks
  sharper) `icon.png`, and a `README.md` whose first paragraph is a
  one-sentence description of the app (followed by usage and any hardware or
  network requirements). The `Validate app READMEs` check fails pull requests
  without one: `python3 .github/scripts/validate_app_readmes.py badge/apps`.

## Working with a connected badge

- Use `mpremote devs` to discover a connected badge, then explicit
  `mpremote connect <port> ...` commands.
- Only one process can own the USB serial port. Run serial commands one at a
  time: never in parallel tool calls and never in the background.
- `mpremote ... repl` is interactive; do not start it from a tool call. Use
  `exec`, `eval`, or `run`, and ask the user to open the REPL in their own
  terminal when a live session is needed.
- Remote filesystem paths in `mpremote fs` commands begin with `:`. The normal
  REPL mounts `/system` read-only; use a host mount for transient tests or USB
  mass-storage mode to deploy under `/system/apps/`. Inspect state under
  `:/state/`.
- Install apps by following "Installing an app" (including "Menu icon patch")
  in `hardware/USB_SERIAL.md`: always use USB mass-storage mode for
  `/system/apps/<app>`, preview `deploy_app.py` / `patch_menu_icons.py` before
  `--write`, and finish with `mpremote connect <port> reset` (or
  `badge_serial.py eject`) so the badge reboots to the menu.
- Writing to a badge changes the user's device. Show the dry-run output and
  confirm before `--write` unless the user already asked you to install.

## Testing

1. `validate_app.py badge/apps/<app>` for static checks.
2. Optional: the browser simulator at https://badger.github.io/editor. The
   Badge Simulator canvas in `.github/extensions/badge-simulator/` is a GitHub
   Copilot app extension and does not run in Claude Code.
3. A physical badge is the real test. Report which checks actually ran and
   never call an app hardware-verified because static checks passed.

When porting a 2025 app, preserve behavior and assets but explicitly translate
the graphics, input, timing, orientation, lifecycle, and state APIs. Use
`badge/apps/input_test/`, `badge/apps/demos/` and `badge/apps/flappy_mona/` as
primary references.
