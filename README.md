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
| `/copy:gmail` | Format for Gmail/email (HTML tables) |
| `/copy:gdocs` | Format for Google Docs (Markdown, paste via Edit → Paste from Markdown) |
| `/copy:jira` | Format for Jira Cloud (Markdown) |
| `/copy:cleartext` | Plain text (universal) |
| `/copy:richformat` | Rich Text Format (RTF) for Word, Pages |

**Usage:**
```
/copy:slack                    → Auto-detect what to copy, format for Slack
/copy:slack the summary table  → Copy specific content for Slack
/copy:gmail                    → Auto-detect, format as HTML for email
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

### `/tweet` - Post to X (Twitter)

Post tweets directly from Claude Code. Drafts the text, shows a preview with character count, and asks for approval before posting.

```
/tweet Testing my new tweet skill from Claude Code
/tweet Announce the launch of our new attribution feature
```

**Workflow:**
1. Draft tweet text (or use your text as-is)
2. Preview with character count (max 280)
3. Approve / Edit / Cancel
4. Posts via X API v2, returns tweet URL

**Setup (one-time):**
```bash
pip3 install requests-oauthlib
```
On first run, `/tweet` will pop up native macOS dialogs to store your X API credentials securely in Keychain. Get keys from [developer.x.com](https://developer.x.com) → your app → Keys and Tokens (Consumer Key/Secret + Access Token/Secret with Read+Write permissions).

Alternatively, set env vars in `~/.zshrc`: `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`.

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
