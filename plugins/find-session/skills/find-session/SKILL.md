---
name: find-session
description: Search past Claude Code conversations by keyword and return session IDs for resuming. Use when the user asks to find, locate, or look for a past/previous conversation, or needs a session ID to resume a conversation with claude --resume. NOT for searching within a conversation (use /reflect), NOT as a replacement for claude --resume itself.
argument-hint: [--all] [keywords...]
allowed-tools: Bash(python3*)
user-invocable: true
---

# Find Session

Search session JSONL files for keyword matches and present session IDs.

Run (relative to the skill base directory shown above):

```bash
python3 scripts/find_session.py [--all] KEYWORDS
```

- Default: searches the current project's sessions only (fast, no noise)
- `--all`: searches across all `~/.claude/projects/` and shows `[project]` labels

Replace `KEYWORDS` with the user's search terms (space-separated). Omit keywords to list the most recent sessions.

**Before presenting results**, check the `# UNTITLED_COUNT=N TOTAL_SHOWN=M` hint line at the end of the script output and `config.json`:
- If `use_haiku_summary` is true (default) AND `UNTITLED_COUNT >= 2` AND `TOTAL_SHOWN <= haiku_threshold` (default 50): **ask the user** if they want Haiku to summarize the untitled sessions before you show the list. If they agree, spawn a single subagent (model: `claude-haiku-4-5-20251001`) to read the first 15 messages of each untitled session and return a one-line summary per session. Then present the full results as a table: date | session ID | summary | `claude --resume` command.
- If the user declines, or conditions aren't met: present the script output as-is. The user copies the `claude --resume [id]` line to resume.

If the script exits with an error or prints "No sessions found", check that the working directory is inside a Claude Code project. Then fall back to `mcp__plugin_claude-mem_mcp-search__search` with the same query for semantic matching.

## Gotchas

**Empty results despite valid keywords** - The script searches `~/.claude/projects/<cwd-slug>/`. If run from outside the project root, the slug won't match and all results will be empty. Confirm `os.getcwd()` maps to the right project.

**Compacted sessions missing content** - Old sessions may have been compacted (summarized). The JSONL may no longer contain the original user messages verbatim, so keyword search will miss them. Use `mcp__plugin_claude-mem_mcp-search__search` as fallback for older sessions.

**Multiple projects** - The script only searches the current project's sessions. Sessions from other projects (e.g. `omri-cc-stuff`) won't appear. Tell the user to run `/find-session` from that project's directory if needed.

**`--all` noise** - claude-mem observer directories are auto-skipped. Use `exclude_slugs` in `config.json` to skip any other noisy project dirs by their exact `~/.claude/projects/` slug name.
