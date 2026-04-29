# Releases

## x v2.0.0 (2026-04-29)

**Breaking change:** plugin renamed `tweet` → `x`. Command `/tweet` is now `/x:tweet`. Update any scripts or muscle memory.

### New
- **`/x:read`** — Fetch a tweet by URL or ID via X API v2 (`GET /2/tweets/:id`) and load it into the conversation as markdown (author, timestamp, public metrics, replied-to / quoted tweets, media). Reuses `/x:tweet` Keychain credentials. Metered by X at ~$0.005 / post read.
- Plugin description updated to cover both posting and reading.

### Changed
- Plugin directory `plugins/tweet/` → `plugins/x/`.
- `plugins/x/.claude-plugin/plugin.json` `name` field is now `x`.
- `marketplace.json` plugin entry renamed and now lists both `./skills/tweet` and `./skills/read`.

### Migration

**If you had the old `tweet` plugin installed**, Claude Code's plugin cache still points at `plugins/tweet/` and `/plugin update` will fail with `Plugin source not found at .../plugins/tweet`. The directory and entry name both moved, so this is a fresh install, not an upgrade.

To migrate:
1. `/plugin` → select `tweet` → **Uninstall**
2. `/plugin` → install `x` from this marketplace
3. Restart Claude Code so the new commands register

Keychain credentials live under service `x-api` and are untouched — `/x:tweet` will pick them up immediately. Just update muscle memory: `/tweet` → `/x:tweet`, and you get `/x:read` for free.

## tweet v1.3.0 (2026-03-30)

Voice learning and skill structure improvements.

### New
- **Voice learning**: Reads `LEARNINGS.json` before drafting to match your established voice, appends observations after each posted tweet
- `config.json` for operational defaults (char target, thread style)
- `references/` directory with extracted char-counting rules and drafting guidelines

### Changed
- Scoped `allowed-tools` to `Bash(python3*), Bash(bash scripts/*)` for security
- Expanded description with negative trigger cases
- Trimmed SKILL.md from 134 to 92 lines via progressive disclosure
- Removed duplicate credential setup and verbose script output sections

## copy v2.2.1 (2026-04-05)

Bugfix: resolve format inconsistencies between router and subcommands.

### Fixed
- **Jira**: Router had stale wiki markup (`||header||`, `*bold*`); now matches `jira.md` Markdown syntax
- **Gmail**: `gmail.md` incorrectly used `pbcopy`; now uses `textutil` → RTF → `osascript` for rich text paste
- **Router**: Added `richformat` and `cleartext` to argument list, examples, and clipboard rules
- **Router**: Renamed `/copy email` → `/copy gmail` for consistency with actual command name

## copy v2.2.0 (2026-03-30)

### New
- `/copy:md` - Copy as standard Markdown (tables, headers, bold, links, code blocks)

---

## v2.0.0 (2025-12-29)

**Breaking Change:** Restructured `/copy` command into separate format-specific commands.

### New Commands
- `/copy:slack` - Format for Slack
- `/copy:gchat` - Format for Google Chat
- `/copy:gmail` - Format for Gmail/email (HTML)
- `/copy:gdocs` - Format for Google Docs (Markdown)
- `/copy:jira` - Format for Jira Cloud (Markdown)
- `/copy:cleartext` - Plain text
- `/copy:richformat` - Rich Text Format (RTF)

### Changes
- Plugin renamed from `copy-command` to `copy` for cleaner namespacing
- Each format is now a separate command (`/copy:slack` instead of `/copy slack`)
- Jira format updated to use Markdown (Jira Cloud) instead of wiki markup
- All commands accept optional `[what to copy]` argument

### Migration
Old: `/copy slack the table`
New: `/copy:slack the table`

---

## v1.x (2025-12-29)

Initial releases with single `/copy` command and various structural experiments.

- v1.3.0 - Skills-based structure attempt
- v1.2.0 - GitHub sync fixes
- v1.0.0 - Initial plugin release
