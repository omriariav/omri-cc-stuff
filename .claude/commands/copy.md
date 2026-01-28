---
description: Format and copy output to clipboard. Guesses what to copy from context. Optional destination (slack/email/gchat/jira/gdocs) and what to copy.
argument-hint: "[destination] [what to copy]"
---

# /copy - Format Output for Destination

Copy data/tables/text to clipboard, formatted for the destination.

## Arguments (all optional)

```
/copy                     → Clear text, guess what to copy
/copy slack               → Format for Slack
/copy email               → Format for Gmail/email
/copy gchat               → Format for Google Chat
/copy gdocs               → Format for Google Docs
/copy jira                → Format for Jira
/copy slack the summary   → Format specific content for Slack
/copy the findings        → Clear text, copy specific content
```

**$ARGUMENTS** = `[destination] [what to copy]`

- If no destination: output clear text (universal)
- If no "what to copy": find most recent table/data/output in conversation

## Workflow

1. **Parse arguments**: Extract destination (if any) and content reference (if any)
2. **Find content**:
   - If content specified → find that specific content in conversation
   - If not specified → find most recent table, data, or significant output
3. **Format for destination** (or clear text if none specified)
4. **Copy to clipboard**:
   - **Email**: Write HTML to temp file → `textutil` convert to RTF → `osascript` to copy RTF (rich text paste)
   - **All others**: `pbcopy` (plain text)
5. **Confirm**: Show preview of what was copied

## Destination Formatting Rules

### Clear Text (default - no destination)
- Plain text, no special formatting
- Tables as simple aligned columns
- Numbers formatted readably ($2.45M not 2450000)
- Universal - works anywhere

### Slack
- Tables in triple backticks (```) with ASCII art (│ and ─)
- Bold: single `*text*`
- Links: `<url|text>`
- Generate QuickChart URL for numeric comparisons

### GChat (Google Chat)
- **Same as Slack** - GChat doesn't render markdown tables
- Tables in triple backticks with ASCII art (│ and ─)
- Bold: `*text*`
- No image embedding - use URL link instead

### Email (Gmail)
- HTML `<table>` with inline styles
- Bold: `<b>` tags
- Embed chart as `<img src="QuickChart URL">`
- **IMPORTANT: Rich text copy** — Gmail pastes raw HTML as text. You MUST copy as rich text:
  1. Write HTML to a temp file (e.g., `/tmp/claude-email.html`)
  2. Convert to RTF: `textutil -convert rtf -inputencoding UTF-8 /tmp/claude-email.html -output /tmp/claude-email.rtf`
  3. Copy RTF to clipboard: `osascript -e 'set the clipboard to (read (POSIX file "/tmp/claude-email.rtf") as «class RTF »)'`
- Do NOT use `pbcopy` for email — it copies plain text only

### Jira
- Tables: `||header||` and `|cell|`
- Bold: `*text*`
- Image: `!url!`

### Google Docs (gdocs)
- Full Markdown formatting (tables, bold, links, headers)
- User pastes via **Edit → Paste from Markdown**
- Tables as Markdown `| col |` syntax
- Bold: `**text**`
- Links: `[text](url)`

## ASCII Table Format (Slack & GChat)

```
*Title*

```
Column 1     │ Column 2  │ Column 3
─────────────┼───────────┼──────────
Value 1      │ Value 2   │ Value 3
Value 4      │ Value 5   │ Value 6
```
```

## Content Detection Priority

When guessing what to copy, look for (in order):
1. Most recent table/data output
2. Most recent code block
3. Most recent bulleted list
4. Most recent structured content
5. Summary or key findings

## Number Formatting

Always format numbers for readability:
- `2450000` → `$2.45M`
- `15.7894` → `15.8%`
- `1247` → `1,247`

## QuickChart (for Slack/Email only)

Generate chart URL when data has numeric comparisons:
```python
import json, urllib.parse
config = {"type": "bar", "data": {"labels": [...], "datasets": [{"data": [...]}]}}
url = f"https://quickchart.io/chart?c={urllib.parse.quote(json.dumps(config))}&w=600&h=400"
```

## Examples

### `/copy`
Find last output, copy as clear text.

### `/copy slack`
Find last output, format for Slack with ASCII table + chart URL.

### `/copy gchat`
Find last output, format same as Slack (ASCII table in code block).

### `/copy gdocs`
Find last output, format as Markdown. User pastes via Edit → Paste from Markdown.

### `/copy the summary`
Find "summary" in conversation, copy as clear text.

### `/copy email the comparison`
Find "comparison", format as HTML table for email.

## Output

After copying, show:
```
✓ Copied to clipboard (format: [destination or "clear text"])

Preview:
[first 5-10 lines of copied content]
```
