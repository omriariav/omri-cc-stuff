---
description: Copy to clipboard as Rich Text (RTF). Specify what to copy, or auto-detects from context.
argument-hint: [what to copy]
---

# /copy:richformat - Format as Rich Text (RTF)

Copy data/tables/text to clipboard as Rich Text Format (RTF) for pasting into Word, Pages, etc.

**$ARGUMENTS** = `[what to copy]` (optional - if not specified, finds most recent output)

## Workflow

1. **Find content**: If specified in arguments, find that content. Otherwise, find most recent table/data/output.
2. **Format as RTF**
3. **Copy to clipboard with RTF type**
4. **Confirm**: Show preview

## RTF Formatting

Use `pbcopy` with RTF content type, or generate RTF markup:

```bash
# Copy as RTF on macOS
echo '{\rtf1\ansi Your formatted text here}' | pbcopy -Prefer rtf
```

## RTF Table Format

```rtf
{\rtf1\ansi
\trowd
\cellx3000\cellx6000\cellx9000
\intbl Column 1\cell Column 2\cell Column 3\cell\row
\intbl Value 1\cell Value 2\cell Value 3\cell\row
}
```

## Formatting Elements

- Bold: `\b text\b0`
- Italic: `\i text\i0`
- Tables: `\trowd`, `\cell`, `\row`

## Number Formatting

Always format numbers for readability:
- `2450000` → `$2.45M`
- `15.7894` → `15.8%`
- `1247` → `1,247`

## Output

After copying, show:
```
✓ Copied to clipboard (format: Rich Text/RTF)

Preview:
[first 5-10 lines of copied content]
```
