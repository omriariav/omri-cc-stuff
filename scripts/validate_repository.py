#!/usr/bin/env python3
"""Run dependency-free syntax checks across repository-owned files."""

from __future__ import annotations

import json
import py_compile
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [
        ROOT / relative
        for relative in result.stdout.split("\0")
        if relative and (ROOT / relative).is_file()
    ]


def main() -> int:
    files = tracked_files()
    json_files = sorted(path for path in files if path.suffix == ".json")
    python_files = sorted(path for path in files if path.suffix == ".py")
    shell_files = sorted(path for path in files if path.suffix == ".sh")

    for path in json_files:
        json.loads(path.read_text(encoding="utf-8"))
    for path in python_files:
        py_compile.compile(path, doraise=True)
    for path in shell_files:
        subprocess.run(["bash", "-n", str(path)], check=True)

    print(
        "Validated "
        f"{len(json_files)} JSON files, "
        f"{len(python_files)} Python files, and "
        f"{len(shell_files)} shell files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
