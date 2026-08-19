"""Plugin skill layout: Codex/OpenAI do not follow symlinks into skills/kata/."""

from __future__ import annotations

import filecmp
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_SKILL = ROOT / "skills" / "kata"


class PluginSkillLayoutTest(unittest.TestCase):
    def test_plugin_skill_files_are_real_copies(self) -> None:
        canonical_files = [
            ROOT / "SKILL.md",
            ROOT / "scripts" / "runner.py",
            ROOT / "scripts" / "progress.py",
            *(p for p in (ROOT / "assets").rglob("*") if p.is_file() and not p.name.startswith(".")),
            *(p for p in (ROOT / "agents").rglob("*") if p.is_file() and not p.name.startswith(".")),
            *(p for p in (ROOT / "references").rglob("*") if p.is_file() and not p.name.startswith(".")),
        ]
        self.assertGreater(len(canonical_files), 10)
        for canonical in canonical_files:
            rel = canonical.relative_to(ROOT)
            packed = PLUGIN_SKILL / rel
            with self.subTest(packed=str(rel)):
                self.assertTrue(packed.is_file(), f"missing {packed}; run scripts/sync-plugin-skill.sh")
                self.assertFalse(packed.is_symlink(), f"symlink would be dropped: {packed}")
                self.assertTrue(
                    filecmp.cmp(canonical, packed, shallow=False),
                    f"{packed} drifted from {canonical}; run scripts/sync-plugin-skill.sh",
                )


class PluginListingLimitsTest(unittest.TestCase):
    def test_codex_interface_fits_openai_directory_limits(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        interface = manifest["interface"]
        self.assertLessEqual(len(interface["displayName"]), 30)
        self.assertLessEqual(len(interface["shortDescription"]), 30)
        self.assertEqual(interface["shortDescription"].count("\n"), 0)
        self.assertLessEqual(len(interface["longDescription"]), 4000)
        self.assertEqual(manifest["author"]["name"], interface["developerName"])
        self.assertLessEqual(len(interface["defaultPrompt"]), 3)
        for prompt in interface["defaultPrompt"]:
            self.assertLessEqual(len(prompt), 128)
            self.assertNotIn("@", prompt)

    def test_openai_yaml_short_description_fits_limit(self) -> None:
        text = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        lines = [line for line in text.splitlines() if line.startswith("  short_description:")]
        self.assertEqual(len(lines), 1)
        value = lines[0].split(":", 1)[1].strip()
        self.assertLessEqual(len(value), 30)

    def test_openai_yaml_policy_only_allows_implicit_invocation(self) -> None:
        """Directory scanner: policy may contain only allow_implicit_invocation."""
        text = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        policy_lines = []
        in_policy = False
        for line in text.splitlines():
            if line.startswith("policy:"):
                in_policy = True
                continue
            if in_policy and line and not line.startswith(" "):
                break
            if in_policy:
                policy_lines.append(line)
        keys = [line.split(":", 1)[0].strip() for line in policy_lines if line.strip()]
        self.assertEqual(keys, ["allow_implicit_invocation"])
        self.assertIn("allow_implicit_invocation: false", text)


if __name__ == "__main__":
    unittest.main()
