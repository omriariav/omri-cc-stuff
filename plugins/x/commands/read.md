---
description: Read a tweet from X (Twitter) by URL or ID and load it into the conversation as markdown.
argument-hint: '<x.com URL or numeric tweet ID> [--json]'
allowed-tools: Bash(python3:*), Read
---

Execute the **read** skill: read `${CLAUDE_PLUGIN_ROOT}/skills/read/SKILL.md` and follow its workflow. That file is the single source of truth — target parsing, fetching, long-form-article handling, flags, errors, and cost all live there.

Treat `$ARGUMENTS` as the target (a tweet URL, a `twitter.com/...` link, or a bare numeric ID) plus an optional `--json` flag. Pass the target and `--json` as **separate** arguments, never as one quoted string (that swallows flags). Resolve any script path in the SKILL.md relative to `${CLAUDE_PLUGIN_ROOT}/skills/read/` (e.g. `scripts/read.py` → `${CLAUDE_PLUGIN_ROOT}/skills/read/scripts/read.py`).
