#!/bin/bash
# claude-coacher SessionStart hook — inject the collaborator frame.
#
# Degrades gracefully: any missing dependency, missing file, empty frame,
# or unreadable content results in exit 0 with no output — never blocks
# session startup.
set -euo pipefail
cat > /dev/null  # drain stdin (SessionStart sends a payload we don't use)

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
FRAME_FILE="$PLUGIN_ROOT/frame.md"

[ -f "$FRAME_FILE" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

python3 - "$FRAME_FILE" <<'PY'
import json, re, sys

try:
    with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
        raw = f.read()
except OSError:
    sys.exit(0)

# Extract only the <claude-coacher-frame>...</claude-coacher-frame> block.
# Anything outside the tags (comments, editorial notes) is ignored so it
# never bleeds into session context.
match = re.search(
    r"<claude-coacher-frame>.*?</claude-coacher-frame>",
    raw,
    re.DOTALL,
)
frame = match.group(0).strip() if match else raw.strip()

if not frame:
    sys.exit(0)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": frame,
    },
    "systemMessage": "coacher: collaborator frame loaded (use /coacher:reset to re-anchor or /coacher:rant to translate a vent)",
}))
PY
