---
description: Copy to clipboard for Google Chat. Specify what to copy, or auto-detects from context.
argument-hint: [what to copy]
---

# /copy:gchat - Format for Google Chat

Copy data/tables/text to clipboard, formatted for Google Chat.

**$ARGUMENTS** = `[what to copy]` (optional - if not specified, finds most recent output)

## Workflow

1. **Find content**: If specified in arguments, find that content. Otherwise, find most recent table/data/output.
2. **Format for Google Chat**
3. **Copy to clipboard**: `pbcopy`
4. **Confirm**: Show preview

## Google Chat Formatting Rules

- **Same as Slack** - GChat doesn't render markdown tables
- Tables in triple backticks with ASCII art (│ and ─)
- Bold: `*text*`
- No image embedding - use URL link instead

## ASCII Table Format

```
*Title*

```
Column 1     │ Column 2  │ Column 3
─────────────┼───────────┼──────────
Value 1      │ Value 2   │ Value 3
Value 4      │ Value 5   │ Value 6
```
```

## Number Formatting

Always format numbers for readability:
- `2450000` → `$2.45M`
- `15.7894` → `15.8%`
- `1247` → `1,247`

## Output

After copying, show:
```
✓ Copied to clipboard (format: Google Chat)

Preview:
[first 5-10 lines of copied content]
```
