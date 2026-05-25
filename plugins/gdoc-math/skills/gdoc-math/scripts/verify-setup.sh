#!/bin/bash
# Verify gdoc-math dependencies: pandoc, the gws CLI, and gws Drive auth.
# Exits non-zero if anything is missing so the skill can stop before running the pipeline.

errors=0

# 1) pandoc — turns markdown+LaTeX into a .docx with native OMML equations.
if command -v pandoc >/dev/null 2>&1; then
    echo "  pandoc: installed ($(pandoc --version | head -1))"
else
    echo "  pandoc: MISSING — install with: brew install pandoc"
    errors=$((errors + 1))
fi

# 2) python3 — md2gdoc.sh uses it to parse gws JSON output.
if command -v python3 >/dev/null 2>&1; then
    echo "  python3: installed ($(python3 --version 2>&1))"
else
    echo "  python3: MISSING — required to parse gws output (install Python 3)"
    errors=$((errors + 1))
fi

# 3) gws — the Google Workspace CLI that uploads + converts the .docx to a Google Doc.
if command -v gws >/dev/null 2>&1; then
    echo "  gws: installed ($(command -v gws))"

    # 3b) gws Drive auth — the pipeline writes to Google Drive, so a live token is required.
    if gws drive about --quiet >/dev/null 2>&1; then
        who="$(gws drive about --format json 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("user",{}).get("email",""))' 2>/dev/null)"
        echo "  gws auth: OK${who:+ ($who)}"
    else
        echo "  gws auth: NOT AUTHENTICATED — run: gws auth login   (or use /gws:auth)"
        errors=$((errors + 1))
    fi
else
    echo "  gws: MISSING — install with: go install github.com/omriariav/workspace-cli/cmd/gws@latest"
    echo "       repo: https://github.com/omriariav/workspace-cli  (then: gws auth login)"
    errors=$((errors + 1))
fi

if [ $errors -eq 0 ]; then
    echo ""
    echo "Ready: markdown+LaTeX → editable Google Doc."
else
    echo ""
    echo "$errors issue(s) found. Fix them before using /gdoc-math."
    exit 1
fi
