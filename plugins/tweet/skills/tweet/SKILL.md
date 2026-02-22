---
name: tweet
description: |
  Post tweets to X (Twitter) from Claude Code.
  Use when user says "/tweet", "post a tweet", "tweet this".
allowed-tools: Bash, Read, AskUserQuestion
argument-hint: [what to tweet about]
---

# Tweet - Post to X (Twitter)

Post tweets from Claude Code via the X API v2. Supports single tweets, threads (auto-split for long text), and replies.

## Workflow

0. **Setup check**: Run `bash scripts/verify-setup.sh`. If credentials are missing:
   - Run `bash scripts/setup.sh` — this pops up native macOS dialogs for each key (values never pass through the conversation)
   - Tell user to get keys from developer.x.com → app → "Keys and Tokens" if they don't have them yet
   - Re-run verify to confirm, then proceed to step 1
1. **Draft**: Take `$ARGUMENTS` as the tweet prompt. If it's a direct tweet (clear, short text), use as-is. If it's a description/topic, draft tweet text. No length restriction at this stage.
2. **Preview**: Always display the **full tweet text** in a quote block, followed by the character count. The user must see exactly what will be posted before the `AskUserQuestion` prompt. Then:
   - **If <= 280 chars**: Show the full text + `(N/280 chars)`, then `AskUserQuestion` with options:
     - "Post it" — send the tweet
     - "Edit" — user provides revised text, loop back to preview
     - "Cancel" — abort
   - **If > 280 chars**: Show the full text + `(N chars — over limit)`, then `AskUserQuestion` with options:
     - "Post as thread" — auto-split into numbered parts (see Step 2b)
     - "Shorten it" — rewrite to fit 280 chars, loop back to preview
     - "Cancel" — abort
2b. **Thread preview** (if user chose "Post as thread"): Show the **full text of every part** with per-part char counts:
   ```
   1/3: First part of the tweet text shown in full here... (278/280)

   2/3: Second part text shown in full here... (265/280)

   3/3: Final part shown in full. (42/280)
   ```
   Then `AskUserQuestion` with options:
   - "Post it" — post the thread using `--reply-to` chaining (see "Thread (pre-split)" in Step 3)
   - "Edit" — user revises, loop back to step 2
   - "Cancel" — abort
3. **Post**: Execute the appropriate command based on mode:
   - **Single tweet**: `python3 scripts/post.py "the tweet text here"`
   - **Thread (pre-split)**: Post each tweet individually using `--reply-to` chaining. This preserves your exact tweet boundaries from the preview:
     ```
     python3 scripts/post.py "1/N: first tweet text"
     # capture tweet_id from output
     python3 scripts/post.py --reply-to TWEET_ID "2/N: second tweet text"
     # repeat for each part
     ```
   - **Thread (auto-split)**: `python3 scripts/post.py --thread "the full long text here"` — WARNING: this splits on word boundaries by character count, ignoring paragraph breaks. Only use for unstructured text where split points don't matter.
   - **Reply**: `python3 scripts/post.py --reply-to TWEET_ID "reply text here"`
4. **Confirm**: Show the tweet URL(s) from the script output.

## Tweet Drafting Guidelines

- Max 280 characters per tweet. Longer text: user chooses to post as numbered thread or shorten.
- Professional but authentic tone
- No hashtag spam (0-2 max, only if natural)
- Include relevant context (product name, what happened)
- If announcing something, lead with the news

## Character Counting — Critical

**Your markdown char count will NOT match the script's count.** Common mismatches:

- **URLs**: X wraps all URLs to t.co (23 chars), but `post.py` counts raw URL length. Always count the full URL string length, not 23.
- **Backticks**: Backtick characters (`` ` ``) in your preview are real chars in the tweet. Don't use them in length estimation then omit them.
- **Newlines**: Each `\n` counts as a character.
- **Em dashes**: `—` is 1 char but may render wider in preview.

**Best practice**: Aim for **270 chars max** in your preview to leave a safety margin. If the script rejects, you only need to trim a few words instead of multiple retry loops.

**Do NOT estimate char count yourself.** If close to the limit, use `python3 -c "print(len('''tweet text here'''))"` to get the exact count before previewing to the user.

## Script Output

Single tweet outputs JSON:
```json
{"id": "1234567890", "url": "https://x.com/i/status/1234567890", "text": "the posted tweet"}
```

Thread outputs a JSON array:
```json
[
  {"id": "111", "url": "https://x.com/i/status/111", "text": "1/3: First part...", "part": 1},
  {"id": "222", "url": "https://x.com/i/status/222", "text": "2/3: Second part...", "part": 2},
  {"id": "333", "url": "https://x.com/i/status/333", "text": "3/3: Final part.", "part": 3}
]
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
- **ALWAYS show the full tweet text** before asking the user to approve — never ask "Post it?" without displaying exactly what will be posted
- Always show character count in preview
- For threads, show the full text of every part with per-part character counts
- **For manually crafted threads: ALWAYS use --reply-to chaining**, not `--thread`. The `--thread` auto-splitter ignores paragraph structure and will break your carefully crafted tweets at arbitrary word boundaries.

## Known Issues

- `--thread` auto-splitter collapses all whitespace (including `\n\n`) and re-splits on word count, not paragraph boundaries. A previewed 7-tweet thread may become 6 tweets with mid-sentence breaks. Fix: use `--reply-to` chaining for pre-split threads. (2026-02-20)
- **Char count mismatch between preview and post.py**: Claude's estimated char count in preview often differs from `post.py`'s actual count by 5-30 chars, causing "Tweet too long" errors and retry loops. Root cause: URL length, special chars, newlines counted differently. Fix: use `python3 -c "print(len(...))"` for exact count, or aim for 270 chars. (2026-02-22)
