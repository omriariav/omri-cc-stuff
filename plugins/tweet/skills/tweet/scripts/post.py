#!/usr/bin/env python3
"""Post a tweet via X API v2 using OAuth 1.0a."""

import json
import os
import sys

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


def post_tweet(text):
    """Post tweet and return response JSON."""
    if len(text) > 280:
        print(json.dumps({"error": f"Tweet too long: {len(text)} chars (max 280)"}))
        sys.exit(1)

    if not text.strip():
        print(json.dumps({"error": "Tweet text is empty"}))
        sys.exit(1)

    creds = load_credentials()

    try:
        from requests_oauthlib import OAuth1Session
    except ImportError:
        print(json.dumps({"error": "requests_oauthlib not installed. Run: pip3 install requests-oauthlib"}))
        sys.exit(1)

    oauth = OAuth1Session(
        creds["api_key"],
        client_secret=creds["api_secret"],
        resource_owner_key=creds["access_token"],
        resource_owner_secret=creds["access_token_secret"],
    )

    resp = oauth.post(
        "https://api.x.com/2/tweets",
        json={"text": text},
    )

    if resp.status_code == 201:
        data = resp.json()
        tweet_id = data["data"]["id"]
        print(json.dumps({
            "id": tweet_id,
            "url": f"https://x.com/i/status/{tweet_id}",
            "text": text,
        }))
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: post.py 'tweet text'"}))
        sys.exit(1)

    post_tweet(sys.argv[1])
