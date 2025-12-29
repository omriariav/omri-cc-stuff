# Releases

## v2.0.0 (2025-12-29)

**Breaking Change:** Restructured `/copy` command into separate format-specific commands.

### New Commands
- `/copy:slack` - Format for Slack
- `/copy:gchat` - Format for Google Chat
- `/copy:gmail` - Format for Gmail/email (HTML)
- `/copy:gdocs` - Format for Google Docs (Markdown)
- `/copy:jira` - Format for Jira Cloud (Markdown)
- `/copy:cleartext` - Plain text
- `/copy:richformat` - Rich Text Format (RTF)

### Changes
- Plugin renamed from `copy-command` to `copy` for cleaner namespacing
- Each format is now a separate command (`/copy:slack` instead of `/copy slack`)
- Jira format updated to use Markdown (Jira Cloud) instead of wiki markup
- All commands accept optional `[what to copy]` argument

### Migration
Old: `/copy slack the table`
New: `/copy:slack the table`

---

## v1.x (2025-12-29)

Initial releases with single `/copy` command and various structural experiments.

- v1.3.0 - Skills-based structure attempt
- v1.2.0 - GitHub sync fixes
- v1.0.0 - Initial plugin release
