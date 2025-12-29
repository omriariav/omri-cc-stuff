---
description: Copy to clipboard for Google Docs (Paste from Markdown). Specify what to copy, or auto-detects from context.
argument-hint: [what to copy]
---

# /copy:gdocs - Format for Google Docs

Copy data/tables/text to clipboard, formatted for Google Docs.

**$ARGUMENTS** = `[what to copy]` (optional - if not specified, finds most recent output)

## Workflow

1. **Find content**: If specified in arguments, find that content. Otherwise, find most recent table/data/output.
2. **Format as Markdown for Google Docs**
3. **Copy to clipboard**: `pbcopy`
4. **Confirm**: Show preview and remind user to use "Paste from Markdown"

## Google Docs Formatting Rules

- Full Markdown formatting (tables, bold, links, headers)
- User pastes via **Edit → Paste from Markdown**
- Tables as Markdown `| col |` syntax
- Bold: `**text**`
- Links: `[text](url)`

## Markdown Table Format

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |
```

## Number Formatting

Always format numbers for readability:
- `2450000` → `$2.45M`
- `15.7894` → `15.8%`
- `1247` → `1,247`

## Output

After copying, show:
```
✓ Copied to clipboard (format: Google Docs Markdown)

Paste using: Edit → Paste from Markdown

Preview:
[first 5-10 lines of copied content]
```
