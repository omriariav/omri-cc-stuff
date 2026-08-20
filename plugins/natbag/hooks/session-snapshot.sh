#!/bin/bash
# SessionStart hook: runs daily flight snapshot (self-guards to once/day in snapshot.py).
# Runs at session start so flight data is fresh without blocking Skill calls.
set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

# Log to ~/.natbag/snapshot.log instead of /dev/null so failures (SSL, API
# changes, disk errors) leave a trace instead of silently stopping history.
LOG_FILE="$HOME/.natbag/snapshot.log"
mkdir -p "$HOME/.natbag"
if [ -f "$LOG_FILE" ] && [ "$(wc -c < "$LOG_FILE")" -gt 262144 ]; then
  tail -n 200 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi
{
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] session-snapshot"
  python3 "$PLUGIN_ROOT/skills/natbag/scripts/snapshot.py"
} >> "$LOG_FILE" 2>&1 || true

exit 0
