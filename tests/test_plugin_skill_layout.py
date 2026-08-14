"""Plugin skill layout: Codex/OpenAI do not follow symlinks into skills/kata/."""

from __future__ import annotations

import filecmp
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_SKILL = ROOT / "skills" / "kata"


class PluginSkillLayoutTest(unittest.TestCase):
    def test_plugin_skill_files_are_real_copies(self) -> None:
        pairs = [
            (ROOT / "SKILL.md", PLUGIN_SKILL / "SKILL.md"),
            (ROOT / "scripts" / "runner.py", PLUGIN_SKILL / "scripts" / "runner.py"),
            (ROOT / "scripts" / "progress.py", PLUGIN_SKILL / "scripts" / "progress.py"),
            (ROOT / "assets" / "icon.svg", PLUGIN_SKILL / "assets" / "icon.svg"),
            (ROOT / "assets" / "icon.png", PLUGIN_SKILL / "assets" / "icon.png"),
            (ROOT / "assets" / "logo.png", PLUGIN_SKILL / "assets" / "logo.png"),
            (ROOT / "agents" / "openai.yaml", PLUGIN_SKILL / "agents" / "openai.yaml"),
            (
                ROOT / "references" / "session-protocol.md",
                PLUGIN_SKILL / "references" / "session-protocol.md",
            ),
        ]
        for canonical, packed in pairs:
            with self.subTest(packed=str(packed.relative_to(ROOT))):
                self.assertTrue(packed.is_file(), f"missing {packed}")
                self.assertFalse(packed.is_symlink(), f"symlink would be dropped: {packed}")
                self.assertTrue(
                    filecmp.cmp(canonical, packed, shallow=False),
                    f"{packed} drifted from {canonical}; run scripts/sync-plugin-skill.sh",
                )


if __name__ == "__main__":
    unittest.main()
