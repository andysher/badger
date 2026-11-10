"""Install this complete skill for the current user without deleting local files."""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

PERSONAL_MARKER = ".personal-install"


def install(source: Path, home: Path) -> Path:
    source = source.resolve()
    text = (source / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
    name = (
        re.search(r"^name:\s*([a-z0-9-]+)\s*$", frontmatter[1], re.MULTILINE)
        if frontmatter else None
    )
    if name is None:
        raise ValueError(f"No valid skill name in {source / 'SKILL.md'}")
    destination = home / ".claude" / "skills" / name[1]
    if destination.is_symlink():
        raise ValueError(f"Refusing to overwrite a linked skill folder: {destination}")
    if destination.resolve() == source:
        return destination
    if destination.resolve().is_relative_to(source):
        raise ValueError("The installation destination must be outside the source folder.")
    shutil.copytree(
        source,
        destination,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store", "._*"),
    )
    (destination / PERSONAL_MARKER).write_text(
        "Personal Claude Code install of this skill; do not delete.\n", encoding="utf-8"
    )
    return destination


def main() -> int:
    if sys.version_info < (3, 10):
        print("error: Python 3.10 or newer is required.", file=sys.stderr)
        return 1
    try:
        destination = install(Path(__file__).resolve().parents[1], Path.home())
    except (OSError, ValueError, shutil.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Installed hyb26-skill to {destination}")
    print("Verify in Claude Code: type /skills (or ask 'What skills are available?').")
    print("Skills are picked up live; restart Claude Code if it does not appear.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
