#!/usr/bin/env python3
"""
cleaner_checks.py — per-skill skill-cleaner checks for /skill-reviewer.

Runs the skill-cleaner methodology (by @steipete) against ONE target skill:
  https://github.com/steipete/agent-scripts/blob/main/skills/skill-cleaner/SKILL.md

Reports three per-skill signals:
  1. Description budget  — token cost vs the fleet-budget cap (heavy=trim?)
  2. Duplicates          — other copies of the same skill name, with keep-priority
  3. Usage evidence      — recent transcript path mentions (opt-in via --with-logs)

These signals feed into the /skill-reviewer report under
"## Skill Cleanliness Signals" — informational alongside the 10-dim rubric,
not part of the score. Read-only; suggests, never edits.

Usage:
  python3 cleaner_checks.py <path-to-SKILL.md-or-its-parent-dir>
  python3 cleaner_checks.py <path>  --with-logs
  python3 cleaner_checks.py <path>  --json
  python3 cleaner_checks.py <path>  --root ~/Code/myproject/plugins
"""

import argparse
import json
import math
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_CONTEXT_TOKENS = 200_000
DEFAULT_BUDGET_PERCENT = 2.0
DEFAULT_MONTHS = 3
DEFAULT_HEAVY_TOK = 120
SKIP_DIR_PARTS = {".git", "node_modules", ".venv", "vendor", "__pycache__"}


def default_roots():
    """Standard Claude Code skill roots that exist on disk."""
    home = Path.home()
    roots = []
    p = home / ".claude" / "skills"
    if p.is_dir():
        roots.append(p)
    cache = home / ".claude" / "plugins" / "cache"
    if cache.is_dir():
        for marketplace in cache.iterdir():
            if not marketplace.is_dir():
                continue
            plugins_dir = marketplace / "plugins"
            if not plugins_dir.is_dir():
                continue
            for plugin in plugins_dir.iterdir():
                sk = plugin / "skills"
                if sk.is_dir():
                    roots.append(sk)
    return roots


def find_skill_files(root: Path):
    """os.walk with directory pruning — skips noise dirs during traversal."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_PARTS]
        if "SKILL.md" in filenames:
            out.append(Path(dirpath) / "SKILL.md")
    return out


def parse_frontmatter(text: str):
    """Return (name, description) tolerant to YAML block-scalar `description: |`."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return None, None
    fm = m.group(1)
    name_m = re.search(r"(?m)^name:\s*([^\n]+)", fm)
    desc_m = re.search(r"(?m)^description:\s*(.*?)(?=^[A-Za-z][\w-]*:\s|\Z)", fm + "\n", re.DOTALL)
    name = name_m.group(1).strip() if name_m else None
    desc = None
    if desc_m:
        d = desc_m.group(1).strip()
        # Strip YAML block-scalar header (`|`, `>`, with optional chomping `+`/`-`)
        # so the content — not the marker — is what gets measured.
        d = re.sub(r"^[|>][+-]?\s*\n", "", d)
        if d[:1] in ('"', "'") and d[-1:] == d[:1]:
            d = d[1:-1]
        d = re.sub(r"\s+", " ", d).strip()
        desc = d
    return name, desc


def tok_cost(s: str) -> int:
    """Skill-cleaner token cost: ceil(utf8_bytes / 4)."""
    return math.ceil(len(s.encode("utf-8")) / 4)


def classify_origin(path: Path):
    """Priority for which copy to keep (lower number = prefer)."""
    s = str(path)
    if "/.claude/plugins/cache/" in s:
        return ("plugin", 1)
    if "/.claude/skills/" in s:
        return ("personal", 2)
    return ("repo", 3)


def scan_logs_for(skill_name: str, months: int):
    """
    Conservative path-only scan: find transcripts containing
    'skills/<name>/SKILL.md' in the last N months. Skills invoked by name
    without a path won't appear here — treat as candidate signal only.
    """
    projects = Path.home() / ".claude" / "projects"
    if not projects.is_dir():
        return None, 0, 0, "(no ~/.claude/projects directory found)"
    cutoff = datetime.now() - timedelta(days=months * 30)
    pattern = re.compile(rf"skills/{re.escape(skill_name)}/SKILL\.md")
    n_scanned = 0
    n_hits = 0
    latest = None
    for jsonl in projects.rglob("*.jsonl"):
        try:
            mtime = datetime.fromtimestamp(jsonl.stat().st_mtime)
            if mtime < cutoff:
                continue
            n_scanned += 1
            with open(jsonl, encoding="utf-8", errors="ignore") as f:
                if any(pattern.search(line) for line in f):
                    n_hits += 1
                    if latest is None or mtime > latest:
                        latest = mtime
        except Exception:
            continue
    return latest, n_hits, n_scanned, f"({n_scanned} transcripts scanned in last {months} months; conservative path-only heuristic)"


def find_duplicates(name: str, target: Path, roots):
    """
    Return list of OTHER SKILL.md paths (besides target) whose frontmatter name == name.
    Realpath-deduped so a skill reachable via multiple symlinked roots is reported once.
    """
    matches = []
    seen_real = {target.resolve()}
    for r in roots:
        for skill_md in find_skill_files(r):
            real = skill_md.resolve()
            if real in seen_real:
                continue
            seen_real.add(real)
            try:
                txt = skill_md.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            n, _ = parse_frontmatter(txt)
            n = n or skill_md.parent.name
            if n == name:
                origin, prio = classify_origin(skill_md)
                matches.append({"path": str(skill_md), "origin": origin, "priority": prio})
    return matches


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("target", help="path to the target skill's SKILL.md (or its parent dir)")
    p.add_argument("--root", action="append", default=[], help="extra skill root to scan for duplicates (repeatable)")
    p.add_argument("--with-logs", action="store_true", help="opt-in: scan ~/.claude/projects/*.jsonl for usage evidence")
    p.add_argument("--months", type=int, default=DEFAULT_MONTHS, help=f"transcript scan window in months (default {DEFAULT_MONTHS})")
    p.add_argument("--context-tokens", type=int, default=DEFAULT_CONTEXT_TOKENS)
    p.add_argument("--budget-percent", type=float, default=DEFAULT_BUDGET_PERCENT)
    p.add_argument("--heavy-threshold", type=int, default=DEFAULT_HEAVY_TOK)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    target = Path(args.target).expanduser().resolve()
    if target.is_dir():
        target = target / "SKILL.md"
    if not target.is_file():
        print(f"error: SKILL.md not found at {target}", file=sys.stderr)
        sys.exit(2)

    try:
        text = target.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"error: cannot read {target}: {e}", file=sys.stderr)
        sys.exit(2)

    name, desc = parse_frontmatter(text)
    if not name:
        name = target.parent.name
    desc = desc or ""

    target_tokens = tok_cost(desc)
    target_origin, target_prio = classify_origin(target)
    budget_cap = math.floor(args.context_tokens * args.budget_percent / 100)
    pct_of_cap = (target_tokens / budget_cap * 100) if budget_cap else 0.0
    pressure = "OK" if target_tokens < args.heavy_threshold else "CANDIDATE for trim"

    # Duplicates
    roots = default_roots() + [Path(r).expanduser() for r in args.root]
    roots = [r for r in roots if r.is_dir()]
    seen = set()
    uniq_roots = []
    for r in roots:
        rp = r.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        uniq_roots.append(r)
    roots = uniq_roots

    duplicates = find_duplicates(name, target, roots)
    all_copies = [{"path": str(target), "origin": target_origin, "priority": target_prio}] + duplicates
    keep_suggestion = sorted(all_copies, key=lambda x: x["priority"])[0] if duplicates else None

    # Usage
    usage = None
    log_summary = "(skipped — pass --with-logs to enable)"
    if args.with_logs:
        latest, n_hits, n_scanned, log_summary = scan_logs_for(name, args.months)
        usage = {
            "latest": latest.strftime("%Y-%m-%d") if latest else None,
            "sessions_with_path_evidence": n_hits,
            "transcripts_scanned": n_scanned,
            "months_window": args.months,
        }

    report = {
        "skill": name,
        "path": str(target),
        "origin": target_origin,
        "budget": {
            "tokens": target_tokens,
            "pct_of_cap": round(pct_of_cap, 1),
            "cap_tokens": budget_cap,
            "context_tokens": args.context_tokens,
            "budget_percent": args.budget_percent,
            "heavy_threshold": args.heavy_threshold,
            "pressure": pressure,
        },
        "duplicates": duplicates,
        "keep_suggestion": keep_suggestion,
        "usage": usage,
        "log_summary": log_summary,
        "roots_scanned": [str(r) for r in roots],
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return

    # NOTE: the `## Skill Cleanliness Signals` heading is supplied by
    # references/report-template.md; this script emits the section CONTENT only,
    # which Claude pastes in place of the placeholder. Avoids a duplicate H2.
    print(f"_Methodology: [skill-cleaner by @steipete](https://github.com/steipete/agent-scripts/blob/main/skills/skill-cleaner/SKILL.md), per-skill subset. Informational — not part of the rubric score._")
    print()
    print(f"**Target**: `{name}` at `{target}` [{target_origin}]")
    print()
    print(f"**1. Description budget** — {target_tokens} tok ({pct_of_cap:.1f}% of {budget_cap:,}-tok cap)  **{pressure}**")
    print(f"   Cap = {args.budget_percent}% of {args.context_tokens:,}-tok context; heavy threshold = {args.heavy_threshold} tok.")
    print()
    print(f"**2. Duplicates across roots**")
    if duplicates:
        print(f"   Found {len(duplicates)} other cop{'y' if len(duplicates) == 1 else 'ies'} of `{name}`:")
        for d in duplicates:
            print(f"   - `{d['path']}` [{d['origin']}]")
        print(f"   Keep-priority (plugin > personal > repo) suggests **keep**: `{keep_suggestion['path']}` [{keep_suggestion['origin']}].")
        for c in all_copies:
            if c["path"] != keep_suggestion["path"]:
                print(f"   - **remove**: `{c['path']}` [{c['origin']}]")
    else:
        print(f"   (none — `{name}` is unique across {len(roots)} scanned root(s))")
    print()
    print(f"**3. Usage evidence**")
    print(f"   {log_summary}")
    if usage:
        if usage["latest"]:
            print(f"   Last seen (path evidence): **{usage['latest']}**; {usage['sessions_with_path_evidence']} session(s) in last {usage['months_window']} months.")
        else:
            print(f"   No transcript path evidence in last {usage['months_window']} months.")
            print(f"   Note: path-only heuristic. Skills invoked by name without a path won't show. Treat as candidate signal, not proof of disuse.")


if __name__ == "__main__":
    main()
