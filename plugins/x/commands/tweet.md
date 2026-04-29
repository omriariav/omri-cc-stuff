---
description: Post a tweet, thread, or reply to X (Twitter) — drafts, previews, and posts after approval.
argument-hint: '<text or topic to tweet>'
allowed-tools: Bash(python3:*), Bash(bash:*), Read, AskUserQuestion
---

Post a tweet from Claude Code via the X API v2. Supports single tweets, threads (auto-split for long text), and replies. Detailed drafting guidelines and voice learnings live in `${CLAUDE_PLUGIN_ROOT}/skills/tweet/` — read them when drafting.

## Workflow

0. **Setup check**: Run `bash ${CLAUDE_PLUGIN_ROOT}/skills/tweet/scripts/verify-setup.sh`. If credentials are missing, run `bash ${CLAUDE_PLUGIN_ROOT}/skills/tweet/scripts/setup.sh` (native macOS dialogs — values never pass through the conversation), then re-verify.

1. **Draft**: Take `$ARGUMENTS` as the tweet prompt. If it's a direct tweet (clear, short text), use as-is. If it's a description/topic, draft tweet text. Read `${CLAUDE_PLUGIN_ROOT}/skills/tweet/SKILL.md`, `${CLAUDE_PLUGIN_ROOT}/skills/tweet/references/drafting-guidelines.md`, `${CLAUDE_PLUGIN_ROOT}/skills/tweet/config.json`, and `${CLAUDE_PLUGIN_ROOT}/skills/tweet/LEARNINGS.json` for voice and operational defaults. No length restriction at draft stage.

2. **Preview**: Show the **full tweet text** in a quote block followed by character count. Then `AskUserQuestion`:
   - **≤ 280 chars**: options `Post it` / `Edit` / `Cancel`
   - **> 280 chars**: options `Post as thread` / `Shorten it` / `Cancel`

2b. **Thread preview** (if user chose "Post as thread"): show every part with per-part char counts (`1/N: text... (278/280)`), then `AskUserQuestion`: `Post it` / `Edit` / `Cancel`.

3. **Post**: Run from the plugin root:
   - **Single**: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/tweet/scripts/post.py "the tweet text"`
   - **Thread (pre-split)**: post each part with `--reply-to <previous_id>` chaining, capturing each tweet_id from output
   - **Thread (auto-split, fallback only)**: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/tweet/scripts/post.py --thread "long text"`
   - **Reply**: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/tweet/scripts/post.py --reply-to TWEET_ID "reply text"`

4. **Confirm**: Show the tweet URL(s) from the script output.

5. **Voice learning**: After a successful post, append observations to `${CLAUDE_PLUGIN_ROOT}/skills/tweet/LEARNINGS.json` if anything in the draft → final transformation is generalizable (rejected phrasings, structural choices the user accepted/rejected). Skip noise.
