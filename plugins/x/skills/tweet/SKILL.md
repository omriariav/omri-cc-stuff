---
name: tweet
description: |
  Post tweets to X (Twitter) from Claude Code. Supports single tweets, threads (auto-split or manual), and replies.
  Use when user says "/x:tweet", "post a tweet", "tweet this", "post a thread", "reply to this tweet".
  NOT for reading tweets, analytics, scheduling, or DMs.
allowed-tools: Bash(python3*), Bash(bash scripts/*), Read, AskUserQuestion
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

Read `references/drafting-guidelines.md` for baseline rules, `config.json` for operational defaults (char target, thread style), and `LEARNINGS.json` for user-specific voice and preferences.

## Voice Learning

Before drafting any tweet, read `LEARNINGS.json` to match the user's established voice and preferences. Read `config.json` for operational defaults.

After each tweet is posted (confirmed via script output), append a new entry to the `entries` array in `LEARNINGS.json` for any patterns you noticed:
- Tone adjustments the user made during editing
- Phrasing preferences (words they added, removed, or rephrased)
- Structural preferences (thread vs. single tweet, use of lists, data, visuals)
- Any explicit feedback the user gave about style

Each entry has `date`, `category` (one of: `tone`, `phrasing`, `structure`, `feedback`), and `observation` fields. Do not duplicate existing observations.
If the `entries` array exceeds 30 items, consolidate related entries before appending new ones.

## Character Counting — Critical

Read `references/char-counting.md` for detailed rules. Key point: aim for **270 chars max** and use `python3 -c "print(len(...))"` for exact counts near the limit.

## Script Output

Scripts output JSON with `id`, `url`, `text` fields. Threads return an array with a `part` number per entry. Errors return `{"error": "..."}`.

## Important

- **NEVER post without explicit user approval via AskUserQuestion**
- **ALWAYS show the full tweet text** before asking the user to approve — never ask "Post it?" without displaying exactly what will be posted
- Always show character count in preview
- For threads, show the full text of every part with per-part character counts
- **For manually crafted threads: ALWAYS use --reply-to chaining**, not `--thread`. The `--thread` auto-splitter ignores paragraph structure and will break your carefully crafted tweets at arbitrary word boundaries.

## Known Issues

- `--thread` auto-splitter collapses all whitespace (including `\n\n`) and re-splits on word count, not paragraph boundaries. A previewed 7-tweet thread may become 6 tweets with mid-sentence breaks. Fix: use `--reply-to` chaining for pre-split threads. (2026-02-20)
- **Char count mismatch between preview and post.py**: Claude's estimated char count in preview often differs from `post.py`'s actual count by 5-30 chars, causing "Tweet too long" errors and retry loops. Root cause: URL length, special chars, newlines counted differently. Fix: use `python3 -c "print(len(...))"` for exact count, or aim for 270 chars. (2026-02-22)
