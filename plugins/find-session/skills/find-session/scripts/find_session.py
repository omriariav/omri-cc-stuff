#!/usr/bin/env python3
"""Search Claude Code and Codex session history by keyword."""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Codex injects these as role=user messages; they are not real user input.
# Matched against whitespace-normalized message text via str.startswith.
CODEX_INJECTION_PREFIXES = (
    "# AGENTS.md instructions",
    "<environment_context>",
    "<skill>",
    "<turn_aborted>",
    "<user_instructions>",
    "<system-reminder>",
    "<<ccr:",
)


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


# ---------------------------------------------------------------------------
# Claude Code sessions: ~/.claude/projects/<slug>/<uuid>.jsonl
# ---------------------------------------------------------------------------

def parse_claude_session(content: str) -> tuple:
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
            raw_title = d.get("customTitle", "")
            title = str(raw_title).strip() if raw_title else ""
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
                    raw_text = item.get("text", "")
                    text = str(raw_text) if raw_text else ""
                    if not text:
                        continue
                    user_parts.append(text)
                    if first_msg == "(no message)":
                        first_msg = " ".join(text.split())[:130]
        elif isinstance(c, str) and c:
            user_parts.append(c)
            if first_msg == "(no message)":
                first_msg = " ".join(c.split())[:130]

    return custom_title, first_msg, "\n".join(user_parts).lower()


def search_claude_dir(project_dir: Path, query: str, display: str) -> list:
    results = []
    for fpath in project_dir.glob("*.jsonl"):
        try:
            content = fpath.read_text(errors="replace")
            mtime = fpath.stat().st_mtime
        except Exception:
            continue

        custom_title, first_msg, user_text = parse_claude_session(content)

        if query and not matches_query(user_text, query):
            continue

        sid = fpath.stem
        dt = datetime.fromtimestamp(mtime)
        results.append({
            "date": dt,
            "source": "claude",
            "project": display,
            "session_id": sid,
            "title": custom_title,
            "preview": first_msg,
            "path": str(fpath),
            "resume_cmd": f"claude --resume {sid}",
        })
    return results


def search_claude(query: str, search_all: bool, exclude_slugs: set) -> list:
    projects_root = Path.home() / ".claude" / "projects"
    if not projects_root.exists():
        return []

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
            continue
        results.extend(search_claude_dir(project_dir, query, display))
    return results


# ---------------------------------------------------------------------------
# Codex sessions: ~/.codex/sessions/<Y>/<M>/<D>/rollout-<ts>-<uuid>.jsonl
# ---------------------------------------------------------------------------

_CODEX_UUID_RE = re.compile(
    r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$"
)


def codex_filename_uuid(fpath: Path):
    """rollout-2026-06-24T00-00-26-019ef648-... -> 019ef648-cd09-7f30-a4e6-...

    Returns the trailing UUID of the rollout filename, or None when the stem
    doesn't end in a well-formed UUID (malformed file)."""
    m = _CODEX_UUID_RE.search(fpath.stem)
    return m.group(1) if m else None


def _cwd_in_project(cwd, project_root: str) -> bool:
    """True when a Codex session's recorded cwd is the project root or a
    subdirectory of it — Codex may be launched from a subdir of the repo."""
    if not cwd:
        return False
    if cwd == project_root:
        return True
    return cwd.startswith(project_root.rstrip("/") + "/")


def _prefilter_safe(query: str) -> bool:
    """The raw-bytes prefilter is only a guaranteed superset of matches_query
    for queries whose characters appear verbatim in the JSONL. JSON escapes
    quotes, backslashes, and (when ensure_ascii) non-ASCII chars, so skip the
    prefilter for those and fall back to a full scan."""
    return query.isascii() and '"' not in query and "\\" not in query


def parse_codex_session(fpath: Path, search_all: bool, project_root: str,
                        include_subagents: bool, need_full: bool):
    """Parse a Codex rollout file in one pass.

    Returns (cwd, session_id, preview, user_text_lower), or None when the file
    is skipped early (cwd doesn't match the current project, or it's an excluded
    subagent session). session_meta is the first record, so the project/subagent
    filters short-circuit before the body is read. When ``need_full`` is False
    (no keyword query), parsing stops once the preview is captured.
    """
    cwd = None
    session_id = None
    preview = None
    user_parts = []

    try:
        f = open(fpath, errors="replace")
    except Exception:
        return None

    with f:
        for line in f:
            try:
                d = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue

            t = d.get("type")
            p = d.get("payload") or {}

            if t == "session_meta":
                cwd = p.get("cwd")
                session_id = p.get("id")
                if not include_subagents and p.get("thread_source") == "subagent":
                    return None
                if not search_all and project_root and not _cwd_in_project(cwd, project_root):
                    return None
                continue

            if (t == "response_item" and p.get("type") == "message"
                    and p.get("role") == "user"):
                for item in (p.get("content") or []):
                    if not (isinstance(item, dict)
                            and item.get("type") == "input_text"):
                        continue
                    raw = item.get("text") or ""
                    norm = " ".join(raw.split())
                    if not norm or norm.startswith(CODEX_INJECTION_PREFIXES):
                        continue
                    user_parts.append(norm)
                    if preview is None:
                        preview = norm[:130]

            # Without a keyword query we only need meta + first preview.
            if not need_full and session_id is not None and preview is not None:
                break

    if session_id is None:
        session_id = codex_filename_uuid(fpath)

    # A scoped (current-project) search must match the recorded cwd. This also
    # drops files that never carried a session_meta (cwd is None), which would
    # otherwise bypass the inline filter above and leak in as "(unknown)".
    if not search_all and project_root and not _cwd_in_project(cwd, project_root):
        return None

    # Unresumable without an id (no session_meta and a malformed filename).
    if session_id is None:
        return None

    return cwd, session_id, preview, "\n".join(user_parts).lower()


def codex_prefilter(root: Path, query: str):
    """Return the set of files containing every query term (raw, case-insensitive),
    as a fast superset to avoid fully parsing every transcript. Returns None when
    no usable search tool is available (caller then scans all files)."""
    terms = query.split()
    if not terms:
        return None
    tool = "rg" if shutil.which("rg") else ("grep" if shutil.which("grep") else None)
    if tool is None:
        return None

    candidates = None
    for term in terms:
        if tool == "rg":
            # --no-ignore/--hidden so rg doesn't silently skip files via a stray
            # .gitignore or the hidden-dir heuristic (root lives under ~/.codex).
            cmd = ["rg", "-l", "-i", "-F", "--no-ignore", "--hidden", "--", term, str(root)]
        else:
            cmd = ["grep", "-rliF", "--include=rollout-*.jsonl", "--", term, str(root)]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        except Exception:
            return None
        files = {ln for ln in r.stdout.splitlines() if ln}
        candidates = files if candidates is None else (candidates & files)
        if not candidates:
            break
    return candidates


def search_codex(query: str, search_all: bool, include_subagents: bool) -> list:
    sessions_root = Path.home() / ".codex" / "sessions"
    if not sessions_root.exists():
        return []

    project_root = None if search_all else resolve_project_root()

    candidates = None
    if query and _prefilter_safe(query):
        candidates = codex_prefilter(sessions_root, query)

    results = []
    for fpath in sessions_root.glob("**/rollout-*.jsonl"):
        if candidates is not None and str(fpath) not in candidates:
            continue
        try:
            mtime = fpath.stat().st_mtime
        except Exception:
            continue

        parsed = parse_codex_session(fpath, search_all, project_root,
                                     include_subagents, need_full=bool(query))
        if parsed is None:
            continue
        cwd, session_id, preview, user_text = parsed

        if query and not matches_query(user_text, query):
            continue

        dt = datetime.fromtimestamp(mtime)
        results.append({
            "date": dt,
            "source": "codex",
            "project": Path(cwd).name if cwd else "(unknown)",
            "session_id": session_id,
            "title": None,  # Codex has no /rename — always preview-based
            "preview": preview or "(no message)",
            "path": str(fpath),
            "resume_cmd": f"codex resume {session_id}",
        })
    return results


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


def format_text(results: list, search_all: bool, query: str, max_results: int):
    """Human-readable output."""
    total = len(results)
    shown = results[:max_results]
    scope = "all projects" if search_all else "current project"
    label = f'matching "{query}"' if query else "recent"
    print(f"Found {total} {label} session(s) in {scope}:\n")

    for r in shown:
        if search_all:
            tag = f"[{r['source']} · {r['project']}]  "
        else:
            tag = f"[{r['source']}]  "
        title_line = f'  title: "{r["title"]}"' if r["title"] else f"  {r['preview']}"
        print(f"{r['date'].strftime('%Y-%m-%d %H:%M')}  {tag}{r['session_id']}")
        print(title_line)
        print(f"  {r['resume_cmd']}")
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
                "source": r["source"],
                "project": r["project"],
                "session_id": r["session_id"],
                "title": r["title"],
                "preview": r["preview"] if not r["title"] else None,
                "path": r["path"],
                "untitled": r["title"] is None,
                "resume_cmd": r["resume_cmd"],
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

    include_subagents = "--include-subagents" in args
    args = [a for a in args if a != "--include-subagents"]

    # Source selection: --source claude|codex|both (or --source=codex), plus
    # the shorthand aliases --claude / --codex / --both.
    source = "both"
    cleaned = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--both", "--claude", "--codex"):
            source = a[2:]
            i += 1
            continue
        if a == "--source" and i + 1 < len(args):
            source = args[i + 1].lower()
            i += 2
            continue
        if a.startswith("--source="):
            source = a.split("=", 1)[1].lower()
            i += 1
            continue
        cleaned.append(a)
        i += 1
    args = cleaned
    if source not in ("claude", "codex", "both"):
        source = "both"

    query = " ".join(args).lower()
    config = load_config()
    max_results = config.get("max_results", 20)
    exclude_slugs = set(config.get("exclude_slugs", []))

    results = []
    if source in ("claude", "both"):
        results.extend(search_claude(query, search_all, exclude_slugs))
    if source in ("codex", "both"):
        results.extend(search_codex(query, search_all, include_subagents))

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
