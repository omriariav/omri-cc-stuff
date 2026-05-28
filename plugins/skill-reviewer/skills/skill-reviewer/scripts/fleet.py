#!/usr/bin/env python3
"""
fleet.py — cross-skill audit for /skill-reviewer.

Adapts the skill-cleaner methodology by @steipete for Claude Code:
  https://github.com/steipete/agent-scripts/blob/main/skills/skill-cleaner/SKILL.md

Where the rest of /skill-reviewer evaluates a single skill in depth, this runs
across the WHOLE loaded set and reports five sections in skill-cleaner's
prescribed order:

  1. Skill Budget                — always-loaded description tokens vs cap
  2. Description Candidates      — heavy descriptions worth trimming
  3. Duplicates                  — same skill name across multiple roots
  4. Unused Candidates           — no transcript path evidence (opt-in)
  5. Roots                       — what was actually scanned

Read-only. Suggests changes; never applies them.

Usage:
  python3 fleet.py
  python3 fleet.py --root ~/Code/myproject/plugins
  python3 fleet.py --with-logs --months 3
  python3 fleet.py --context-tokens 200000 --budget-percent 2
  python3 fleet.py --json
"""

import argparse
import json
import math
import re
from collections import defaultdict
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
    # Installed plugins: ~/.claude/plugins/cache/<marketplace>/plugins/<plugin>/skills
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


def find_skills(root: Path):
    """Find SKILL.md files under root, skipping noise dirs."""
    out = []
    for path in root.rglob("SKILL.md"):
        if any(part in SKIP_DIR_PARTS for part in path.parts):
            continue
        out.append(path)
    return out


def parse_frontmatter(text: str):
    """Return (name, description) from YAML frontmatter, tolerant to block scalars."""
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
        if d[:1] in ('"', "'") and d[-1:] == d[:1]:
            d = d[1:-1]
        d = re.sub(r"\s+", " ", d).strip()
        desc = d
    return name, desc


def tok_cost(s: str) -> int:
    """Token cost per skill-cleaner: ceil(utf8_bytes / 4)."""
    return math.ceil(len(s.encode("utf-8")) / 4)


def classify_origin(path: Path):
    """Priority for which copy to keep (lower number = preferred to keep)."""
    s = str(path)
    if "/.claude/plugins/cache/" in s:
        return ("plugin", 1)
    if "/.claude/skills/" in s:
        return ("personal", 2)
    return ("repo", 3)


def scan_logs(months: int):
    """
    Conservative path-only scan: which skill names appear as
    'skills/<name>/SKILL.md' in Claude Code transcripts over the last N months.
    Skills invoked by name without a path won't be detected — treat output as
    CANDIDATES only.
    """
    projects = Path.home() / ".claude" / "projects"
    if not projects.is_dir():
        return set(), "(no ~/.claude/projects directory found)"
    cutoff = datetime.now() - timedelta(days=months * 30)
    mentioned: set[str] = set()
    n_files = 0
    for jsonl in projects.rglob("*.jsonl"):
        try:
            if datetime.fromtimestamp(jsonl.stat().st_mtime) < cutoff:
                continue
            n_files += 1
            with open(jsonl, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    for m in re.finditer(r"skills/([A-Za-z0-9_\-]+)/SKILL\.md", line):
                        mentioned.add(m.group(1))
        except Exception:
            continue
    return mentioned, f"({n_files} transcript files scanned, last {months} months; conservative path-only heuristic)"


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--root", action="append", default=[], help="extra skill root to scan (repeatable)")
    p.add_argument("--with-logs", action="store_true", help="opt-in: scan ~/.claude/projects/*.jsonl for unused-candidate detection")
    p.add_argument("--months", type=int, default=DEFAULT_MONTHS, help=f"transcript scan window in months (default {DEFAULT_MONTHS})")
    p.add_argument("--context-tokens", type=int, default=DEFAULT_CONTEXT_TOKENS, help=f"context window for budget calc (default {DEFAULT_CONTEXT_TOKENS:,})")
    p.add_argument("--budget-percent", type=float, default=DEFAULT_BUDGET_PERCENT, help=f"budget %% of context (default {DEFAULT_BUDGET_PERCENT})")
    p.add_argument("--heavy-threshold", type=int, default=DEFAULT_HEAVY_TOK, help=f"description token threshold flagged as trim candidate (default {DEFAULT_HEAVY_TOK})")
    p.add_argument("--json", action="store_true", help="machine-readable JSON output")
    args = p.parse_args()

    roots = default_roots() + [Path(r).expanduser() for r in args.root]
    roots = [r for r in roots if r.is_dir()]
    # realpath de-dup to avoid symlink false positives
    seen: set[Path] = set()
    uniq_roots = []
    for r in roots:
        rp = r.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        uniq_roots.append(r)
    roots = uniq_roots

    skills = []
    by_name: dict[str, list[dict]] = defaultdict(list)
    for r in roots:
        for skill_md in find_skills(r):
            try:
                txt = skill_md.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            name, desc = parse_frontmatter(txt)
            if not name:
                name = skill_md.parent.name
            desc = desc or ""
            origin, prio = classify_origin(skill_md)
            entry = {
                "name": name,
                "description": desc,
                "tokens": tok_cost(desc),
                "path": str(skill_md),
                "origin": origin,
                "priority": prio,
                "root": str(r),
            }
            skills.append(entry)
            by_name[name].append(entry)

    total_tokens = sum(s["tokens"] for s in skills)
    budget = math.floor(args.context_tokens * args.budget_percent / 100)
    pct_of_budget = (total_tokens / budget * 100) if budget else 0.0
    candidates = sorted([s for s in skills if s["tokens"] >= args.heavy_threshold], key=lambda x: -x["tokens"])
    dupes = {n: lst for n, lst in by_name.items() if len(lst) > 1}

    unused = []
    log_summary = "(skipped — pass --with-logs to enable)"
    if args.with_logs:
        mentioned, log_summary = scan_logs(args.months)
        unused = [s for s in skills if s["name"] not in mentioned]

    report = {
        "budget": {
            "total_tokens": total_tokens,
            "budget": budget,
            "pct_of_budget": round(pct_of_budget, 1),
            "context_tokens": args.context_tokens,
            "budget_percent": args.budget_percent,
            "skill_count": len(skills),
        },
        "description_candidates": candidates,
        "duplicates": dupes,
        "unused": unused,
        "log_summary": log_summary,
        "roots": [str(r) for r in roots],
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return

    b = report["budget"]
    pressure = "OK" if b["pct_of_budget"] < 80 else ("WARN" if b["pct_of_budget"] < 100 else "OVER")
    bar = "=" * 72
    print(bar)
    print(f"  Skill fleet audit  ({b['skill_count']} skills across {len(report['roots'])} root(s))")
    print(f"  Methodology: skill-cleaner by @steipete, adapted for Claude Code")
    print(bar)
    print()
    print("1. Skill Budget")
    print(f"   Always-loaded description tokens: {b['total_tokens']:,} / {b['budget']:,} ({b['pct_of_budget']}% of budget)  [{pressure}]")
    print(f"   Budget formula: {b['budget_percent']}% of {b['context_tokens']:,}-token context = {b['budget']:,} tokens")
    print()
    print("2. Description Optimization Candidates")
    if candidates:
        print(f"   {len(candidates)} skill(s) with description >= {args.heavy_threshold} tokens:")
        for c in candidates[:20]:
            short = c["description"][:90] + ("..." if len(c["description"]) > 90 else "")
            print(f"   - {c['name']:30}  {c['tokens']:4d} tok   [{c['origin']}]")
            print(f"       {short}")
        if len(candidates) > 20:
            print(f"   ... and {len(candidates) - 20} more")
    else:
        print("   (none — all descriptions under threshold)")
    print()
    print("3. Duplicates")
    if dupes:
        for name, entries in sorted(dupes.items()):
            ordered = sorted(entries, key=lambda x: x["priority"])
            keep = ordered[0]
            print(f"   - {name}  ({len(entries)} copies)")
            print(f"       keep:   {keep['path']}  [{keep['origin']}]")
            for e in ordered[1:]:
                print(f"       remove: {e['path']}  [{e['origin']}]")
    else:
        print("   (none)")
    print()
    print("4. Unused Skill Candidates")
    print(f"   {log_summary}")
    if args.with_logs:
        if unused:
            print(f"   {len(unused)} skill(s) with no transcript path evidence:")
            for u in sorted(unused, key=lambda x: x["name"])[:30]:
                print(f"   - {u['name']:30}  [{u['origin']}]  {u['path']}")
            if len(unused) > 30:
                print(f"   ... and {len(unused) - 30} more")
            print("   Note: heuristic is conservative (path-only). Skills invoked by name without")
            print("         path won't show as evidence. Treat as CANDIDATES — never auto-delete.")
        else:
            print("   (none — every skill has recent path evidence)")
    print()
    print("5. Roots")
    for r in report["roots"]:
        n_in_root = sum(1 for s in skills if s["root"] == r)
        print(f"   - {r}  ({n_in_root} skill(s))")
    print()
    print("Output policy: suggestions only. Apply fixes via /skill-reviewer --fix <skill> or edit manually.")


if __name__ == "__main__":
    main()
