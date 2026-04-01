#!/usr/bin/env python3
"""Search Claude Code session history by keyword."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config.json"
    try:
        with open(config_path) as f:
            return json.load(f)
    except Exception:
        return {}


def slug_to_display(slug: str) -> str:
    """Convert -Users-omri-a-Code-yaklar -> 'yaklar'."""
    s = slug.lstrip("-")
    marker = "-Code-"
    idx = s.find(marker)
    if idx != -1:
        return s[idx + len(marker):]
    parts = s.split("-")
    return parts[-1] if parts else slug


def parse_session(content: str) -> tuple:
    """Return (custom_title_or_None, first_user_message)."""
    custom_title = None
    first_msg = "(no message)"
    for line in content.splitlines():
        try:
            d = json.loads(line)
            if d.get("type") == "custom-title":
                custom_title = d.get("customTitle", "").strip()
            if first_msg == "(no message)":
                msg = d.get("message") or {}
                if msg.get("role") == "user":
                    c = msg.get("content", "")
                    if isinstance(c, list):
                        for item in c:
                            if isinstance(item, dict) and item.get("type") == "text":
                                first_msg = item["text"].strip()[:130]
                                break
                    elif isinstance(c, str):
                        first_msg = c.strip()[:130]
        except Exception:
            pass
        if custom_title and first_msg != "(no message)":
            break
    return custom_title, first_msg


def search_project_dir(project_dir: Path, query: str, display: str) -> list:
    results = []
    for fpath in project_dir.glob("*.jsonl"):
        try:
            content = fpath.read_text(errors="ignore")
        except Exception:
            continue
        if query and query not in content.lower():
            continue
        dt = datetime.fromtimestamp(fpath.stat().st_mtime)
        custom_title, first_msg = parse_session(content)
        results.append((dt, display, fpath.stem, custom_title, first_msg))
    return results


def main():
    args = sys.argv[1:]

    search_all = "--all" in args
    if search_all:
        args = [a for a in args if a != "--all"]

    query = " ".join(args).lower()
    config = load_config()
    max_results = config.get("max_results", 20)
    exclude_slugs = set(config.get("exclude_slugs", []))

    projects_root = Path.home() / ".claude" / "projects"

    if search_all:
        # Search all projects
        dirs_to_search = []
        for project_dir in sorted(projects_root.iterdir()):
            slug = project_dir.name
            if not project_dir.is_dir():
                continue
            if slug in exclude_slugs:
                continue
            # Auto-skip claude-mem observer directories (noisy background sessions)
            if "claude-mem-observer" in slug or "mem-observer" in slug:
                continue
            dirs_to_search.append((project_dir, slug_to_display(slug)))
    else:
        # Default: current project only
        cwd = os.getcwd()
        slug = cwd.replace("/", "-").replace(".", "-")
        project_dir = projects_root / slug
        dirs_to_search = [(project_dir, slug_to_display(slug))]

    results = []
    for project_dir, display in dirs_to_search:
        if not project_dir.exists():
            if not search_all:
                print(f"No session directory found for current project.")
                print(f"Expected: {project_dir}")
            continue
        results.extend(search_project_dir(project_dir, query, display))

    if not results:
        scope = "all projects" if search_all else "current project"
        print(f"No matching sessions found in {scope}.")
        if query:
            print(f'Query: "{query}"')
            if not search_all:
                print("Try adding --all to search across all projects.")
        return

    results.sort(reverse=True)
    scope = "all projects" if search_all else "current project"
    label = f'matching "{query}"' if query else "recent"
    total = len(results)
    shown = results[:max_results]
    print(f"Found {total} {label} session(s) in {scope}:\n")
    for dt, display, sid, custom_title, first_msg in shown:
        prefix = f"[{display}]  " if search_all else ""
        title_line = f'  title: "{custom_title}"' if custom_title else f"  {first_msg}"
        print(f"{dt.strftime('%Y-%m-%d %H:%M')}  {prefix}{sid}")
        print(title_line)
        print(f"  claude --resume {sid}")
        print()
    if total > max_results:
        print(f"(showing {max_results} of {total} — refine your query to narrow down)")

    # Hint for Claude: how many shown results lack a custom title
    untitled = sum(1 for _, _, _, ct, _ in shown if not ct)
    print(f"# UNTITLED_COUNT={untitled} TOTAL_SHOWN={len(shown)}")


if __name__ == "__main__":
    main()
