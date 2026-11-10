"""Keep this Claude Code skill in step with the Copilot copy in .github/skills."""

from __future__ import annotations

import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
COPILOT = PACKAGE.parents[2] / ".github" / "skills" / PACKAGE.name

# Files adapted for Claude Code. Everything else must match byte for byte.
ADAPTED = {
    "SKILL.md",
    "README.md",
    "INSTALL.txt",
    "TEST.md",
    "references/simulator.md",
    "scripts/install_skill.py",
    "scripts/skill_paths.py",
    "tests/test_workflows.py",
    "tests/test_copilot_sync.py",
}
IGNORED_PARTS = {"__pycache__", ".DS_Store"}


def shared_files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and not IGNORED_PARTS.intersection(path.parts)
        and path.suffix != ".pyc"
        and path.name != ".personal-install"
    }


@unittest.skipUnless(COPILOT.is_dir(), "Copilot copy of the skill is not present")
class CopilotSyncTests(unittest.TestCase):
    def test_same_file_set(self):
        self.assertEqual(
            shared_files(PACKAGE) - ADAPTED, shared_files(COPILOT) - ADAPTED
        )

    def test_shared_files_are_identical(self):
        for name in sorted(shared_files(PACKAGE) - ADAPTED):
            with self.subTest(file=name):
                self.assertEqual(
                    (PACKAGE / name).read_bytes(),
                    (COPILOT / name).read_bytes(),
                    f"{name} differs from {COPILOT / name}; copy the change across.",
                )


if __name__ == "__main__":
    unittest.main()
