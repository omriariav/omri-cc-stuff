# Releases

## x v2.1.2 (2026-05-27)

Maintenance — no behavior change.

- `/x:read` and `/x:tweet` command files collapsed into **thin pointers** to their respective `skills/<name>/SKILL.md`. The skills are now the single source of truth for both commands; the previously duplicated workflow prose (which had to be hand-synced on every change, e.g. the v2.1.1 URL-counting fix) is gone. Commands instruct the model to resolve `scripts/...` paths relative to the skill directory.

## gdoc-math v1.0.2 (2026-05-27)

Maintenance — no behavior change.

- Trimmed the `SKILL.md` frontmatter `description` (dropped redundant trigger examples and verbose NOT-for clauses) to cut always-loaded prompt-budget cost. All trigger phrases preserved.

## skill-reviewer v1.0.1 (2026-05-27)

Maintenance — no behavior change.

- Trimmed the `SKILL.md` frontmatter `description` (dropped the inline dimension list — documentation, not a trigger) to reduce always-loaded prompt-budget cost.

## claude-reviewer v1.1.1 (2026-05-27)

Maintenance — no behavior change.

- Trimmed the `SKILL.md` frontmatter `description` (dropped the rubric-stats clause) to reduce always-loaded prompt-budget cost. Trigger phrases unchanged.

## copy v2.3.1 (2026-05-27)

Maintenance — no behavior change.

- Removed an orphaned legacy unified-router command (`.claude/commands/copy.md`) that sat in a non-loading location and duplicated the eight split `/copy:*` commands. No effect on the active command surface.

## gdoc-math v1.0.1 (2026-05-25)

Docs/example only — no pipeline changes.

- **Bundled example swapped** to a general math showcase: `examples/math-demo.md` (quadratic formula, Euler's identity, finite + geometric series, the derivative limit, the Gaussian integral, Pythagoras). Replaces the ML-specific `laplace-smoothing.md` sample so the demo reads as broadly recognizable math.
- `SKILL.md` and `README.md` updated to point at the new sample.

## gdoc-math v1.0.0 (2026-05-25)

New plugin. `/gdoc-math` converts a Markdown file containing LaTeX math into a **native Google Doc whose equations are real, editable equation objects** — solving the gap that `/copy:gdocs` (Paste from Markdown) and Google's own "Export to Docs" can't: both leave `$...$` / `$$...$$` as literal text.

### How it works
```
markdown+LaTeX  →[pandoc]→  .docx (OMML)  →[gws drive upload + convert --to docs]→  Google Doc
                                                                └─ intermediate .docx auto-trashed
```
pandoc renders LaTeX into Office MathML; Google Drive imports OMML as native, editable equations. Verified by round-tripping the converted Doc back to `.docx` — equations return as `m:oMath` objects with zero embedded images.

### Features
- Inline (`$…$`), display (`$$…$$`), and `\(…\)` / `\[…\]` math.
- Input modes: a `.md` file path, inline content, or the last math-bearing content in the conversation.
- `--name` (Doc title), `--folder` (target Drive folder), `--keep-docx` (debug).
- Optional `default_folder_id` in `config.json`; empty by default (My Drive root), never required.
- Ships a runnable sample at `examples/laplace-smoothing.md`.

### Requirements (verified by `verify-setup.sh` at Step 0)
- `pandoc` — `brew install pandoc`
- `python3` — parses `gws` output (default on macOS)
- `gws` ([Google Workspace CLI](https://github.com/omriariav/workspace-cli)), authenticated for Drive — `go install github.com/omriariav/workspace-cli/cmd/gws@latest`, then `gws auth login`

### Notes
- Simple fractions/subscripts/Greek round-trip cleanly; complex LaTeX (stacked fractions, matrices, large operators) can lose fidelity on Google's import and may need a touch-up.
- Kept standalone (not folded into `copy`) on purpose: it writes to Google Drive over the network with external dependencies — a different contract from `copy`'s instant, offline, clipboard-only commands.

## copy v2.3.0 (2026-05-04)

`/copy:slack` now produces a **native Slack table** on paste when the resolved content is just a table.

### New
- **Native Slack table paste (table-only path)** — When the content is a bare table, `/copy:slack` puts a Google-Sheets-flavored payload on the macOS pasteboard: `public.utf8-plain-text` carries TSV, and `public.html` carries a `<table>` wrapped with `<google-sheets-html-origin>` and `data-sheets-root="1"`. Slack's composer recognizes that exact shape and converts the paste into a real native table block — same render as a bot posting via the Block Kit `table` API.
- New `## Native Table Paste` section in `commands/slack.md` with the full TSV + HTML + JXA `NSPasteboard` recipe (plain `pbcopy` is not enough for this path).

### Changed
- **Router** (`/copy slack`): step 4 of the workflow now branches Slack into table-only (JXA path) vs mixed/prose (`pbcopy`); the destination rules and the example explicitly call out the same branch so a model following either prompt can't fall back to plain text and silently break native rendering.
- Mixed/prose Slack guidance (bold, links, QuickChart) is now scoped to the mixed path. Adding any prose or chart URL to the table-only path would convert the paste into mixed content and Slack would drop the native render — the docs spell this out.

### Why "table-only"?
Slack's composer recognizes the Sheets-flavored clipboard only when the paste is a table. Add prose around the table and Slack falls back to plain text. For prose + native table together, the realistic options are:
- Two pastes (prose first, table-only second), or
- Use a Slack MCP / webhook that posts via `chat.postMessage` with a Block Kit `table` block.

End users still cannot construct a native table block in the composer manually — that's a Slack platform constraint, not a plugin gap.

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

## copy v2.2.2 (2026-04-29)

Bugfix: `/copy:slack` now emits Markdown `[text](url)` links instead of Slack's `<url|text>` Block Kit syntax.

### Fixed
- **Slack**: Links use Markdown `[text](url)` — renders as a hyperlink in the composer when "Format messages with markup" is enabled in Slack preferences. The previous `<url|text>` form is API/`mrkdwn` syntax and renders literally in the composer. Raw URLs remain a safe fallback (Slack auto-unfurls them). (#6)
- Router (`/copy slack`) updated to match.

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
