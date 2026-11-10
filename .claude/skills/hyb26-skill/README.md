# HYB26-skill (Claude Code)

A [Claude Code skill](https://code.claude.com/docs/en/skills) for building,
testing, and installing apps on the GitHub Universe 2026 badge. It works on
macOS, Linux, and Windows.

This is the Claude Code version of the Copilot skill in
[`.github/skills/hyb26-skill`](../../../.github/skills/hyb26-skill/). The
scripts and references are the same; `SKILL.md`, the installer, and these docs
are adapted for Claude Code. The step-by-step guide for app authors is
[docs/building-apps-with-claude.md](../../../docs/building-apps-with-claude.md).

## What it helps with

- Turning an idea into an app under `badge/apps/<name>` with `__init__.py`,
  `icon.png`, and a `README.md` that passes the repository's README check.
- Using the 2026 firmware API, reference apps, and hardware notes from
  `badger/home`.
- Talking to the badge with `mpremote`: running code, reading files.
- Switching the badge into USB Disk Mode from the computer and copying one app
  safely (dry run first, backups on replace, `secrets.py` never copied).
- Patching a stock badge menu so apps show their own `icon.png`
  ([Gadgetoid's patch](https://gist.github.com/Gadgetoid/f72b85e6efe603bd02b2b730bbc40356)).
- Quick checks in the [badger.github.io simulator](https://badger.github.io/editor),
  followed by testing on a real badge.

## Use it in this repository

Claude Code discovers project skills in `.claude/skills/` automatically and
loads this one whenever a request is about badge apps. Start `claude` in a
`badger/home` checkout and ask, for example:

> Make a dice app for my badge and install it.

You can also invoke it directly with `/hyb26-skill`.

## Install it for your own projects

Requires Python 3.10+. From this folder:

```bash
sh ./install-skill.sh            # macOS / Linux
```

```powershell
.\install-skill.ps1              # Windows PowerShell
```

This copies the skill to `~/.claude/skills/hyb26-skill` (and writes a
`.personal-install` marker so the tools use your current folder as the
project) without deleting unrelated files there. Rerun it to update. In Claude
Code, type `/skills` to check it is listed. See [INSTALL.txt](INSTALL.txt).

## Tools

| Script | Purpose |
| --- | --- |
| `scaffold_app.py` | Create a starter app with icon and README |
| `validate_app.py` | Static checks: syntax, imports, lifecycle, assets, icon, README |
| `badge_serial.py` | Find the badge port, show info, open the REPL, enter USB Disk Mode |
| `deploy_app.py` | Copy one app to the BADGER volume (dry run by default) |
| `patch_menu_icons.py` | Let the badge menu show app `icon.png` files (dry run by default) |
| `inventory_badge_apps.py` | List readable app files on a mounted badge |

Commands for each host are in [SKILL.md](SKILL.md).

## Maintenance

Run `python3 -m unittest discover -s tests -v` from this folder after
changes. [TEST.md](TEST.md) lists prompts for checking Claude's behavior. Keep
`scripts/` and `references/` in sync with the Copilot copy in
`.github/skills/hyb26-skill/` (`tests/test_copilot_sync.py` lists the files
that intentionally differ and fails if anything else drifts), and keep both aligned with `badge/AGENTS.md` and
`hardware/USB_SERIAL.md`.
