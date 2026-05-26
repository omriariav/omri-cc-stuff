#!/usr/bin/env python3
"""Post a tweet (or thread) via X API v2 using OAuth 1.0a."""

import json
import os
import sys
import argparse
import re


# X wraps every URL in a t.co shortlink, so a URL counts as a fixed 23 chars
# toward the 280 limit regardless of its real length. Counting raw len() here
# over-rejects tweets X would happily accept (e.g. a long GitHub release URL
# that X scores as 23 but len() scores at 55+).
TCO_URL_LEN = 23
_URL_RE = re.compile(r"https?://\S+")


def tweet_len(text):
    """Length as X counts it: each http(s) URL weighted as 23 chars."""
    return len(_URL_RE.sub("x" * TCO_URL_LEN, text))


def word_len(word):
    """Per-word weighted length for thread splitting (a URL word counts as 23)."""
    return TCO_URL_LEN if _URL_RE.fullmatch(word) else len(word)


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


def delete_tweet(tweet_id):
    """Delete a tweet by ID. Prints JSON result and exits non-zero on failure."""
    creds = load_credentials()
    oauth = make_oauth_session(creds)
    resp = oauth.delete(f"https://api.x.com/2/tweets/{tweet_id}")

    if resp.status_code == 200:
        body = resp.json()
        deleted = body.get("data", {}).get("deleted", False)
        print(json.dumps({"deleted": deleted, "id": tweet_id}))
        if not deleted:
            sys.exit(1)
        return
    if resp.status_code == 404:
        print(json.dumps({"error": f"Tweet {tweet_id} not found (404). Already deleted or never existed."}))
        sys.exit(1)
    if resp.status_code in (401, 403):
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        print(json.dumps({"error": f"Auth error ({resp.status_code}): {detail}. The tweet must belong to the authenticated account."}))
        sys.exit(1)
    if resp.status_code == 429:
        print(json.dumps({"error": "Rate limited by X API. Wait and try again."}))
        sys.exit(1)
    print(json.dumps({"error": f"X API error ({resp.status_code}): {resp.text}"}))
    sys.exit(1)


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

    Raises ValueError if any word is too long to fit in a single chunk.
    """
    words = text.split()
    if not words:
        return []

    # Check for unsplittable words upfront (worst-case prefix is ~7 chars)
    max_prefix_len = len("99/99: ")
    max_word_len = 280 - max_prefix_len
    for word in words:
        if word_len(word) > max_word_len:
            raise ValueError(
                f"Word is {word_len(word)} chars (max {max_word_len} per chunk after thread prefix). "
                f"Shorten or break up: '{word[:50]}...'"
            )

    # Try splitting with increasing part counts until all chunks fit
    for total in range(2, 100):
        prefix_len = len(f"{total}/{total}: ")
        max_text_len = 280 - prefix_len

        chunks = []
        current_chunk_words = []
        current_len = 0

        for word in words:
            word_addition = word_len(word) + (1 if current_chunk_words else 0)
            if current_len + word_addition > max_text_len and current_chunk_words:
                chunks.append(" ".join(current_chunk_words))
                current_chunk_words = [word]
                current_len = word_len(word)
            else:
                current_chunk_words.append(word)
                current_len += word_addition

        if current_chunk_words:
            chunks.append(" ".join(current_chunk_words))

        if len(chunks) <= total:
            actual_total = len(chunks)
            return [f"{i+1}/{actual_total}: {chunk}" for i, chunk in enumerate(chunks)]

    return [text[:280]]


def post_thread(chunks, oauth, reply_to=None):
    """Post a thread of tweets, each replying to the previous.

    If reply_to is provided, the first chunk is posted as a reply to that tweet.
    Returns list of result dicts. On mid-thread failure, emits partial results
    to stderr before exiting.
    """
    results = []
    previous_id = reply_to  # first chunk replies to this (None = standalone)

    for i, chunk in enumerate(chunks):
        try:
            tweet_id, _ = post_single_tweet(oauth, chunk, reply_to=previous_id)
        except SystemExit:
            if results:
                print(json.dumps({"partial_results": results, "failed_at_part": i + 1}), file=sys.stderr)
            raise
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
    if tweet_len(text) > 280:
        print(json.dumps({"error": f"Tweet too long: {tweet_len(text)} chars (max 280, URLs counted as {TCO_URL_LEN}). Use --thread for auto-splitting."}))
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


def post_tweet_thread(text, reply_to=None):
    """Split text into thread chunks and post as a thread."""
    if not text.strip():
        print(json.dumps({"error": "Tweet text is empty"}))
        sys.exit(1)

    try:
        chunks = split_into_thread(text)
    except ValueError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    if len(chunks) < 2:
        print(json.dumps({"error": "Text fits in a single tweet, no thread needed. Post without --thread."}))
        sys.exit(1)

    creds = load_credentials()
    oauth = make_oauth_session(creds)

    try:
        results = post_thread(chunks, oauth, reply_to=reply_to)
        print(json.dumps(results))
    except SystemExit:
        raise
    except Exception as e:
        print(json.dumps({"error": f"Thread posting failed: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post tweets via X API v2")
    parser.add_argument("text", nargs="?", help="Tweet text to post (omit when using --from-file or --delete)")
    parser.add_argument("--reply-to", dest="reply_to", help="Tweet ID to reply to")
    parser.add_argument("--thread", action="store_true", help="Auto-split into numbered thread")
    parser.add_argument("--from-file", dest="from_file", help="Read tweet text from a file path instead of the positional arg. Avoids shell-escape bugs (apostrophes, quotes, newlines).")
    parser.add_argument("--delete", dest="delete_id", metavar="TWEET_ID", help="Delete the tweet with this ID and exit.")

    args = parser.parse_args()

    if args.delete_id:
        if args.text or args.from_file or args.thread or args.reply_to:
            print(json.dumps({"error": "--delete is exclusive; do not combine with text, --from-file, --thread, or --reply-to."}))
            sys.exit(2)
        delete_tweet(args.delete_id)
        sys.exit(0)

    if args.from_file and args.text:
        print(json.dumps({"error": "Pass tweet text either as the positional argument or via --from-file, not both."}))
        sys.exit(2)

    if args.from_file:
        try:
            with open(args.from_file, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            print(json.dumps({"error": f"Could not read --from-file {args.from_file!r}: {e}"}))
            sys.exit(1)
        # Trailing newlines (incl. CRLF) from editors/heredocs are almost never intentional in tweet bodies.
        text = text.rstrip("\r\n")
    else:
        if not args.text:
            print(json.dumps({"error": "Missing tweet text. Pass as positional arg, or use --from-file PATH, or --delete TWEET_ID."}))
            sys.exit(2)
        text = args.text

    if args.thread:
        post_tweet_thread(text, reply_to=args.reply_to)
    else:
        post_tweet(text, reply_to=args.reply_to)
