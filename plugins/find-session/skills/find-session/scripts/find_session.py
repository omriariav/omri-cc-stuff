#!/usr/bin/env python3
"""Search Claude Code session history by keyword."""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config.json"
    try:
        with open(config_path) as f:
            cfg = json.load(f)
        # Validate key fields
        cfg["max_results"] = max(1, int(cfg.get("max_results", 20)))
        cfg["haiku_threshold"] = max(1, int(cfg.get("haiku_threshold", 50)))
        return cfg
    except Exception:
        return {"max_results": 20, "haiku_threshold": 50}


def slug_to_display(slug: str) -> str:
    """Convert -Users-omri-a-Code-yaklar -> 'yaklar'."""
    s = slug.lstrip("-")
    # Try common markers in order
    for marker in ("-Code-", "-code-", "-Projects-", "-projects-", "-src-"):
        idx = s.find(marker)
        if idx != -1:
            return s[idx + len(marker):]
    parts = s.split("-")
    return parts[-1] if parts else slug


def resolve_project_root() -> str:
    """Resolve project root via git, falling back to cwd."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return os.getcwd()


def parse_session(content: str) -> tuple:
    """Single-pass parse: returns (custom_title, first_user_msg, user_text_lower).

    Extracts the latest custom-title, first user message preview,
    and all user message text for keyword matching — in one pass.
    """
    custom_title = None
    first_msg = "(no message)"
    user_parts = []

    for line in content.splitlines():
        try:
            d = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue

        # Track latest custom-title (not first — user may /rename multiple times)
        if d.get("type") == "custom-title":
            title = d.get("customTitle", "").strip()
            if title:
                custom_title = title
                user_parts.append(title)

        msg = d.get("message") or {}
        if msg.get("role") != "user":
            continue

        c = msg.get("content", "")
        if isinstance(c, list):
            for item in c:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item["text"]
                    user_parts.append(text)
                    if first_msg == "(no message)":
                        first_msg = " ".join(text.split())[:130]
        elif isinstance(c, str) and c:
            user_parts.append(c)
            if first_msg == "(no message)":
                first_msg = " ".join(c.split())[:130]

    return custom_title, first_msg, "\n".join(user_parts).lower()


def matches_query(text: str, query: str) -> bool:
    """Match each query term in text. Uses literal substring for terms with
    special characters, word-boundary for plain alphanumeric terms."""
    for term in query.split():
        if re.search(r'[^\w]', term):
            # Term has punctuation — use literal substring match
            if term not in text:
                return False
        else:
            if not re.search(r'\b' + re.escape(term) + r'\b', text):
                return False
    return True


def search_project_dir(project_dir: Path, query: str, display: str) -> list:
    results = []
    for fpath in project_dir.glob("*.jsonl"):
        try:
            content = fpath.read_text(errors="replace")
        except Exception:
            continue

        custom_title, first_msg, user_text = parse_session(content)

        if query and not matches_query(user_text, query):
            continue

        dt = datetime.fromtimestamp(fpath.stat().st_mtime)
        results.append({
            "date": dt,
            "project": display,
            "session_id": fpath.stem,
            "title": custom_title,
            "preview": first_msg,
            "path": str(fpath),
        })
    return results


def format_text(results: list, search_all: bool, query: str, max_results: int):
    """Human-readable output."""
    total = len(results)
    shown = results[:max_results]
    scope = "all projects" if search_all else "current project"
    label = f'matching "{query}"' if query else "recent"
    print(f"Found {total} {label} session(s) in {scope}:\n")

    for r in shown:
        prefix = f"[{r['project']}]  " if search_all else ""
        title_line = f'  title: "{r["title"]}"' if r["title"] else f"  {r['preview']}"
        print(f"{r['date'].strftime('%Y-%m-%d %H:%M')}  {prefix}{r['session_id']}")
        print(title_line)
        print(f"  claude --resume {r['session_id']}")
        print()

    if total > max_results:
        print(f"(showing {max_results} of {total} — refine your query to narrow down)")

    untitled = sum(1 for r in shown if not r["title"])
    # Hint line on stderr so it doesn't pollute user-visible output
    print(f"# UNTITLED_COUNT={untitled} TOTAL_SHOWN={len(shown)}", file=sys.stderr)


def format_json(results: list, search_all: bool, query: str, max_results: int):
    """JSON output for programmatic use."""
    shown = results[:max_results]
    output = {
        "query": query,
        "scope": "all" if search_all else "current",
        "total": len(results),
        "shown": len(shown),
        "sessions": [
            {
                "date": r["date"].strftime("%Y-%m-%d %H:%M"),
                "project": r["project"],
                "session_id": r["session_id"],
                "title": r["title"],
                "preview": r["preview"] if not r["title"] else None,
                "path": r["path"],
                "untitled": r["title"] is None,
                "resume_cmd": f"claude --resume {r['session_id']}",
            }
            for r in shown
        ],
    }
    untitled = sum(1 for r in shown if not r["title"])
    output["untitled_count"] = untitled
    print(json.dumps(output, indent=2))


def main():
    args = sys.argv[1:]

    search_all = "--all" in args or "-all" in args
    args = [a for a in args if a not in ("--all", "-all")]

    output_json = "--json" in args
    args = [a for a in args if a != "--json"]

    query = " ".join(args).lower()
    config = load_config()
    max_results = config.get("max_results", 20)
    exclude_slugs = set(config.get("exclude_slugs", []))

    projects_root = Path.home() / ".claude" / "projects"

    if not projects_root.exists():
        if output_json:
            print(json.dumps({"error": "No sessions directory found at ~/.claude/projects/", "sessions": [], "total": 0}))
        else:
            print("No sessions directory found at ~/.claude/projects/")
        return

    if search_all:
        dirs_to_search = []
        for project_dir in sorted(projects_root.iterdir()):
            slug = project_dir.name
            if not project_dir.is_dir():
                continue
            if slug in exclude_slugs:
                continue
            if "claude-mem-observer" in slug or "mem-observer" in slug:
                continue
            dirs_to_search.append((project_dir, slug_to_display(slug)))
    else:
        project_root = resolve_project_root()
        slug = project_root.replace("/", "-").replace(".", "-")
        project_dir = projects_root / slug
        dirs_to_search = [(project_dir, slug_to_display(slug))]

    results = []
    for project_dir, display in dirs_to_search:
        if not project_dir.exists():
            if not search_all:
                msg = f"No session directory found for current project.\nExpected: {project_dir}"
                if output_json:
                    print(json.dumps({"error": msg, "sessions": [], "total": 0}))
                else:
                    print(msg)
            continue
        results.extend(search_project_dir(project_dir, query, display))

    if not results:
        scope = "all projects" if search_all else "current project"
        msg = f'No matching sessions found in {scope}.'
        hint = f'\nQuery: "{query}"' if query else ""
        suggestion = "\nTry adding --all to search across all projects." if query and not search_all else ""
        if output_json:
            print(json.dumps({"error": msg, "query": query, "scope": scope, "sessions": [], "total": 0}))
        else:
            print(msg + hint + suggestion)
        return

    results.sort(key=lambda r: r["date"], reverse=True)

    if output_json:
        format_json(results, search_all, query, max_results)
    else:
        format_text(results, search_all, query, max_results)


if __name__ == "__main__":
    main()
