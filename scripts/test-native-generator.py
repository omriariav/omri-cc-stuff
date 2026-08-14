#!/usr/bin/env python3
"""Integration checks for onboarding new plugin shapes."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


GENERATOR = Path(__file__).with_name("sync-native-manifests.py").resolve()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_plugin_manifest(root: Path, name: str, description: str) -> Path:
    plugin_root = root / "plugins" / name
    write_json(
        plugin_root / ".claude-plugin" / "plugin.json",
        {
            "name": name,
            "version": "1.0.0",
            "description": description,
            "author": {"name": "Test Author"},
        },
    )
    return plugin_root


def run_generator(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GENERATOR), "--root", str(root), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root)
        write_json(
            root / ".claude-plugin" / "plugin.json",
            {
                "name": "test-marketplace",
                "description": "Generator integration fixture.",
                "author": {"name": "Test Author"},
            },
        )
        write_json(
            root / ".claude-plugin" / "marketplace.json",
            {
                "name": "test-marketplace",
                "owner": {"name": "Test Author"},
                "plugins": [
                    {
                        "name": name,
                        "source": f"./plugins/{name}",
                        "category": "utilities",
                    }
                    for name in ("future-command", "future-hook", "future-mcp")
                ],
            },
        )

        command = write_plugin_manifest(
            root, "future-command", "A command-only future plugin."
        )
        command_file = command / "commands" / "run.md"
        command_file.parent.mkdir(parents=True)
        command_file.write_text(
            "---\n"
            "description: Run the future command.\n"
            "argument-hint: '[arguments]'\n"
            "---\n\n"
            "Run the requested future command.\n",
            encoding="utf-8",
        )

        hook = write_plugin_manifest(root, "future-hook", "A hook-based future plugin.")
        skill_file = hook / "skills" / "future-hook" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text(
            "---\nname: future-hook\ndescription: Exercise a future hook plugin.\n---\n",
            encoding="utf-8",
        )
        write_json(hook / "hooks" / "hooks.json", {"hooks": {"SessionStart": []}})

        mcp = write_plugin_manifest(root, "future-mcp", "An MCP-only future plugin.")
        write_json(mcp / ".mcp.json", {"mcpServers": {}})

        initial_check = run_generator(root, "--check")
        assert initial_check.returncode == 1, initial_check.stdout + initial_check.stderr
        assert "Traceback" not in initial_check.stderr, initial_check.stderr
        assert "Native manifests are out of sync" in initial_check.stderr
        assert "future-command/skills/future-command-run/SKILL.md" in initial_check.stderr

        generated = run_generator(root)
        assert generated.returncode == 0, generated.stdout + generated.stderr
        final_check = run_generator(root, "--check")
        assert final_check.returncode == 0, final_check.stdout + final_check.stderr

        command_codex = json.loads(
            (command / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        assert command_codex["skills"] == "./skills/"
        assert (command / "skills" / "future-command-run" / "SKILL.md").is_file()

        hook_cursor = json.loads(
            (hook / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        assert hook_cursor["hooks"] == "./.cursor-plugin/hooks.json"
        cursor_hooks_path = hook / ".cursor-plugin" / "hooks.json"
        assert cursor_hooks_path.is_file()

        custom_cursor_hooks = {
            "hooks": {"sessionStart": [{"command": "./scripts/cursor-start.sh"}]}
        }
        write_json(cursor_hooks_path, custom_cursor_hooks)
        regenerated = run_generator(root)
        assert regenerated.returncode == 0, regenerated.stdout + regenerated.stderr
        assert json.loads(cursor_hooks_path.read_text(encoding="utf-8")) == custom_cursor_hooks
        preserved_check = run_generator(root, "--check")
        assert preserved_check.returncode == 0, (
            preserved_check.stdout + preserved_check.stderr
        )

        mcp_codex = json.loads(
            (mcp / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        assert mcp_codex["mcpServers"] == "./.mcp.json"

        cursor_marketplace = json.loads(
            (root / ".cursor-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        command_entry = cursor_marketplace["plugins"][0]
        assert command_entry["description"] == "A command-only future plugin."
        assert command_entry["author"] == {"name": "Test Author"}

    print("Future-plugin generator integration tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
