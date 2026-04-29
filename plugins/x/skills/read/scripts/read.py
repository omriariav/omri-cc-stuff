#!/usr/bin/env python3
"""Fetch a tweet via X API v2 GET /2/tweets/:id and render as markdown to stdout.

Usage:
    python3 read.py "https://x.com/jack/status/20"
    python3 read.py 20
    python3 read.py "https://x.com/jack/status/20" --json
"""

import argparse
import json
import os
import re
import sys


TWEET_URL_RE = re.compile(r"(?:x|twitter)\.com/[^/]+/status/(\d+)", re.IGNORECASE)


def parse_tweet_id(arg):
    """Extract numeric tweet ID from a URL or accept a bare numeric ID."""
    arg = arg.strip()
    m = TWEET_URL_RE.search(arg)
    if m:
        return m.group(1)
    if arg.isdigit():
        return arg
    return None


def load_credentials():
    """Load X API credentials from keyring (preferred) or env vars. Mirrors post.py."""
    keys = {}
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

    keys = {
        "api_key": os.environ.get("X_API_KEY"),
        "api_secret": os.environ.get("X_API_SECRET"),
        "access_token": os.environ.get("X_ACCESS_TOKEN"),
        "access_token_secret": os.environ.get("X_ACCESS_TOKEN_SECRET"),
    }
    missing = [k for k, v in keys.items() if not v]
    if missing:
        print(json.dumps({"error": f"Missing credentials: {', '.join(missing)}. Run scripts/setup.sh in the tweet skill or set env vars."}))
        sys.exit(1)
    return keys


def make_oauth_session(creds):
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


def fetch_tweet(oauth, tweet_id):
    params = {
        "tweet.fields": "created_at,author_id,public_metrics,conversation_id,referenced_tweets,lang,entities",
        "expansions": "author_id,referenced_tweets.id,referenced_tweets.id.author_id,attachments.media_keys",
        "user.fields": "username,name,verified",
        "media.fields": "type,url,preview_image_url,alt_text",
    }
    resp = oauth.get(f"https://api.x.com/2/tweets/{tweet_id}", params=params)

    if resp.status_code == 200:
        return resp.json()
    if resp.status_code == 404:
        print(json.dumps({"error": f"Tweet {tweet_id} not found (404). Deleted, private, or never existed."}))
        sys.exit(1)
    if resp.status_code == 429:
        print(json.dumps({"error": "Rate limited by X API. Wait and try again."}))
        sys.exit(1)
    if resp.status_code in (401, 403):
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        print(json.dumps({"error": f"Auth error ({resp.status_code}): {detail}"}))
        sys.exit(1)
    print(json.dumps({"error": f"X API error ({resp.status_code}): {resp.text}"}))
    sys.exit(1)


def index_users(payload):
    users = {}
    for u in payload.get("includes", {}).get("users", []):
        users[u["id"]] = u
    return users


def index_tweets(payload):
    refs = {}
    for t in payload.get("includes", {}).get("tweets", []):
        refs[t["id"]] = t
    return refs


def index_media(payload):
    media = {}
    for m in payload.get("includes", {}).get("media", []):
        media[m["media_key"]] = m
    return media


def render_markdown(payload):
    data = payload["data"]
    users = index_users(payload)
    refs = index_tweets(payload)
    media = index_media(payload)

    author = users.get(data.get("author_id"), {})
    handle = author.get("username", "unknown")
    name = author.get("name", handle)

    lines = []
    lines.append(f"# Tweet by {name} (@{handle})")
    lines.append("")
    lines.append(f"**URL:** https://x.com/{handle}/status/{data['id']}")
    if data.get("created_at"):
        lines.append(f"**Posted:** {data['created_at']}")
    metrics = data.get("public_metrics") or {}
    if metrics:
        lines.append(
            f"**Metrics:** {metrics.get('like_count', 0)} likes · "
            f"{metrics.get('retweet_count', 0)} retweets · "
            f"{metrics.get('reply_count', 0)} replies · "
            f"{metrics.get('quote_count', 0)} quotes"
        )
    lines.append("")
    lines.append("## Text")
    lines.append("")
    lines.append("> " + data.get("text", "").replace("\n", "\n> "))
    lines.append("")

    # Referenced tweets (replied-to / quoted)
    for ref in data.get("referenced_tweets", []) or []:
        ref_type = ref.get("type")
        ref_id = ref.get("id")
        ref_tweet = refs.get(ref_id)
        if not ref_tweet:
            continue
        ref_author = users.get(ref_tweet.get("author_id"), {})
        ref_handle = ref_author.get("username", "unknown")
        label = {"replied_to": "Replying to", "quoted": "Quoting", "retweeted": "Retweeting"}.get(ref_type, ref_type)
        lines.append(f"## {label} @{ref_handle}")
        lines.append("")
        lines.append(f"**URL:** https://x.com/{ref_handle}/status/{ref_id}")
        lines.append("")
        lines.append("> " + ref_tweet.get("text", "").replace("\n", "\n> "))
        lines.append("")

    # Media
    media_keys = (data.get("attachments") or {}).get("media_keys", [])
    if media_keys:
        lines.append("## Media")
        lines.append("")
        for k in media_keys:
            m = media.get(k)
            if not m:
                continue
            mtype = m.get("type", "media")
            url = m.get("url") or m.get("preview_image_url") or "(no url)"
            alt = m.get("alt_text")
            line = f"- {mtype}: {url}"
            if alt:
                line += f" — alt: {alt}"
            lines.append(line)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="Fetch a tweet by URL or ID via X API v2.")
    parser.add_argument("target", help="Tweet URL (x.com/twitter.com) or numeric tweet ID")
    parser.add_argument("--json", action="store_true", help="Print raw API JSON instead of markdown")
    args = parser.parse_args()

    tweet_id = parse_tweet_id(args.target)
    if not tweet_id:
        print(json.dumps({"error": f"Could not parse tweet ID from: {args.target!r}"}))
        sys.exit(1)

    creds = load_credentials()
    oauth = make_oauth_session(creds)
    payload = fetch_tweet(oauth, tweet_id)

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        sys.stdout.write(render_markdown(payload))


if __name__ == "__main__":
    main()
