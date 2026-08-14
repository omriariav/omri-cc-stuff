#!/usr/bin/env python3
"""Run dependency-free syntax checks across repository-owned files."""

from __future__ import annotations

import json
import py_compile
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", "__pycache__"}


def repository_files(pattern: str) -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob(pattern)
        if not any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts)
    )


def main() -> int:
    json_files = repository_files("*.json")
    python_files = repository_files("*.py")
    shell_files = repository_files("*.sh")

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
