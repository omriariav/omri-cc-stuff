# Omri's Claude Code Stuff

Personal collection of Claude Code commands and utilities.

## Installation

In Claude Code:
```
/plugins → Marketplace → Add → omriariav/omri-cc-stuff
```

Then install the `copy` plugin from the marketplace.

## Commands

### `/copy:*` - Format & Copy to Clipboard

Copy data/tables/text to clipboard, formatted for your destination.

| Command | Description |
|---------|-------------|
| `/copy:slack` | Format for Slack (ASCII tables, `*bold*`) |
| `/copy:gchat` | Format for Google Chat (same as Slack) |
| `/copy:gmail` | Format for Gmail/email (rich text paste) |
| `/copy:gdocs` | Format for Google Docs (Markdown, paste via Edit → Paste from Markdown) |
| `/copy:jira` | Format for Jira Cloud (Markdown) |
| `/copy:md` | Markdown (standard syntax) |
| `/copy:cleartext` | Plain text (universal) |
| `/copy:richformat` | Rich Text Format (RTF) for Word, Pages |

**Usage:**
```
/copy:slack                    → Auto-detect what to copy, format for Slack
/copy:slack the summary table  → Copy specific content for Slack
/copy:gmail                    → Auto-detect, format as rich text for email
```

**Features:**
- Auto-detects what to copy from conversation context
- Formats text, tables, lists, code, summaries
- Numbers auto-formatted (e.g., `$2.45M` not `2450000`)
- QuickChart URLs for numeric data visualization

**Example:**
```
You: Compare the top programming languages

Claude: | Language   | Stars  | Growth |
        |------------|--------|--------|
        | Python     | 142K   | +18%   |
        | JavaScript | 128K   | +12%   |
        | Rust       | 89K    | +31%   |

You: /copy:slack

Claude: ✓ Copied to clipboard (format: Slack)
```

### `/x` - Post and Read on X (Twitter)

Two skills under one plugin, sharing the same X API credentials.

#### `/x:tweet` - Post

Post tweets directly from Claude Code. Drafts the text, shows a preview with character count, and asks for approval before posting. Learns your voice over time from editing patterns and feedback.

```
/x:tweet Testing my new tweet skill from Claude Code
/x:tweet Announce the launch of our new attribution feature
```

**Workflow:**
1. Draft tweet text (or use your text as-is)
2. Preview with character count (max 280)
3. Approve / Edit / Cancel
4. Posts via X API v2, returns tweet URL

#### `/x:read` - Read

Fetch a tweet by URL or ID via the X API v2 and load it into the conversation as markdown — with author, timestamp, metrics, replied-to / quoted context, and media. Useful for "summarize this thread", "draft a reply to this", or quoting a tweet in another piece of writing.

```
/x:read https://x.com/jack/status/20
/x:read 20
```

Hand the resulting tweet ID to `/x:tweet --reply-to <id>` to chain a reply. Note: each read is metered by X (~$0.005 / post read on the standard tier).

**Setup (one-time):**
```bash
pip3 install requests-oauthlib
```
On first run, `/x:tweet` will pop up native macOS dialogs to store your X API credentials securely in Keychain (`/x:read` reuses the same credentials). Get keys from [developer.x.com](https://developer.x.com) → your app → Keys and Tokens (Consumer Key/Secret + Access Token/Secret with Read+Write permissions).

Alternatively, set env vars in `~/.zshrc`: `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`.

### `/skill-reviewer` - Skill Design Evaluation

Evaluate any skill's design quality against [best practices](https://x.com/trq212/status/2033949937936085378). Scores 10 dimensions (29-point rubric), detects anti-patterns, and optionally applies safe fixes.

```
/skill-reviewer publisher-lookup          → Review by skill name
/skill-reviewer --fix my-skill            → Review + auto-apply safe fixes
/skill-reviewer --compare skill-a skill-b → Side-by-side comparison
```

**Dimensions scored:** Progressive Disclosure, Description Quality, Gotchas, Non-Obvious Content, Flexibility, Setup & Config, Memory, Scripts, Frontmatter, Hooks Integration.

**Grades:** A (25-29), B (20-24), C (15-19), D (10-14), F (0-9)

### `/find-session` - Search Past Conversations

Search past Claude Code session history by keyword and get `claude --resume` commands to pick up where you left off.

```
/find-session deploy                → Search current project for "deploy"
/find-session --all taboola         → Search across all projects
/find-session --all --json auth     → Structured JSON output
```

**Features:**
- Searches user messages and custom titles (not assistant text)
- Word-boundary matching for clean terms, literal match for punctuation (`claude-mem`, `c++`)
- Shows custom title (from `/rename`) when set, falls back to first message preview
- Optional Haiku summarization for untitled sessions (asks before running)
- `--json` mode for programmatic use
- Git-aware project root resolution (works from subdirectories)

**Configuration** (`config.json`):
| Setting | Default | Description |
|---------|---------|-------------|
| `max_results` | 20 | Max sessions to show |
| `use_haiku_summary` | true | Enable Haiku summarization prompt |
| `haiku_threshold` | 50 | Max results for Haiku to trigger |
| `haiku_model` | `claude-haiku-4-5-20251001` | Model for summarization |
| `exclude_slugs` | `[]` | Project slugs to skip in `--all` mode |

### `/claude-reviewer` - Claude Code Configuration Auditor

Review any project's `.claude/` folder setup against [best practices](https://x.com/akshay_pachaar/status/2035341800739877091). Scores 8 dimensions (24-point rubric), detects anti-patterns, and produces an actionable improvement report.

```
/claude-reviewer                       → Review current project
/claude-reviewer ~/Code/myproject      → Review specific project
/claude-reviewer --global              → Review only ~/.claude/ global config
```

**Dimensions scored:** CLAUDE.md Quality, Permission Hygiene, Modular Instructions, Custom Commands, Skills Setup, Agent Configuration, Git Hygiene, Progressive Disclosure.

**Grades:** A (21-24), B (16-20), C (11-15), D (6-10), F (0-5)

## Other Commands

| Command | Description |
|---------|-------------|
| `/setup-pulse` | Install [claude-pulse](https://github.com/omriariav/claude-pulse) statusline |

### `/setup-pulse` - Install Token Usage Statusline

Installs [claude-pulse](https://github.com/omriariav/claude-pulse) - shows real-time context usage in your statusline.

```
/setup-pulse
```

After running, you'll see: `72k/200k (36%)` with color-coded warnings (green/yellow/red).

## Contributing

Contributions welcome! Feel free to open a PR or issue.

## License

Free to use with attribution. Credit: [Omri Ariav](https://github.com/omriariav)
