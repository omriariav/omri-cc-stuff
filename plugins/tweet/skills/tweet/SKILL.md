---
name: tweet
description: |
  Post tweets to X (Twitter) from Claude Code.
  Use when user says "/tweet", "post a tweet", "tweet this".
allowed-tools: Bash, Read, AskUserQuestion
argument-hint: [what to tweet about]
---

# Tweet - Post to X (Twitter)

Post tweets from Claude Code via the X API v2.

## Workflow

0. **Setup check**: Run `bash scripts/verify-setup.sh`. If credentials are missing:
   - Run `bash scripts/setup.sh` — this pops up native macOS dialogs for each key (values never pass through the conversation)
   - Tell user to get keys from developer.x.com → app → "Keys and Tokens" if they don't have them yet
   - Re-run verify to confirm, then proceed to step 1
1. **Draft**: Take `$ARGUMENTS` as the tweet prompt. If it's a direct tweet (clear, short text), use as-is. If it's a description/topic, draft tweet text.
2. **Preview**: Show the draft with character count (max 280). Use `AskUserQuestion` with options:
   - "Post it" — send the tweet
   - "Edit" — user provides revised text, loop back to preview
   - "Cancel" — abort
3. **Post**: Only after explicit "Post it" approval, run the posting script:
   ```bash
   python3 scripts/post.py "the tweet text here"
   ```
4. **Confirm**: Show the tweet URL from the script output.

## Tweet Drafting Guidelines

- Max 280 characters (hard limit)
- Professional but authentic tone
- No hashtag spam (0-2 max, only if natural)
- Include relevant context (product name, what happened)
- If announcing something, lead with the news

## Script Output

The posting script outputs JSON:
```json
{"id": "1234567890", "url": "https://x.com/i/status/1234567890", "text": "the posted tweet"}
```

On error, it outputs:
```json
{"error": "description of what went wrong"}
```

## Credential Setup (One-Time)

Run `bash scripts/setup.sh` — pops up native macOS dialogs to collect and store keys in Keychain.

**Fallback** — env vars in `~/.zshrc`: `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`.

## Setup Verification

```bash
bash scripts/verify-setup.sh
```

## Important

- **NEVER post without explicit user approval via AskUserQuestion**
- Always show character count in preview
- If text exceeds 280 chars, warn and offer to shorten
