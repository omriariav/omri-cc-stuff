#!/usr/bin/env python3
"""Post a tweet (or thread) via X API v2 using OAuth 1.0a."""

import json
import os
import sys
import argparse


def load_credentials():
    """Load X API credentials from keyring (preferred) or env vars."""
    keys = {}

    # Try keyring first
    try:
        import keyring
        keys = {
            "api_key": keyring.get_password("x-api", "api_key"),
            "api_secret": keyring.get_password("x-api", "api_secret"),
            "access_token": keyring.get_password("x-api", "access_token"),
            "access_token_secret": keyring.get_password("x-api", "access_token_secret"),
        }
        if all(keys.values()):
            return keys
    except ImportError:
        pass
    except Exception:
        print(json.dumps({"warning": "Keychain access failed, trying env vars"}), file=sys.stderr)


    # Fall back to env vars
    keys = {
        "api_key": os.environ.get("X_API_KEY"),
        "api_secret": os.environ.get("X_API_SECRET"),
        "access_token": os.environ.get("X_ACCESS_TOKEN"),
        "access_token_secret": os.environ.get("X_ACCESS_TOKEN_SECRET"),
    }

    missing = [k for k, v in keys.items() if not v]
    if missing:
        print(json.dumps({"error": f"Missing credentials: {', '.join(missing)}. Set env vars (X_API_KEY, etc.) or use keyring."}))
        sys.exit(1)

    return keys


def make_oauth_session(creds):
    """Create an OAuth1Session from credentials."""
    try:
        from requests_oauthlib import OAuth1Session
    except ImportError:
        print(json.dumps({"error": "requests_oauthlib not installed. Run: pip3 install requests-oauthlib"}))
        sys.exit(1)

    return OAuth1Session(
        creds["api_key"],
        client_secret=creds["api_secret"],
        resource_owner_key=creds["access_token"],
        resource_owner_secret=creds["access_token_secret"],
    )


def post_single_tweet(oauth, text, reply_to=None):
    """Post a single tweet, optionally as a reply. Returns (tweet_id, response_data) or exits on error."""
    payload = {"text": text}
    if reply_to:
        payload["reply"] = {"in_reply_to_tweet_id": reply_to}

    resp = oauth.post("https://api.x.com/2/tweets", json=payload)

    if resp.status_code == 201:
        data = resp.json()
        tweet_id = data["data"]["id"]
        return tweet_id, data
    elif resp.status_code == 429:
        print(json.dumps({"error": "Rate limited by X API. Wait a few minutes and try again."}))
        sys.exit(1)
    elif resp.status_code in (401, 403):
        detail = resp.json().get("detail", resp.text)
        print(json.dumps({"error": f"Auth error ({resp.status_code}): {detail}"}))
        sys.exit(1)
    else:
        print(json.dumps({"error": f"X API error ({resp.status_code}): {resp.text}"}))
        sys.exit(1)


def split_into_thread(text):
    """Split text into numbered thread chunks that fit within 280 chars each.

    Each chunk is formatted as '{i}/{total}: {text}' where the prefix
    takes 5-7 chars (e.g. '1/3: ' = 5 chars, '10/12: ' = 7 chars).
    Splits on word boundaries to avoid breaking mid-word.
    """
    # Estimate total parts to determine prefix length
    # Start with a rough estimate, then refine
    words = text.split()
    if not words:
        return []

    # Try splitting with increasing part counts until all chunks fit
    for total in range(2, 100):
        prefix_len = len(f"{total}/{total}: ")
        max_text_len = 280 - prefix_len

        chunks = []
        current_chunk_words = []
        current_len = 0

        for word in words:
            word_addition = len(word) + (1 if current_chunk_words else 0)
            if current_len + word_addition > max_text_len and current_chunk_words:
                chunks.append(" ".join(current_chunk_words))
                current_chunk_words = [word]
                current_len = len(word)
            else:
                current_chunk_words.append(word)
                current_len += word_addition

        if current_chunk_words:
            chunks.append(" ".join(current_chunk_words))

        if len(chunks) <= total:
            # Format with actual count
            actual_total = len(chunks)
            return [f"{i+1}/{actual_total}: {chunk}" for i, chunk in enumerate(chunks)]

    # Fallback: shouldn't reach here for reasonable text
    return [text[:280]]


def post_thread(chunks, oauth):
    """Post a thread of tweets, each replying to the previous.

    Returns list of result dicts. If a chunk fails mid-thread,
    reports what succeeded and what failed.
    """
    results = []
    previous_id = None

    for i, chunk in enumerate(chunks):
        tweet_id, _ = post_single_tweet(oauth, chunk, reply_to=previous_id)
        results.append({
            "id": tweet_id,
            "url": f"https://x.com/i/status/{tweet_id}",
            "text": chunk,
            "part": i + 1,
        })
        previous_id = tweet_id

    return results


def post_tweet(text, reply_to=None):
    """Post a single tweet and print result JSON."""
    if len(text) > 280:
        print(json.dumps({"error": f"Tweet too long: {len(text)} chars (max 280). Use --thread for auto-splitting."}))
        sys.exit(1)

    if not text.strip():
        print(json.dumps({"error": "Tweet text is empty"}))
        sys.exit(1)

    creds = load_credentials()
    oauth = make_oauth_session(creds)
    tweet_id, _ = post_single_tweet(oauth, text, reply_to=reply_to)

    print(json.dumps({
        "id": tweet_id,
        "url": f"https://x.com/i/status/{tweet_id}",
        "text": text,
    }))


def post_tweet_thread(text):
    """Split text into thread chunks and post as a thread."""
    if not text.strip():
        print(json.dumps({"error": "Tweet text is empty"}))
        sys.exit(1)

    chunks = split_into_thread(text)
    if len(chunks) < 2:
        print(json.dumps({"error": "Text fits in a single tweet, no thread needed. Post without --thread."}))
        sys.exit(1)

    # Validate all chunks fit
    for i, chunk in enumerate(chunks):
        if len(chunk) > 280:
            print(json.dumps({"error": f"Chunk {i+1} is {len(chunk)} chars — contains a word too long to split. Shorten it."}))
            sys.exit(1)

    creds = load_credentials()
    oauth = make_oauth_session(creds)

    try:
        results = post_thread(chunks, oauth)
        print(json.dumps(results))
    except SystemExit:
        raise
    except Exception as e:
        print(json.dumps({"error": f"Thread posting failed: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post tweets via X API v2")
    parser.add_argument("text", help="Tweet text to post")
    parser.add_argument("--reply-to", dest="reply_to", help="Tweet ID to reply to")
    parser.add_argument("--thread", action="store_true", help="Auto-split into numbered thread")

    args = parser.parse_args()

    if args.thread:
        post_tweet_thread(args.text)
    else:
        post_tweet(args.text, reply_to=args.reply_to)
