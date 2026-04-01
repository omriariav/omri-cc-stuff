---
name: find-session
description: Search past Claude Code conversations by keyword and return session IDs for resuming. Use when the user asks to find, locate, or look for a past/previous conversation, or needs a session ID to resume a conversation with claude --resume. NOT for searching within a conversation (use /reflect), NOT as a replacement for claude --resume itself.
argument-hint: [--all] [--json] [keywords...]
allowed-tools: Bash(python3*), AskUserQuestion
user-invocable: true
---

# Find Session

Search session JSONL files for keyword matches and present session IDs.

## Step 1: Run the search

Run (relative to the skill base directory shown above):

```bash
python3 scripts/find_session.py [--all] [--json] KEYWORDS
```

- Default: searches the current project's sessions only (fast, no noise)
- `--all`: searches across all `~/.claude/projects/` and shows `[project]` labels
- `--json`: outputs structured JSON (useful for programmatic follow-up)

Replace `KEYWORDS` with the user's search terms (space-separated). Omit keywords to list the most recent sessions. Always shell-quote arguments that contain special characters.

## Step 2: Check for Haiku summarization

Read `config.json` and check the `# UNTITLED_COUNT=N TOTAL_SHOWN=M` hint line at the end of the script output.

1. Is `use_haiku_summary` true in config.json? If no → skip to Step 3.
2. Is `UNTITLED_COUNT >= 2`? If no → skip to Step 3.
3. Is `TOTAL_SHOWN <= haiku_threshold`? If no → skip to Step 3.
4. All conditions met → use `AskUserQuestion` to ask: "N untitled sessions found. Summarize them with Haiku before showing results?"
5. If user agrees:
   a. Re-run the script with `--json` to get session file paths.
   b. Spawn a single subagent (model: read `haiku_model` from config.json) to read the first 15 messages of each untitled session's JSONL file and return a one-line summary per session.
   c. Present all results as a table: date | project | session ID | title or summary | `claude --resume` command. Mark Haiku-generated summaries in italics.
6. If user declines → go to Step 3.

## Step 3: Present results

Show the script output as-is. The user copies the `claude --resume [id]` line to resume.

## Error handling

If the script prints "No matching sessions found" or "No session directory found":
1. Confirm the working directory is inside a Claude Code project.
2. Suggest the user try `--all` to search across all projects.
3. For older sessions that may have been compacted, suggest the user try semantic search with claude-mem if available.

## Gotchas

**Empty results despite valid keywords** — The script resolves the project root via `git rev-parse --show-toplevel` (falls back to cwd). If run outside a git repo, it uses cwd directly. Confirm the resolved path maps to the right `~/.claude/projects/` slug.

**Compacted sessions missing content** — Old sessions may have been compacted (summarized). The JSONL may no longer contain the original user messages verbatim, so keyword search will miss them.

**Stale titles after /rename** — The script uses the *latest* custom-title in the JSONL, not the first. If a session was renamed multiple times, the most recent name is shown.

**Punctuation in search terms** — Terms like "claude-mem" are matched as literal substrings. Plain alphanumeric terms use word-boundary matching. Hyphenated terms work as a single phrase, not split into parts.

**`--all` noise** — claude-mem observer directories are auto-skipped. Use `exclude_slugs` in `config.json` to skip any other noisy project dirs by their exact `~/.claude/projects/` slug name.
