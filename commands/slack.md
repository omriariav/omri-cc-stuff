---
description: Copy to clipboard for Slack. Specify what to copy, or auto-detects from context.
argument-hint: [what to copy]
---

# /copy:slack - Format for Slack

Copy data/tables/text to clipboard, formatted for Slack.

**$ARGUMENTS** = `[what to copy]` (optional - if not specified, finds most recent output)

## Workflow

1. **Find content**: If specified in arguments, find that content. Otherwise, find most recent table/data/output.
2. **Format for Slack**
3. **Copy to clipboard**: `pbcopy`
4. **Confirm**: Show preview

## Slack Formatting Rules

- Tables in triple backticks (```) with ASCII art (│ and ─)
- Bold: single `*text*`
- Links: `<url|text>`
- Generate QuickChart URL for numeric comparisons

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

## QuickChart

Generate chart URL when data has numeric comparisons:
```python
import json, urllib.parse
config = {"type": "bar", "data": {"labels": [...], "datasets": [{"data": [...]}]}}
url = f"https://quickchart.io/chart?c={urllib.parse.quote(json.dumps(config))}&w=600&h=400"
```

## Output

After copying, show:
```
✓ Copied to clipboard (format: Slack)

Preview:
[first 5-10 lines of copied content]
```
