#!/bin/bash
# Session Context Plugin - SessionStart hook
set -euo pipefail
cat > /dev/null

GWS="/Users/omri.a/go/bin/gws"
CACHE_DIR="${CLAUDE_PLUGIN_ROOT:-/tmp}/state"
CACHE_FILE="$CACHE_DIR/context-cache.txt"
STALE_MINUTES=60

mkdir -p "$CACHE_DIR"

# Check if cache is fresh
if [ -f "$CACHE_FILE" ]; then
    cache_age=$(( ($(date +%s) - $(stat -f %m "$CACHE_FILE")) / 60 ))
    if [ "$cache_age" -lt "$STALE_MINUTES" ]; then
        CONTEXT=$(cat "$CACHE_FILE")
        python3 -c "
import json, sys
context = sys.stdin.read()
print(json.dumps({'hookSpecificOutput':{'hookEventName':'SessionStart','additionalContext':context}}))
" <<< "$CONTEXT"
        exit 0
    fi
fi

# Fetch fresh data in parallel
TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

$GWS calendar events --days 1 --format json > "$TMP/cal.json" 2>/dev/null &
$GWS gmail list --query 'is:starred' --max 10 --format json > "$TMP/gmail.json" 2>/dev/null &
$GWS tasks list MTI1NDAwMzI5MTY5NjMyMzk0OTU6MDow --format json > "$TMP/tasks.json" 2>/dev/null &
wait

# Parse and format
python3 - "$TMP" "$CACHE_FILE" <<'PY'
import json, sys, os
from datetime import datetime

tmp = sys.argv[1]
cache_path = sys.argv[2]

def safe_load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return None

now = datetime.now()
lines = []
lines.append(f"## Work Context ({now.strftime('%H:%M')})")
lines.append("")

# Calendar
cal = safe_load(f"{tmp}/cal.json")
if cal and cal.get("events"):
    real_events = [e for e in cal["events"] if e.get("event_type") != "workingLocation"]
    lines.append(f"**Calendar** ({len(real_events)} events today)")
    for e in real_events[:8]:
        start = e.get("start", "")
        if "T" in str(start):
            start = str(start).split("T")[1][:5]
        else:
            start = "all-day"
        summary = e.get("summary", "No title")[:50]
        lines.append(f"  {start} {summary}")
    lines.append("")

# Gmail starred
gmail = safe_load(f"{tmp}/gmail.json")
if gmail and gmail.get("threads"):
    threads = gmail["threads"]
    lines.append(f"**Starred emails** ({len(threads)})")
    for t in threads[:5]:
        snippet = t.get("snippet", "")[:60]
        lines.append(f"  - {snippet}")
    lines.append("")

# Tasks
tasks = safe_load(f"{tmp}/tasks.json")
if tasks and tasks.get("tasks"):
    pending = [t for t in tasks["tasks"] if t.get("status") != "completed"]
    if pending:
        lines.append(f"**Tasks** ({len(pending)} pending)")
        for t in pending[:5]:
            title = t.get("title", "No title")[:50]
            lines.append(f"  - [ ] {title}")
        lines.append("")

context = "\n".join(lines)

# Save to cache
os.makedirs(os.path.dirname(cache_path), exist_ok=True)
with open(cache_path, "w") as f:
    f.write(context)

# Output for hook injection
output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context
    }
}
print(json.dumps(output))
sys.exit(0)
PY
