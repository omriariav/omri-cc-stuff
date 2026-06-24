---
name: find-session
description: Search past Claude Code AND Codex conversations by keyword and return session IDs for resuming. Use when the user asks to find, locate, or look for a past/previous conversation, or needs a session ID to resume a conversation with claude --resume or codex resume. NOT for searching within a conversation (use /reflect), NOT as a replacement for the resume command itself.
argument-hint: [--all] [--json] [--source claude|codex|both] [--include-subagents] [keywords...]
allowed-tools: Bash(python3*), AskUserQuestion
user-invocable: true
---

# Find Session

Search session JSONL files for keyword matches and present session IDs. Covers
two sources: **Claude Code** (`~/.claude/projects/<slug>/<uuid>.jsonl`) and
**Codex** (`~/.codex/sessions/<Y>/<M>/<D>/rollout-<ts>-<uuid>.jsonl`). Each
result is tagged with its source and the correct resume command.

## Step 1: Run the search

Run (relative to the skill base directory shown above):

```bash
python3 scripts/find_session.py [--all] [--json] [--source claude|codex|both] [--include-subagents] KEYWORDS
```

- Default: searches the current project's sessions only (fast, no noise), **both sources**
- `--all` (or `-all`): searches across all projects and shows `[source · project]` labels
- `--source claude|codex|both`: limit to one source (default `both`)
- `--include-subagents`: include Codex subagent sessions (guardian auto-review judges, spawned children) — excluded by default as non-resumable noise
- `--json`: outputs structured JSON (useful for programmatic follow-up); error paths also return JSON

Replace `KEYWORDS` with the user's search terms (space-separated). Omit keywords to list the most recent sessions. Always shell-quote arguments that contain special characters.

The current-project scope resolves the project root via git (or cwd). Claude sessions are matched by directory slug; Codex sessions are matched by the `cwd` recorded in each transcript's `session_meta`.

## Step 2: Check for Haiku summarization

Read `config.json` and check the `# UNTITLED_COUNT=N TOTAL_SHOWN=M` hint line on stderr.

1. Is `use_haiku_summary` true in config.json? If no → skip to Step 3.
2. Is `UNTITLED_COUNT >= 2`? If no → skip to Step 3.
3. Is `TOTAL_SHOWN <= haiku_threshold`? If no → skip to Step 3.
4. All conditions met → use `AskUserQuestion` to ask: "N untitled sessions found. Summarize them with Haiku before showing results?"
5. If user agrees:
   a. Re-run the script with `--json` to get session file paths (and the `source` of each).
   b. Spawn a single subagent (model: read `haiku_model` from config.json) to summarize each untitled session. For **claude** sessions, read the first 15 messages of the JSONL. For **codex** sessions, the first lines are mostly injected boilerplate (`session_meta`, `# AGENTS.md`, `<environment_context>`) — the `--json` `preview` field already holds the first real user message, so prefer it (or read past the injected `role: user` records). Return a one-line summary per session.
   c. Present all results as a table: date | source | project | session ID | title or summary | resume command. Use the per-result `resume_cmd` from `--json` (`claude --resume <id>` vs `codex resume <id>`). Mark Haiku-generated summaries in italics.
6. If user declines → go to Step 3.

## Step 3: Present results

Show the script output as-is. Each result already prints its own resume line — `claude --resume <id>` for Claude sessions, `codex resume <id>` for Codex sessions. The user copies the matching line to resume.

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

**`--all` noise** — claude-mem observer directories are auto-skipped. Use `exclude_slugs` in `config.json` to skip any other noisy project dirs by their exact `~/.claude/projects/` slug name. (Codex subagent sessions are excluded separately via the `--include-subagents` toggle.)

**Codex sessions are always "untitled"** — Codex has no `/rename`, so every Codex result is shown by preview (first real user message), never a title. Expect the Haiku-summarization branch (Step 2) to trigger more often once Codex results are in the mix.

**Codex preview skips injected boilerplate** — Codex records `# AGENTS.md`, `<environment_context>`, `<skill>`, `<turn_aborted>`, and `<<ccr:` blocks as `role: user`. These are filtered from both the preview and keyword matching, so matches reflect genuine user input — not injected context. amq-squad agent bootstraps ("You are a fresh amq-squad agent…") are kept, as they identify the session's role/workstream.

**Codex resume command differs** — resume Codex sessions with `codex resume <uuid>` (UUID = the trailing id in the `rollout-…` filename, which equals `payload.id`), not `claude --resume`. Each result prints the correct command.

**`--all` keyword search reads every transcript** — across all projects that is ~12k Claude files plus ~1k Codex files, so expect a few seconds. A `ripgrep`/`grep` pre-filter narrows the Codex scan when a query is present (falls back to a full scan if neither tool is installed). The default current-project scope stays fast (~1s) because Codex files are skipped by `cwd` after reading only their first line.
