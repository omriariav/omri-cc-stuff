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
