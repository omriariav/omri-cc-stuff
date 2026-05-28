#!/usr/bin/env python3
"""
fleet_audit.py — fleet-level skill-cleaner audit for /claude-reviewer.

Adapts the skill-cleaner methodology (by @steipete) for cross-skill audits
within a project or the global ~/.claude/ scope:
  https://github.com/steipete/agent-scripts/blob/main/skills/skill-cleaner/SKILL.md

Where /skill-reviewer surfaces skill-cleaner signals PER-SKILL (one target,
its budget, its duplicates, its usage), /claude-reviewer surfaces them
FLEET-WIDE across the audited scope:

  1. Fleet budget         — total always-loaded description tokens vs cap
  2. Trim candidates       — skills above the heavy-description threshold
  3. Duplicates            — same skill name across multiple roots
  4. Unused                — opt-in transcript path-scan (candidate signal)

Read-only. Reports signals; never edits. Per-skill fixes flow through
/skill-reviewer --fix <skill>.

Usage:
  python3 fleet_audit.py <project-path>
  python3 fleet_audit.py --global
  python3 fleet_audit.py <project-path> --with-logs
  python3 fleet_audit.py <project-path> --json
"""

import argparse
import json
import math
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_CONTEXT_TOKENS = 200_000
DEFAULT_BUDGET_PERCENT = 2.0
DEFAULT_MONTHS = 3
DEFAULT_HEAVY_TOK = 120
SKIP_DIR_PARTS = {".git", "node_modules", ".venv", "vendor", "__pycache__"}


def project_roots(project_path: Path):
    """Skill roots within a project: .claude/skills/ and plugins/*/skills/."""
    roots = []
    p = project_path / ".claude" / "skills"
    if p.is_dir():
        roots.append(p)
    plugins_dir = project_path / "plugins"
    if plugins_dir.is_dir():
        for plugin in plugins_dir.iterdir():
            if not plugin.is_dir():
                continue
            sk = plugin / "skills"
            if sk.is_dir():
                roots.append(sk)
    return roots


def global_roots():
    """Standard global Claude Code skill roots."""
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
        # Strip YAML block-scalar header (`|`, `>`, with optional `+`/`-` chomping)
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
    """Priority for which copy to keep (lower = prefer)."""
    s = str(path)
    if "/.claude/plugins/cache/" in s:
        return ("plugin", 1)
    if "/.claude/skills/" in s:
        return ("personal", 2)
    return ("repo", 3)


def scan_logs(months: int):
    """
    Conservative path-only transcript scan: return dict skill_name -> latest mtime
    for skills mentioned as 'skills/<name>/SKILL.md' in the last N months.
    Skills invoked by name without a path won't appear — candidate signal only.
    """
    projects = Path.home() / ".claude" / "projects"
    if not projects.is_dir():
        return {}, "(no ~/.claude/projects directory found)"
    cutoff = datetime.now() - timedelta(days=months * 30)
    mentions: dict[str, datetime] = {}
    n_files = 0
    for jsonl in projects.rglob("*.jsonl"):
        try:
            mtime = datetime.fromtimestamp(jsonl.stat().st_mtime)
            if mtime < cutoff:
                continue
            n_files += 1
            with open(jsonl, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    for m in re.finditer(r"skills/([A-Za-z0-9_\-]+)/SKILL\.md", line):
                        name = m.group(1)
                        if name not in mentions or mtime > mentions[name]:
                            mentions[name] = mtime
        except Exception:
            continue
    return mentions, f"({n_files} transcripts scanned, last {months} months; conservative path-only heuristic)"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("scope", nargs="?", help="project directory to audit (omit when using --global)")
    p.add_argument("--global", dest="global_scope", action="store_true", help="audit ~/.claude/ globally")
    p.add_argument("--root", action="append", default=[], help="extra skill root (repeatable)")
    p.add_argument("--with-logs", action="store_true", help="opt-in: scan ~/.claude/projects/*.jsonl for unused detection")
    p.add_argument("--months", type=int, default=DEFAULT_MONTHS, help=f"transcript scan window (months, default {DEFAULT_MONTHS})")
    p.add_argument("--context-tokens", type=int, default=DEFAULT_CONTEXT_TOKENS)
    p.add_argument("--budget-percent", type=float, default=DEFAULT_BUDGET_PERCENT)
    p.add_argument("--heavy-threshold", type=int, default=DEFAULT_HEAVY_TOK)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    if args.global_scope:
        roots = global_roots()
        scope_label = "global (~/.claude/)"
    else:
        if not args.scope:
            print("error: project path required (or use --global)", file=sys.stderr)
            sys.exit(2)
        project_path = Path(args.scope).expanduser().resolve()
        if not project_path.is_dir():
            print(f"error: not a directory: {project_path}", file=sys.stderr)
            sys.exit(2)
        roots = project_roots(project_path)
        scope_label = f"project ({project_path})"

    roots += [Path(r).expanduser() for r in args.root]
    roots = [r for r in roots if r.is_dir()]
    # realpath de-dup
    seen: set[Path] = set()
    uniq_roots = []
    for r in roots:
        rp = r.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        uniq_roots.append(r)
    roots = uniq_roots

    # Scan all skills
    skills = []
    by_name: dict[str, list[dict]] = defaultdict(list)
    seen_files: set[Path] = set()
    for r in roots:
        for skill_md in find_skill_files(r):
            real = skill_md.resolve()
            if real in seen_files:
                continue
            seen_files.add(real)
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
    pressure = "OK" if pct_of_budget < 80 else ("WARN" if pct_of_budget < 100 else "OVER")
    candidates = sorted([s for s in skills if s["tokens"] >= args.heavy_threshold], key=lambda x: -x["tokens"])
    dupes = {n: lst for n, lst in by_name.items() if len(lst) > 1}

    unused = []
    log_summary = "(skipped — pass --with-logs to enable)"
    if args.with_logs:
        mentions, log_summary = scan_logs(args.months)
        for s in skills:
            if s["name"] not in mentions:
                unused.append(s)

    report = {
        "scope": scope_label,
        "budget": {
            "total_tokens": total_tokens,
            "budget": budget,
            "pct_of_budget": round(pct_of_budget, 1),
            "context_tokens": args.context_tokens,
            "budget_percent": args.budget_percent,
            "skill_count": len(skills),
            "pressure": pressure,
        },
        "trim_candidates": candidates,
        "duplicates": dupes,
        "unused": unused,
        "log_summary": log_summary,
        "roots": [str(r) for r in roots],
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return

    # NOTE: the `## Skill Fleet Audit` heading is supplied by
    # references/report-template.md; this script emits the section CONTENT only.
    b = report["budget"]
    print(f"_Methodology: [skill-cleaner by @steipete](https://github.com/steipete/agent-scripts/blob/main/skills/skill-cleaner/SKILL.md), fleet-level. Informational — not part of the rubric score._")
    print()
    print(f"**Scope**: {scope_label} — {b['skill_count']} skill(s) across {len(report['roots'])} root(s)")
    print()
    print(f"**1. Fleet budget** — {b['total_tokens']:,} tok / {b['budget']:,} cap ({b['pct_of_budget']}% of budget)  **{pressure}**")
    print(f"   Cap = {args.budget_percent}% of {args.context_tokens:,}-tok context. Token cost = ceil(utf8_bytes / 4).")
    print()
    print(f"**2. Description trim candidates (>= {args.heavy_threshold} tok)**")
    if candidates:
        for c in candidates[:15]:
            print(f"   - `{c['name']}`  {c['tokens']} tok  [{c['origin']}]  `{c['path']}`")
        if len(candidates) > 15:
            print(f"   ... and {len(candidates) - 15} more")
    else:
        print(f"   (none — all descriptions under {args.heavy_threshold} tok)")
    print()
    print(f"**3. Duplicates across roots**")
    if dupes:
        for name, entries in sorted(dupes.items()):
            ordered = sorted(entries, key=lambda x: x["priority"])
            keep = ordered[0]
            print(f"   - `{name}` ({len(entries)} copies)")
            print(f"     **keep**: `{keep['path']}` [{keep['origin']}]")
            for e in ordered[1:]:
                print(f"     remove: `{e['path']}` [{e['origin']}]")
    else:
        print(f"   (none — all skill names unique across {len(roots)} root(s))")
    print()
    print(f"**4. Unused candidates**")
    print(f"   {log_summary}")
    if args.with_logs:
        if unused:
            for u in sorted(unused, key=lambda x: x["name"])[:20]:
                print(f"   - `{u['name']}`  [{u['origin']}]  `{u['path']}`")
            if len(unused) > 20:
                print(f"   ... and {len(unused) - 20} more")
            print(f"   Note: heuristic is path-only. Skills invoked by name without a path won't show. Treat as candidate — never auto-delete.")
        else:
            print(f"   (none — every skill has recent path evidence)")
    print()
    print(f"**Roots scanned**:")
    for r in report["roots"]:
        n_in_root = sum(1 for s in skills if s["root"] == r)
        print(f"   - `{r}`  ({n_in_root} skill(s))")


if __name__ == "__main__":
    main()
