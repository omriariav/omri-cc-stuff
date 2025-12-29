---
description: Copy to clipboard for Jira Cloud (Markdown). Specify what to copy, or auto-detects from context.
argument-hint: [what to copy]
---

# /copy:jira - Format for Jira Cloud

Copy data/tables/text to clipboard, formatted as Markdown for Jira Cloud.

**$ARGUMENTS** = `[what to copy]` (optional - if not specified, finds most recent output)

## Workflow

1. **Find content**: If specified in arguments, find that content. Otherwise, find most recent table/data/output.
2. **Format as Markdown for Jira Cloud**
3. **Copy to clipboard**: `pbcopy`
4. **Confirm**: Show preview

## Jira Cloud Formatting Rules (Markdown)

- Tables: Standard Markdown table syntax
- Bold: `**text**`
- Italic: `*text*`
- Code: `` `code` `` or triple backticks for blocks
- Links: `[text](url)`
- Headers: `# H1`, `## H2`, etc.

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
✓ Copied to clipboard (format: Jira Cloud Markdown)

Preview:
[first 5-10 lines of copied content]
```
