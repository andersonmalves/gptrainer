#!/usr/bin/env bash
# Copy canonical skill files into skills/kata/ as real files.
# Codex plugin cache and the OpenAI plugin ZIP do not follow symlinks.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
dest="$root/skills/kata"

rm -f "$dest/SKILL.md"
rm -rf "$dest/references" "$dest/scripts" "$dest/assets"
rm -f "$dest/agents/openai.yaml"

mkdir -p "$dest/agents" "$dest/scripts" "$dest/assets"

cp "$root/SKILL.md" "$dest/SKILL.md"
cp -R "$root/references" "$dest/references"
cp "$root/scripts/runner.py" "$root/scripts/progress.py" "$dest/scripts/"
cp "$root/assets/icon.svg" "$dest/assets/"
cp "$root/agents/openai.yaml" "$dest/agents/openai.yaml"
