#!/usr/bin/env python3
"""
View and query the skill-reviewer history log.

Usage:
    python3 scripts/history.py                    # Show all entries
    python3 scripts/history.py --skill <name>     # Filter by skill name
    python3 scripts/history.py --last 5           # Last N entries
    python3 scripts/history.py --append "..."     # Append a new entry

Log format (one line per review):
    YYYY-MM-DD | <skill-name> | <score>/29 | <grade> | <top-issue>
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime


def get_log_path() -> Path:
    """Get history log path from config.json or default."""
    config_path = Path(__file__).parent.parent / "config.json"
    default = Path.home() / ".claude/plugin-data/skill-review/history.log"
    try:
        config = json.loads(config_path.read_text())
        raw = config.get("history_log", str(default))
        return Path(raw).expanduser()
    except (OSError, json.JSONDecodeError):
        return default


def read_log(log_path: Path) -> list[dict]:
    """Parse history log into structured records.

    Format: YYYY-MM-DD | skill-name | score/29 | grade | top issue
    The top-issue field may contain pipes — split on the first 4 delimiters only.
    """
    if not log_path.exists():
        return []

    records = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        # Split on first 4 pipes only so top_issue can contain pipes safely
        parts = [p.strip() for p in line.split("|", maxsplit=4)]
        if len(parts) >= 4:
            records.append({
                "date": parts[0],
                "skill": parts[1],
                "score": parts[2],
                "grade": parts[3],
                "top_issue": parts[4] if len(parts) > 4 else "",
                "raw": line,
            })
    return records


def append_entry(log_path: Path, entry: str):
    """Append a new entry to the history log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(entry.strip() + "\n")
    print(f"Appended to {log_path}")


def main():
    parser = argparse.ArgumentParser(description="Query skill-reviewer history log")
    parser.add_argument("--skill", help="Filter by skill name (partial match)")
    parser.add_argument("--last", type=int, default=0, help="Show last N entries")
    parser.add_argument("--append", help="Append a new log entry")
    parser.add_argument("--log", help="Override log path")
    args = parser.parse_args()

    log_path = Path(args.log).expanduser() if args.log else get_log_path()

    if args.append:
        append_entry(log_path, args.append)
        return

    records = read_log(log_path)

    if not records:
        print(f"No history found at {log_path}")
        print("Run /skill-reviewer on any skill to start tracking.")
        return

    # Filter
    if args.skill:
        # Exact match first; fall back to substring only if no exact match found
        exact = [r for r in records if r["skill"].lower() == args.skill.lower()]
        records = exact if exact else [r for r in records if args.skill.lower() in r["skill"].lower()]

    if args.last:
        records = records[-args.last:]

    if not records:
        print(f"No records matching filter.")
        return

    # Print table
    print(f"\n  Skill Review History ({log_path})")
    print(f"  {len(records)} record(s)\n")
    print(f"  {'Date':<12} {'Skill':<30} {'Score':<8} {'Grade':<6} Top Issue")
    print("  " + "-" * 80)
    for r in records:
        issue = r["top_issue"][:35] + "..." if len(r["top_issue"]) > 35 else r["top_issue"]
        print(f"  {r['date']:<12} {r['skill']:<30} {r['score']:<8} {r['grade']:<6} {issue}")

    # Summary stats
    grades = [r["grade"] for r in records]
    print(f"\n  Grade distribution: {', '.join(f'{g}={grades.count(g)}' for g in sorted(set(grades)))}")


if __name__ == "__main__":
    main()
