---
description: Read a tweet from X (Twitter) by URL or ID and load it into the conversation as markdown.
argument-hint: '<x.com URL or numeric tweet ID> [--json]'
allowed-tools: Bash(python3:*), Read
---

Fetch a single tweet via the X API v2 `GET /2/tweets/:id` endpoint and render it as markdown so the rest of the conversation can act on it (summarize, reply via `/x:tweet`, quote, etc.).

## Workflow

1. **Parse target**: From `$ARGUMENTS`, extract the URL or numeric tweet ID. If the user also asked for raw JSON output (mentions "raw", "as JSON", "--json"), capture that as a separate flag — do not pass `$ARGUMENTS` as a single quoted string, that swallows flags.

2. **Fetch**: Run from the plugin root:
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/read/scripts/read.py <target>
   ```
   Append `--json` as a separate argument when the user asked for raw JSON. The script reuses the same Keychain credentials as `/x:tweet` (service `x-api`).

3. **Present**: The script prints markdown with the tweet's text, author, timestamp, public metrics, any referenced tweets (replied-to / quoted), and media URLs. Show this output verbatim, or summarize depending on what the user asked for.

4. **Follow-up**: If the user wants to reply, hand off to `/x:tweet` and pass the fetched tweet ID for `--reply-to`. The tweet's URL contains the ID after `/status/`.

## Errors

- **Missing credentials**: Run `/x:tweet` once first — it triggers `setup.sh` for native macOS keychain dialogs. Or set env vars: `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`.
- **404**: Tweet was deleted, is from a private account, or never existed. Don't retry.
- **429**: Rate limited. Wait and try again — don't loop.
- **401/403**: Credentials invalid or the account lacks read access for that tweet. Re-run setup.

## Cost

X API v2 Posts read tier is metered. One `/x:read` call ≈ one post read + one user read for the author (~$0.005 + $0.010 on the standard tier as of 2026).
