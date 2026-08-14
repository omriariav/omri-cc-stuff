#!/usr/bin/env python3
"""Validate plugin release metadata and emit a canonical release tag."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = re.compile(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?")
SEMVER = re.compile(
    r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
NATIVE_MANIFESTS = (
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    ".grok-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
)


class ReleaseError(ValueError):
    """A release invariant is not satisfied."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ReleaseError(f"missing manifest: {path.relative_to(ROOT)}") from error
    except json.JSONDecodeError as error:
        raise ReleaseError(f"invalid JSON in {path.relative_to(ROOT)}: {error}") from error
    if not isinstance(payload, dict):
        raise ReleaseError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def marketplace_entries() -> list[dict[str, Any]]:
    marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    entries = marketplace.get("plugins")
    if not isinstance(entries, list) or not all(isinstance(item, dict) for item in entries):
        raise ReleaseError(".claude-plugin/marketplace.json must contain a plugins array")
    return entries


def validate_plugin(plugin: str, entries: list[dict[str, Any]]) -> tuple[str, str]:
    if PLUGIN_NAME.fullmatch(plugin) is None:
        raise ReleaseError(f"invalid plugin name: {plugin!r}")

    expected_source = f"./plugins/{plugin}"
    matches = [
        entry
        for entry in entries
        if entry.get("name") == plugin or entry.get("source") == expected_source
    ]
    if len(matches) != 1:
        raise ReleaseError(
            f"{plugin}: expected exactly one marketplace entry for {expected_source}"
        )
    if matches[0].get("name") != plugin or matches[0].get("source") != expected_source:
        raise ReleaseError(f"{plugin}: marketplace name and source do not match")

    plugin_root = ROOT / "plugins" / plugin
    source = load_json(plugin_root / NATIVE_MANIFESTS[0])
    if source.get("name") != plugin:
        raise ReleaseError(f"{plugin}: Claude manifest name does not match directory")
    version = source.get("version")
    if not isinstance(version, str) or SEMVER.fullmatch(version) is None:
        raise ReleaseError(f"{plugin}: version must be valid semantic versioning")

    for relative_path in NATIVE_MANIFESTS[1:]:
        manifest = load_json(plugin_root / relative_path)
        if manifest.get("name") != plugin:
            raise ReleaseError(f"{plugin}: {relative_path} has a different name")
        if manifest.get("version") != version:
            raise ReleaseError(f"{plugin}: {relative_path} has a different version")

    return version, f"{plugin}-v{version}"


def write_github_output(path: Path, *, plugin: str, version: str, tag: str) -> None:
    with path.open("a", encoding="utf-8") as output:
        output.write(f"plugin={plugin}\nversion={version}\ntag={tag}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--plugin", help="Plugin name to prepare for release")
    selection.add_argument(
        "--check-all", action="store_true", help="Validate every marketplace plugin"
    )
    parser.add_argument(
        "--github-output",
        type=Path,
        help="Append plugin, version, and tag values to a GitHub Actions output file",
    )
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> int:
    global ROOT
    args = parse_args()
    ROOT = args.root.resolve()
    entries = marketplace_entries()
    if args.check_all:
        names = [entry.get("name") for entry in entries]
        for name in names:
            if not isinstance(name, str):
                raise ReleaseError("marketplace plugin names must be strings")
        if len(names) != len(set(names)):
            raise ReleaseError("marketplace plugin names must be unique")
        for name in names:
            version, tag = validate_plugin(name, entries)
            print(f"{name}: {version} ({tag})")
        return 0

    version, tag = validate_plugin(args.plugin, entries)
    print(tag)
    if args.github_output is not None:
        write_github_output(
            args.github_output, plugin=args.plugin, version=version, tag=tag
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReleaseError as error:
        raise SystemExit(f"release validation failed: {error}") from error
