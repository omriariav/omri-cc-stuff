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


def run_git(root: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
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
        run_git(root, "init", "--quiet")
        run_git(root, "config", "user.name", "Release Test")
        run_git(root, "config", "user.email", "release-test@example.com")
        run_git(root, "config", "commit.gpgSign", "false")
        run_git(root, "config", "tag.gpgSign", "false")
        run_git(root, "add", ".")
        run_git(root, "commit", "--quiet", "-m", "fixture")
        for tag in (
            "future-plugin-v1.2.0",
            "future-plugin-v1.2.3-rc.1",
            "future-plugin-v1.3.0-rc.1",
            "future-plugin-v1.3.0",
            "future-plugin-vnot-semver",
        ):
            run_git(root, "tag", tag)

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
            "previous_tag=future-plugin-v1.2.3-rc.1\n"
            "prerelease=false\n"
        )

        prerelease_manifest = dict(manifest, version="1.3.0-rc.2")
        for relative_path in NATIVE_MANIFESTS:
            write_json(plugin_root / relative_path, prerelease_manifest)
        prerelease_output = root / "prerelease-output.txt"
        prerelease = run_helper(
            root,
            "--plugin",
            plugin,
            "--github-output",
            str(prerelease_output),
        )
        assert prerelease.returncode == 0, prerelease.stdout + prerelease.stderr
        assert "previous_tag=future-plugin-v1.3.0-rc.1\n" in prerelease_output.read_text(
            encoding="utf-8"
        )
        assert "prerelease=true\n" in prerelease_output.read_text(encoding="utf-8")

        backport_manifest = dict(manifest, version="1.2.2")
        for relative_path in NATIVE_MANIFESTS:
            write_json(plugin_root / relative_path, backport_manifest)
        backport_output = root / "backport-output.txt"
        backport = run_helper(
            root,
            "--plugin",
            plugin,
            "--github-output",
            str(backport_output),
        )
        assert backport.returncode == 0, backport.stdout + backport.stderr
        assert "previous_tag=future-plugin-v1.2.0\n" in backport_output.read_text(
            encoding="utf-8"
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
