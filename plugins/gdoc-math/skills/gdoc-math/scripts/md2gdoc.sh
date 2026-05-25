#!/usr/bin/env bash
#
# md2gdoc.sh — Convert a Markdown file (with LaTeX math) into a native Google Doc
# whose equations are real, editable Google Docs equation objects.
#
# Pipeline:
#   markdown+LaTeX  --[pandoc]-->  .docx (OMML equations)
#                   --[gws drive upload]-->  raw .docx in Drive
#                   --[gws drive convert --to docs]-->  Google Doc
#                   --[gws drive delete]-->  trash the intermediate .docx
#
# Why this works: pandoc renders `$...$` / `$$...$$` into Office MathML (OMML),
# and Google Drive imports OMML as native editable equations — something Google
# Docs' "Paste from Markdown" cannot do (it leaves LaTeX as literal text).
#
# Usage:
#   md2gdoc.sh <input.md> [--name "Doc title"] [--folder DRIVE_FOLDER_ID] [--keep-docx]
#
# Output (stdout): the Google Doc web link on the last line, prefixed "DOC_URL=".

set -euo pipefail

err() { printf 'ERROR: %s\n' "$1" >&2; exit 1; }

# ---- args -------------------------------------------------------------------
INPUT=""
DOC_NAME=""
FOLDER=""
KEEP_DOCX=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)      [[ $# -ge 2 && "$2" != --* ]] || err "--name requires a value";   DOC_NAME="$2"; shift 2 ;;
    --folder)    [[ $# -ge 2 && "$2" != --* ]] || err "--folder requires a value"; FOLDER="$2";   shift 2 ;;
    --keep-docx) KEEP_DOCX=1;       shift ;;
    -h|--help)
      sed -n '2,20p' "$0"; exit 0 ;;
    -*) err "unknown flag: $1" ;;
    *)  [[ -z "$INPUT" ]] && INPUT="$1" || err "unexpected argument: $1"; shift ;;
  esac
done

[[ -n "$INPUT" ]]    || err "no input markdown file given. Usage: md2gdoc.sh <input.md> [--name ...] [--folder ...]"
[[ -f "$INPUT" ]]    || err "input file not found: $INPUT"

# ---- dependency checks ------------------------------------------------------
command -v pandoc >/dev/null 2>&1 || err "pandoc not found. Install with: brew install pandoc"
command -v gws    >/dev/null 2>&1 || err "gws (Google Workspace CLI) not found. Install: go install github.com/omriariav/workspace-cli/cmd/gws@latest"
command -v python3 >/dev/null 2>&1 || err "python3 not found."

# gws auth probe (cheap, read-only). Fails loudly if not authenticated.
gws drive about --quiet >/dev/null 2>&1 \
  || err "gws is not authenticated for Drive. Run the gws auth setup (see /gws:auth) and retry."

# Optional: fall back to a default Drive folder from config.json when --folder
# wasn't passed. Purely optional — empty/missing config just means My Drive root.
if [[ -z "$FOLDER" ]]; then
  CONFIG_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/config.json"
  if [[ -f "$CONFIG_FILE" ]]; then
    # A missing config is fine (My Drive root). A present file must be a JSON object;
    # malformed JSON or a non-object (e.g. a list) is a real error, not a silent fallback.
    FOLDER="$(python3 -c 'import sys,json
d=json.load(open(sys.argv[1]))
sys.exit("not a JSON object") if not isinstance(d,dict) else print(d.get("default_folder_id","") or "")' "$CONFIG_FILE")" \
      || err "config.json must be a JSON object with an optional \"default_folder_id\": $CONFIG_FILE"
  fi
fi

# ---- derive a doc name if not provided --------------------------------------
if [[ -z "$DOC_NAME" ]]; then
  # First Markdown H1, else the input filename without extension.
  DOC_NAME="$(grep -m1 -E '^#[[:space:]]+' "$INPUT" 2>/dev/null | sed -E 's/^#+[[:space:]]+//' || true)"
  if [[ -z "$DOC_NAME" ]]; then
    base="$(basename "$INPUT")"
    DOC_NAME="${base%.*}"
  fi
fi

# ---- temp workspace ---------------------------------------------------------
TMPDIR_RUN="$(mktemp -d "${TMPDIR:-/tmp}/md2gdoc.XXXXXX")"
DOCX="$TMPDIR_RUN/out.docx"
RAW_ID=""
cleanup() {
  # Trash the intermediate raw .docx FIRST (convert makes a NEW file) — do it before
  # the local rm so a failing rm under `set -e` can't skip the Drive cleanup.
  if [[ "$KEEP_DOCX" -eq 0 && -n "$RAW_ID" ]]; then
    gws drive delete "$RAW_ID" --quiet >/dev/null 2>&1 || true
  fi
  rm -rf "$TMPDIR_RUN" || true
}
trap cleanup EXIT

# ---- 1) pandoc: markdown(+LaTeX) -> docx with native OMML equations ---------
# Explicit `markdown` reader (NOT gfm) so tex_math_dollars is on; also accept
# \( \) and \[ \] delimiters that LLM exports often use.
pandoc "$INPUT" \
  -f markdown+tex_math_dollars+tex_math_single_backslash \
  -o "$DOCX" \
  || err "pandoc conversion failed."
[[ -s "$DOCX" ]] || err "pandoc produced an empty .docx."

# ---- 2) upload the .docx to Drive -------------------------------------------
UPLOAD_ARGS=(drive upload "$DOCX" --name "${DOC_NAME}.docx" --format json)
[[ -n "$FOLDER" ]] && UPLOAD_ARGS+=(--folder "$FOLDER")
# Keep stderr out of the captured JSON — a stray warning on stdout-mixed-stderr
# would break parsing only *after* the Drive file was created.
UPLOAD_JSON="$(gws "${UPLOAD_ARGS[@]}" 2>"$TMPDIR_RUN/upload.err")" \
  || err "gws drive upload failed: $(cat "$TMPDIR_RUN/upload.err" 2>/dev/null)"
RAW_ID="$(printf '%s' "$UPLOAD_JSON" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("id",""))' 2>/dev/null || true)"
[[ -n "$RAW_ID" ]] || err "could not parse uploaded file id from gws output: $UPLOAD_JSON"

# ---- 3) convert the .docx into a native Google Doc --------------------------
CONVERT_ARGS=(drive convert "$RAW_ID" --to docs --name "$DOC_NAME" --format json)
[[ -n "$FOLDER" ]] && CONVERT_ARGS+=(--folder "$FOLDER")
CONVERT_JSON="$(gws "${CONVERT_ARGS[@]}" 2>"$TMPDIR_RUN/convert.err")" \
  || err "gws drive convert failed: $(cat "$TMPDIR_RUN/convert.err" 2>/dev/null)"

DOC_URL="$(printf '%s' "$CONVERT_JSON" | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d.get("web_link") or d.get("webViewLink") or "")' 2>/dev/null || true)"
DOC_ID="$(printf '%s' "$CONVERT_JSON" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("id",""))' 2>/dev/null || true)"
[[ -n "$DOC_ID" ]] || err "conversion did not return a Google Doc id: $CONVERT_JSON"
[[ -n "$DOC_URL" ]] || DOC_URL="https://docs.google.com/document/d/${DOC_ID}/edit"

# ---- report -----------------------------------------------------------------
printf 'DOC_NAME=%s\n' "$DOC_NAME"
printf 'DOC_ID=%s\n'   "$DOC_ID"
printf 'DOC_URL=%s\n'  "$DOC_URL"
