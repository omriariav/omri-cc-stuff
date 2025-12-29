---
description: Copy to clipboard for Gmail/email (HTML). Specify what to copy, or auto-detects from context.
argument-hint: [what to copy]
---

# /copy:gmail - Format for Gmail/Email

Copy data/tables/text to clipboard, formatted as HTML for Gmail.

**$ARGUMENTS** = `[what to copy]` (optional - if not specified, finds most recent output)

## Workflow

1. **Find content**: If specified in arguments, find that content. Otherwise, find most recent table/data/output.
2. **Format as HTML for email**
3. **Copy to clipboard**: `pbcopy`
4. **Confirm**: Show preview

## Email/Gmail Formatting Rules

- HTML `<table>` with inline styles
- Bold: `<b>` tags
- Embed chart as `<img src="QuickChart URL">`

## HTML Table Format

```html
<table style="border-collapse: collapse; font-family: Arial, sans-serif;">
  <tr style="background-color: #f2f2f2;">
    <th style="border: 1px solid #ddd; padding: 8px;">Column 1</th>
    <th style="border: 1px solid #ddd; padding: 8px;">Column 2</th>
  </tr>
  <tr>
    <td style="border: 1px solid #ddd; padding: 8px;">Value 1</td>
    <td style="border: 1px solid #ddd; padding: 8px;">Value 2</td>
  </tr>
</table>
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

Embed as: `<img src="[chart url]" alt="Chart">`

## Output

After copying, show:
```
✓ Copied to clipboard (format: HTML for Email)

Preview:
[first 5-10 lines of copied content]
```
