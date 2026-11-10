# Building badge apps with Claude

This guide shows how to use [Claude Code](https://code.claude.com/docs) to
design, build, test, and install apps on the **GitHub Universe 2026 badge**.
You describe what you want and Claude writes the app, checks it, and puts it on
your badge. You don't need to know MicroPython first.

Claude does this with the **hyb26-skill** project skill in
[`.claude/skills/hyb26-skill/`](../.claude/skills/hyb26-skill/SKILL.md) and the
project instructions in [`CLAUDE.md`](../CLAUDE.md). Both load automatically
when you run Claude Code in this repository.

- [What you need](#what-you-need)
- [Set up](#set-up)
- [Your first app in five minutes](#your-first-app-in-five-minutes)
- [The workflow, step by step](#the-workflow-step-by-step)
- [Writing good prompts](#writing-good-prompts)
- [Example prompts](#example-prompts)
- [Testing without a badge](#testing-without-a-badge)
- [Debugging a crash](#debugging-a-crash)
- [Using the skill outside this repository](#using-the-skill-outside-this-repository)
- [Submitting your app](#submitting-your-app)
- [Troubleshooting](#troubleshooting)
- [How the pieces fit together](#how-the-pieces-fit-together)

## What you need

| Item | Why |
| --- | --- |
| [Claude Code](https://code.claude.com/docs/en/setup) on your computer (CLI, desktop app, or VS Code / JetBrains extension) | Runs the skill and its scripts. Use a **local** session: a cloud session (claude.ai/code) can write and validate apps but cannot reach a USB badge. |
| Python 3.10 or newer | Runs the skill's tools. Check with `python3 --version` (Windows: `python --version`). |
| [`mpremote`](https://docs.micropython.org/en/latest/reference/mpremote.html) | Talks to the badge over USB serial. `python3 -m pip install mpremote` (use a virtual environment if your system Python refuses). |
| A Universe 2026 badge and a **data-capable** USB-C cable | For installing and real testing. Charge-only cables are the most common cause of "badge not found". |
| A clone of this repository | `git clone https://github.com/badger/home.git` (or your fork). |

## Set up

```bash
git clone https://github.com/badger/home.git
cd home
python3 -m pip install mpremote
claude
```

Inside Claude Code, check the skill is available:

```text
/skills
```

You should see `hyb26-skill`. Plug in the badge and ask:

```text
Is my badge connected? Show me its firmware and installed apps.
```

Claude runs `badge_serial.py info`, which finds the badge (USB `2e8a:1101`),
lists its apps, and reports whether its menu can show custom app icons.

## Your first app in five minutes

Type:

```text
Make a badge app called dice. SELECT rolls two dice with a short shake
animation, and it shows the total. Install it on my badge.
```

Claude will:

1. **Plan** the screens, controls, and assets, and ask only about things that
   would change the app a lot.
2. **Scaffold** `badge/apps/dice/` with `__init__.py`, a 24x24+ `icon.png`, and
   a `README.md` (`scaffold_app.py`).
3. **Write the app** using the 2026 firmware API (`badge`, `screen`, `color`,
   `run(update)`, and friends).
4. **Validate** it (`validate_app.py badge/apps/dice`) and fix any problems.
5. **Switch the badge into USB Disk Mode** (`badge_serial.py disk-mode`) so the
   `BADGER` drive appears.
6. **Preview, then copy** the app (`deploy_app.py badge/apps/dice`, then
   `--write` once you agree). It also patches the menu so your icon shows if the
   badge needs it (`patch_menu_icons.py`).
7. **Eject** the drive (`badge_serial.py eject`); the badge restarts to the
   menu.
8. Give you a **checklist** to try on the badge, and say which checks it ran
   and which still need you.

Pick **Dice** from the badge menu and try it.

## The workflow, step by step

You can run any step yourself or just ask Claude. The commands below are run
from the repository root.

```bash
scripts=.claude/skills/hyb26-skill/scripts
```

On Windows PowerShell use `$scripts = ".claude\skills\hyb26-skill\scripts"`
and `python` instead of `python3`.

### 1. Describe the idea

Tell Claude what the app does, its controls, and anything it should remember.
See [Writing good prompts](#writing-good-prompts).

### 2. Scaffold

```bash
python3 $scripts/scaffold_app.py my_app --title "My App" \
  --description "My App shows a friendly greeting."
```

This creates:

```text
badge/apps/my_app/
├── __init__.py   # update() + run(update)
├── icon.png      # replace with your own square PNG (48x48 looks sharpest)
└── README.md     # first sentence describes the app
```

It never overwrites an existing app.

### 3. Build

Claude follows [`badge/AGENTS.md`](../badge/AGENTS.md). The key rules:

- Use the runtime **globals** (`badge`, `screen`, `image`, `font`, `color`,
  `shape`, `brush`, `vec2`, `rect`, `mat3`, `run`, `BUTTON_*`, `HIRES`). Don't
  `import badge`. Import `State` from `badgeware` for saved data.
- Define `update()` and call `run(update)` at module level.
- Read buttons with `badge.pressed()`, `held()`, `released()`, `touched()`
  using logical buttons (`BUTTON_UP/DOWN/LEFT/RIGHT/SELECT/BACK/MENU`). HOME
  belongs to the launcher.
- Move things with `badge.ticks_delta` so speed doesn't depend on frame rate.
- Use `screen.width` / `screen.height` (160x120 default, 320x240 with
  `badge.mode(HIRES | VSYNC)`).
- `os.chdir("/system/apps/<name>")` and keep asset paths relative.
- **Never** use the 2025 API in `badge25/`.

### 4. Validate

```bash
python3 $scripts/validate_app.py badge/apps/my_app
python3 .github/scripts/validate_app_readmes.py badge/apps   # same check as CI
```

Static checks find syntax errors, 2025 APIs, missing files, a bad icon, and
README problems. They do **not** prove the app runs on a badge.

### 5. Install on the badge

```bash
python3 $scripts/badge_serial.py info          # find the badge, check menu icon support
python3 $scripts/badge_serial.py disk-mode     # reboot into USB Disk Mode (BADGER drive)
python3 $scripts/patch_menu_icons.py           # preview; add --write if the menu needs it
python3 $scripts/deploy_app.py badge/apps/my_app           # dry run
python3 $scripts/deploy_app.py badge/apps/my_app --write   # copy
python3 $scripts/badge_serial.py eject         # flush, eject, wait for the badge to restart
```

Updating an app you've installed before needs `--replace`; the old copy is
kept in `.badge-app-backups` on the drive. `secrets.py` is never copied.

Claude shows you the dry-run output and asks before anything is written to
your badge, unless you already asked it to install.

### 6. Test on the badge

Open the app from the menu and go through Claude's checklist: every screen and
button, HOME and reopening, saved data after a restart, and error cases (for
example Wi-Fi off). Check the menu tile shows your icon, not the default one.
Tell Claude what you see; it will fix and redeploy.

## Writing good prompts

Good prompts cover:

- **Screens and states**: "a title screen, the game, and a game-over screen".
- **Controls**: "LEFT/RIGHT moves, SELECT jumps, BACK pauses".
- **What to remember**: "save the high score".
- **Resolution and look**: "HIRES, dark background, big numbers".
- **Hardware or network**: "uses the accelerometer", "fetches a JSON URL over
  Wi-Fi (credentials are in secrets.py)".
- **How far to go**: "install it on my badge" or "don't touch my badge yet".

Say **"use hyb26-skill"** or type `/hyb26-skill` if Claude doesn't pick it up
on its own.

## Example prompts

**A new game**

```text
Build a badge game where Mona catches falling stars. LEFT/RIGHT moves, stars
speed up over time, three misses ends the game, and the high score is saved.
Use the flappy_mona app as a style reference. Install it when it validates.
```

**Use a sensor**

```text
Make a spirit-level app using the badge's IMU. Show a bubble that moves with
tilt and turns green when the badge is level.
```

**Network app**

```text
Make an app that shows a JSON status from https://example.com/status.json,
refreshes every minute, caches the last result, and still shows something
useful when Wi-Fi is off. Credentials come from secrets.py; don't touch it.
```

**Improve an existing app**

```text
Add a pause screen on BACK and a saved high score to badge/apps/snake. Keep the
existing controls.
```

**Port a 2025 app**

```text
Port badge25/apps/<name> to the 2026 badge. Keep the behavior and assets, but
translate graphics, input, timing, and state to the 2026 API.
```

**Badge housekeeping**

```text
What apps are on my badge and how much free space is left?
Put my badge into USB Disk Mode.
My app has an icon.png but the badge menu shows a generic icon. Fix it.
```

## Testing without a badge

1. **Static checks** with `validate_app.py` (add `--target emulator` for
   simulator warnings).
2. **Browser simulator** at <https://badger.github.io/editor>: paste your
   app's `__init__.py` (and assets) to see layout and logic. It doesn't run
   sockets, Bluetooth, IR, the camera, or `.mpy` files, and speed and memory
   differ from the real badge. If you have a browser tool connected to Claude
   (for example Claude in Chrome), Claude can drive the editor for you.

The **Badge Simulator canvas** in `.github/extensions/badge-simulator/` is a
GitHub Copilot app extension and doesn't run in Claude Code.

Without a badge, Claude will give you a hardware test checklist and say
physical testing is still to do. An app isn't done until it has run on a
badge.

## Debugging a crash

1. Ask Claude: *"My app crashes when I press SELECT. Here's what I see: ..."*
2. To get the traceback, attach to the badge **in your own terminal** without
   resetting it, then open the app from the menu:

   ```bash
   mpremote connect <port> resume repl     # Ctrl-] to exit
   ```

   Paste the traceback to Claude. (Claude doesn't open interactive REPLs
   itself; it uses one-shot `mpremote exec` / `eval` to probe the badge.)
3. Claude fixes the code, re-validates, and redeploys with `--replace`.

Only one program can use the badge's serial port at a time. Close Thonny, Web
Serial tabs, `screen`, or other `mpremote` sessions before asking Claude to
talk to the badge.

## Using the skill outside this repository

To build badge apps in any folder (Git optional), install the skill for your
user:

```bash
sh .claude/skills/hyb26-skill/install-skill.sh        # macOS / Linux
```

```powershell
.\.claude\skills\hyb26-skill\install-skill.ps1        # Windows PowerShell
```

It's copied to `~/.claude/skills/hyb26-skill`. Rerun to update. Then:

```bash
mkdir "Badge Projects" && cd "Badge Projects"
claude
```

```text
Use hyb26-skill to make a counter app in this folder.
```

Apps are created under `badge/apps/` in the folder you started Claude in. Run
Claude from your project folder, not from your home folder or the skill folder.

## Submitting your app

1. Make sure `README.md` starts with a one-sentence description (10-200
   characters, ending in punctuation), then usage and any hardware, Wi-Fi, or
   `secrets.py` needs. Add a screenshot if you can.
2. Run `python3 .github/scripts/validate_app_readmes.py badge/apps`.
3. Check `badge/secrets.py` is still empty: `git diff badge/secrets.py`.
4. Ask Claude to commit on a branch and open a pull request, or do it yourself.
   Follow [CONTRIBUTING.md](../CONTRIBUTING.md) and the pull request template.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `/skills` doesn't list `hyb26-skill` | Start Claude Code from the repository root (or install the skill personally) and restart it. |
| "No badge found" | Use a data USB-C cable, run `mpremote devs`, and close other serial programs. |
| `OSError: 30` / `EROFS` when copying | `/system` is read-only over serial. Use USB Disk Mode (`badge_serial.py disk-mode`). |
| `BADGER` drive doesn't appear | Open the **Mass Storage** app on the badge, or double-tap RESET. Never copy apps to the `RP2350` drive (that's the bootloader). |
| Windows says "error occurred while ejecting" | Harmless: the badge reboots as soon as it gets the eject request. |
| Menu shows a generic icon | Run `patch_menu_icons.py` (preview, then `--write`) in USB Disk Mode. Apps named like a built-in app keep the built-in icon. |
| `deploy_app.py` refuses to copy | The app already exists; add `--replace` (a backup is kept). |
| App works in the simulator but not on the badge | Expected for sockets, Bluetooth, IR, timing, and memory. Debug on the badge. |
| Claude uses `from badgeware import screen, PixelFont ...` | That's the 2025 API. Remind it: "use the 2026 API from badge/AGENTS.md". |

## How the pieces fit together

| Path | What it is |
| --- | --- |
| [`CLAUDE.md`](../CLAUDE.md) | Project instructions Claude Code always loads in this repository. |
| [`.claude/skills/hyb26-skill/SKILL.md`](../.claude/skills/hyb26-skill/SKILL.md) | The skill: workflow, rules, and when to use each tool. |
| `.claude/skills/hyb26-skill/references/` | Detailed references Claude reads when needed (API, app contract, USB serial, menu icons, simulator, hardware). |
| `.claude/skills/hyb26-skill/scripts/` | Scaffold, validate, serial, deploy, menu-patch, and inventory tools. |
| `.claude/skills/hyb26-skill/tests/` | Unit tests for the tools (`python3 -m unittest discover -s tests -v`). |
| [`badge/AGENTS.md`](../badge/AGENTS.md) | The 2026 app API and rules. |
| [`hardware/USB_SERIAL.md`](../hardware/USB_SERIAL.md) | Tested `mpremote`, REPL, and install procedures. |
| `.github/copilot-instructions.md`, `.github/skills/hyb26-skill/` | The GitHub Copilot versions of the same instructions and skill. |

The Claude and Copilot skills share the same scripts and references; a test
(`tests/test_copilot_sync.py`) fails if they drift apart.
