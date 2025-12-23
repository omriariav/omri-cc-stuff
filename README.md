# Omri's Claude Code Stuff

Personal collection of Claude Code commands, skills, and agents.

## Installation

```bash
# Clone the repo
git clone https://github.com/omriariav/omri-cc-stuff.git ~/Code/omri-cc-stuff

# Symlink commands (add to your ~/.claude/)
ln -s ~/Code/omri-cc-stuff/commands ~/.claude/commands
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
- Numbers auto-formatted ($2.45M not 2450000)

## License

MIT
