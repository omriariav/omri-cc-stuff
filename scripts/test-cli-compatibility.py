#!/usr/bin/env python3
"""Smoke-test native marketplace support in the real agent CLIs."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PLUGIN = "copy"
MANIFESTS = {
    "codex": ROOT / ".agents" / "plugins" / "marketplace.json",
    "grok": ROOT / ".grok-plugin" / "marketplace.json",
    "cursor": ROOT / ".cursor-plugin" / "marketplace.json",
}


def run(
    arguments: list[str],
    *,
    env: dict[str, str],
    expect_success: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        arguments,
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if expect_success and result.returncode != 0:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(arguments)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def parsed_json(result: subprocess.CompletedProcess[str]) -> Any:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise AssertionError(f"CLI did not emit JSON:\n{result.stdout}") from error


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def plugin_names(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {entry["name"] for entry in payload["plugins"]}


def assert_catalog_matches(runtime: str) -> set[str]:
    canonical = plugin_names(ROOT / ".claude-plugin" / "marketplace.json")
    native = plugin_names(MANIFESTS[runtime])
    check(
        native == canonical,
        f"{runtime} marketplace entries differ from the canonical marketplace: "
        f"missing={sorted(canonical - native)}, extra={sorted(native - canonical)}",
    )
    check(FIXTURE_PLUGIN in native, f"Required fixture plugin is missing: {FIXTURE_PLUGIN}")
    return native


def smoke_codex(env: dict[str, str], expected_plugins: set[str]) -> None:
    codex_home = Path(env["HOME"]) / ".codex"
    codex_home.mkdir()
    env["CODEX_HOME"] = str(codex_home)

    added = parsed_json(
        run(["codex", "plugin", "marketplace", "add", str(ROOT), "--json"], env=env)
    )
    check(
        added["marketplaceName"] == "omri-marketplace",
        "Codex registered the marketplace under an unexpected name",
    )

    marketplaces = parsed_json(
        run(["codex", "plugin", "marketplace", "list", "--json"], env=env)
    )
    check(
        any(
            entry["name"] == "omri-marketplace"
            for entry in marketplaces["marketplaces"]
        ),
        "Codex did not list the registered marketplace",
    )

    available = parsed_json(
        run(
            [
                "codex",
                "plugin",
                "list",
                "--marketplace",
                "omri-marketplace",
                "--available",
                "--json",
            ],
            env=env,
        )
    )
    available_names = {entry["name"] for entry in available["available"]}
    check(
        available_names == expected_plugins,
        f"Codex listed unexpected plugins: {sorted(available_names)}",
    )

    installed_paths: dict[str, Path] = {}
    for plugin_name in sorted(expected_plugins):
        installed = parsed_json(
            run(
                [
                    "codex",
                    "plugin",
                    "add",
                    f"{plugin_name}@omri-marketplace",
                    "--json",
                ],
                env=env,
            )
        )
        installed_path = Path(installed["installedPath"])
        check(installed_path.is_dir(), f"Codex did not install {plugin_name}")
        installed_paths[plugin_name] = installed_path

    fixture_skill = (
        installed_paths[FIXTURE_PLUGIN]
        / "skills"
        / "copy-cleartext"
        / "SKILL.md"
    )
    check(fixture_skill.is_file(), "Codex did not install the fixture skill")

    listed = parsed_json(run(["codex", "plugin", "list", "--json"], env=env))
    installed_entries = {entry["name"]: entry for entry in listed["installed"]}
    check(
        set(installed_entries) == expected_plugins,
        f"Codex did not list every installed plugin: {sorted(installed_entries)}",
    )
    for plugin_name, entry in installed_entries.items():
        check(entry["installed"] is True, f"Codex did not install {plugin_name}")
        check(entry["enabled"] is True, f"Codex did not enable {plugin_name}")


def smoke_grok(env: dict[str, str], expected_plugins: set[str]) -> None:
    env["TERM"] = "xterm"
    run(["grok", "plugin", "marketplace", "add", str(ROOT)], env=env)

    marketplaces = parsed_json(
        run(["grok", "plugin", "marketplace", "list", "--json"], env=env)
    )
    check(
        any(
            Path(entry["source"]["path"]).resolve() == ROOT
            for entry in marketplaces
            if entry["kind"] == "local"
        ),
        "Grok did not list the registered local marketplace",
    )

    available = parsed_json(
        run(["grok", "plugin", "list", "--available", "--json"], env=env)
    )
    available_names = {entry["name"] for entry in available}
    check(
        available_names == expected_plugins,
        f"Grok listed unexpected plugins: {sorted(available_names)}",
    )

    for plugin_name in sorted(expected_plugins):
        run(["grok", "plugin", "install", plugin_name, "--trust"], env=env)

    listed = parsed_json(run(["grok", "plugin", "list", "--json"], env=env))
    installed_entries = {entry["name"]: entry for entry in listed}
    check(
        set(installed_entries) == expected_plugins,
        f"Grok did not list every installed plugin: {sorted(installed_entries)}",
    )
    for plugin_name, entry in installed_entries.items():
        check(entry["status"] == "installed", f"Grok did not install {plugin_name}")
        check(Path(entry["path"]).is_dir(), f"Grok install is missing: {plugin_name}")

    inspected = parsed_json(run(["grok", "inspect", "--json"], env=env))
    loaded_plugins = {entry["name"]: entry for entry in inspected["plugins"]}
    check(
        set(loaded_plugins) == expected_plugins,
        f"Grok did not load every installed plugin: {sorted(loaded_plugins)}",
    )
    for plugin_name, entry in loaded_plugins.items():
        check(entry["enabled"] is True, f"Grok did not enable {plugin_name}")
    check(
        any(
            skill["name"] == "copy-cleartext"
            and skill["source"].get("plugin_name") == FIXTURE_PLUGIN
            for skill in inspected["skills"]
        ),
        "Grok did not load the fixture skill",
    )


def smoke_cursor(env: dict[str, str], expected_plugins: set[str]) -> None:
    env["NO_COLOR"] = "1"

    plugin_help = run(["cursor-agent", "plugin", "--help"], env=env).stdout
    check("marketplace" in plugin_help, "Cursor does not expose marketplace commands")

    add_help = run(
        ["cursor-agent", "plugin", "marketplace", "add", "--help"], env=env
    ).stdout
    check("<gitUrl>" in add_help, "Cursor marketplace add contract changed")
    list_help = run(
        ["cursor-agent", "plugin", "marketplace", "list", "--help"], env=env
    ).stdout
    check('--format <format>' in list_help, "Cursor marketplace list contract changed")

    root_help = run(["cursor-agent", "--help"], env=env).stdout
    check("--plugin-dir <path>" in root_help, "Cursor removed local plugin loading")

    # Marketplace state is account-backed in Cursor. Exercise both documented
    # commands, then assert they stop specifically at the no-secret auth gate.
    marketplace_commands = [
        [
            "cursor-agent",
            "plugin",
            "marketplace",
            "add",
            "https://github.com/omriariav/omri-marketplace",
        ],
        ["cursor-agent", "plugin", "marketplace", "list", "--format", "json"],
    ]
    for arguments in marketplace_commands:
        attempted = run(arguments, env=env, expect_success=False)
        message = (attempted.stdout + attempted.stderr).lower()
        check(attempted.returncode != 0, "Cursor unexpectedly bypassed authentication")
        check(
            "authenticat" in message or "login" in message or "api key" in message,
            f"Cursor marketplace command failed before its auth gate: {message}",
        )

    plugin_roots = [ROOT / "plugins" / name for name in sorted(expected_plugins)]
    for plugin_root in plugin_roots:
        check(
            (plugin_root / ".cursor-plugin" / "plugin.json").is_file(),
            f"Cursor manifest is missing for {plugin_root.name}",
        )
    fixture_skill = (
        ROOT
        / "plugins"
        / FIXTURE_PLUGIN
        / "skills"
        / "copy-cleartext"
        / "SKILL.md"
    )
    check(fixture_skill.is_file(), "Cursor fixture skill is missing")

    # Cursor validates every --plugin-dir before its authentication gate.
    # Reaching the gate proves the real CLI accepted all current plugins.
    plugin_arguments = [
        argument
        for plugin_root in plugin_roots
        for argument in ("--plugin-dir", str(plugin_root))
    ]
    attempted_load = run(
        [
            "cursor-agent",
            *plugin_arguments,
            "--print",
            "--output-format",
            "text",
            "Reply with loaded.",
        ],
        env=env,
        expect_success=False,
    )
    check(attempted_load.returncode != 0, "Cursor unexpectedly bypassed authentication")
    message = (attempted_load.stdout + attempted_load.stderr).lower()
    check(
        "authenticat" in message or "login" in message or "api key" in message,
        f"Cursor local plugin loading failed before its auth gate: {message}",
    )
    check("path does not exist" not in message, "Cursor rejected a plugin path")


SMOKE_TESTS = {
    "codex": smoke_codex,
    "grok": smoke_grok,
    "cursor": smoke_cursor,
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in SMOKE_TESTS:
        choices = "|".join(SMOKE_TESTS)
        print(f"usage: {Path(sys.argv[0]).name} <{choices}>", file=sys.stderr)
        return 2

    runtime = sys.argv[1]
    executable = "cursor-agent" if runtime == "cursor" else runtime
    check(shutil.which(executable) is not None, f"{executable} is not on PATH")
    expected_plugins = assert_catalog_matches(runtime)

    with tempfile.TemporaryDirectory(prefix=f"{runtime}-plugin-smoke-") as temp_home:
        env = os.environ.copy()
        env["HOME"] = temp_home
        SMOKE_TESTS[runtime](env, expected_plugins)

    print(
        f"{runtime} CLI compatibility passed for {len(expected_plugins)} marketplace "
        f"plugins; loaded fixture: {FIXTURE_PLUGIN}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
