# Omri's Claude Code Stuff

Personal collection of Claude Code commands, skills, and agents.

## Installation

In Claude Code:
```
/plugin → Marketplace → Add → omriariav/omri-cc-stuff
```

## Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `/copy` | `/copy [destination] [what]` | Format & copy output to clipboard |

### `/copy` - Format Output for Destination

Copy data/tables/text to clipboard, formatted for the destination.

```
/copy                     → Clear text, guess what to copy
/copy slack               → Format for Slack
/copy email               → Format for Gmail/email
/copy gchat               → Format for Google Chat
/copy jira                → Format for Jira
/copy slack the table     → Format specific content for Slack
```

**Features:**
- Auto-detects what to copy from conversation context
- ASCII tables for Slack & GChat (they don't render markdown tables)
- HTML tables for email
- QuickChart URL generation for numeric data
- Numbers auto-formatted (e.g., 2.45M not 2450000)

**Example:**
```
You: Compare the top programming languages

Claude: | Language   | Stars  | Growth |
        |------------|--------|--------|
        | Python     | 142K   | +18%   |
        | JavaScript | 128K   | +12%   |
        | Rust       | 89K    | +31%   |

You: /copy slack

Claude: ✓ Copied to clipboard (format: Slack)
```

## Contributing

Contributions welcome! Feel free to open a PR or issue.

## License

Free to use with attribution. Credit: [Omri Ariav](https://github.com/omriariav)
