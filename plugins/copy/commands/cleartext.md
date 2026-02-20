---
description: Copy to clipboard as plain text. Specify what to copy, or auto-detects from context.
argument-hint: [what to copy]
---

# /copy:cleartext - Format as Clear Text

Copy data/tables/text to clipboard as plain clear text (universal format).

**$ARGUMENTS** = `[what to copy]` (optional - if not specified, finds most recent output)

## Workflow

1. **Find content**: If specified in arguments, find that content. Otherwise, find most recent table/data/output.
2. **Format as clear text**
3. **Copy to clipboard**: `pbcopy`
4. **Confirm**: Show preview

## Clear Text Formatting Rules

- Plain text, no special formatting
- Tables as simple aligned columns
- Numbers formatted readably ($2.45M not 2450000)
- Universal - works anywhere

## Table Format

```
Column 1      Column 2      Column 3
──────────    ──────────    ──────────
Value 1       Value 2       Value 3
Value 4       Value 5       Value 6
```

## Number Formatting

Always format numbers for readability:
- `2450000` → `$2.45M`
- `15.7894` → `15.8%`
- `1247` → `1,247`

## Content Detection Priority

When guessing what to copy, look for (in order):
1. Most recent table/data output
2. Most recent code block
3. Most recent bulleted list
4. Most recent structured content
5. Summary or key findings

## Output

After copying, show:
```
✓ Copied to clipboard (format: Clear Text)

Preview:
[first 5-10 lines of copied content]
```
