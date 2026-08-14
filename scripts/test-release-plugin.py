#!/usr/bin/env python3
"""Integration checks for the plugin release metadata helper."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


RELEASE_HELPER = Path(__file__).with_name("release_plugin.py").resolve()
NATIVE_MANIFESTS = (
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    ".grok-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_helper(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RELEASE_HELPER), "--root", str(root), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root)
        plugin = "future-plugin"
        plugin_root = root / "plugins" / plugin
        write_json(
            root / ".claude-plugin" / "marketplace.json",
            {"plugins": [{"name": plugin, "source": f"./plugins/{plugin}"}]},
        )
        manifest = {
            "name": plugin,
            "version": "1.2.3",
            "description": "A future plugin.",
            "author": {"name": "Test Author"},
        }
        for relative_path in NATIVE_MANIFESTS:
            write_json(plugin_root / relative_path, manifest)

        check = run_helper(root, "--check-all")
        assert check.returncode == 0, check.stdout + check.stderr
        assert "future-plugin: 1.2.3 (future-plugin-v1.2.3)" in check.stdout

        output_path = root / "github-output.txt"
        release = run_helper(
            root,
            "--plugin",
            plugin,
            "--github-output",
            str(output_path),
        )
        assert release.returncode == 0, release.stdout + release.stderr
        assert release.stdout.strip() == "future-plugin-v1.2.3"
        assert output_path.read_text(encoding="utf-8") == (
            "plugin=future-plugin\n"
            "version=1.2.3\n"
            "tag=future-plugin-v1.2.3\n"
        )

        mismatched = dict(manifest, version="1.2.4")
        write_json(plugin_root / ".codex-plugin" / "plugin.json", mismatched)
        invalid = run_helper(root, "--plugin", plugin)
        assert invalid.returncode != 0
        assert ".codex-plugin/plugin.json has a different version" in invalid.stderr

        invalid_semver = dict(manifest, version="1.2.3-01")
        for relative_path in NATIVE_MANIFESTS:
            write_json(plugin_root / relative_path, invalid_semver)
        invalid = run_helper(root, "--plugin", plugin)
        assert invalid.returncode != 0
        assert "version must be valid semantic versioning" in invalid.stderr

    print("Release metadata integration tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
