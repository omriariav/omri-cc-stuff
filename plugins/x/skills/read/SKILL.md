---
name: read
description: |
  Read a tweet from X (Twitter) by URL or ID and load it into the conversation.
  Use when user says "/x:read <url>", "read this tweet", "what does this tweet say", or pastes an x.com / twitter.com status link and wants to discuss, summarize, or reply to it.
  NOT for posting (use /x:tweet), timelines, search, analytics, or DMs.
argument-hint: '<x.com URL or numeric tweet ID> [--json]'
allowed-tools: Bash(python3*), Read
user-invocable: true
---

# Read - Fetch a Tweet via X API

Fetch a single tweet via the X API v2 `GET /2/tweets/:id` endpoint and render it as markdown so the rest of the conversation can act on it (summarize, reply via `/x:tweet --reply-to`, quote, etc.).

## Workflow

1. **Parse target**: From `$ARGUMENTS`, extract the URL or numeric tweet ID as a single positional argument, and capture any `--json` (or natural-language equivalent like "raw" / "as JSON") as a separate flag. Accepted target forms: `https://x.com/<user>/status/<id>`, `twitter.com/...`, or a bare numeric ID — the script handles all three.
2. **Fetch**: From this skill's directory, run `python3 scripts/read.py <target>`, appending `--json` as a separate argument when raw output was requested. Do NOT pass `"$ARGUMENTS"` as a single quoted string — that swallows flags. The script reuses the same Keychain credentials as `/x:tweet` (service `x-api`).
3. **Present**: The script prints markdown with the tweet's text, author, timestamp, public metrics, any referenced tweets (replied-to / quoted), and media URLs. Show this output to the user verbatim or summarize it depending on what they asked for.
4. **Follow-up**: If the user wants to reply, hand off to `/x:tweet` with the tweet ID for `--reply-to`. The fetched tweet's URL contains the ID after `/status/`.

## Flags

- `--json` — print the raw API payload instead of markdown. Use when the user asks for raw data, full entities, or fields the markdown view drops.

## Errors

- **Missing credentials**: Direct user to run `/x:tweet` once (it triggers `scripts/setup.sh` for native macOS keychain dialogs), or set `X_API_KEY` / `X_API_SECRET` / `X_ACCESS_TOKEN` / `X_ACCESS_TOKEN_SECRET` env vars.
- **404**: Tweet was deleted, is from a private account, or never existed. Don't retry.
- **429**: Rate limited. Wait and try again — don't loop.
- **401/403**: Credentials are invalid or the account lacks read access for that tweet. Re-run setup.

## Cost

X API v2 Posts read tier is billed per resource ($0.005 / post read on the metered tier as of 2026). One `/x:read` call = one post read + (typically) one user read for the author.
