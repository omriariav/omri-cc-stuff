---
name: gdoc-math
description: |
  Convert Markdown containing LaTeX math into a native Google Doc whose equations are real, editable Google Docs equation objects (not images, not literal $$ text).
  Use when the user says "/gdoc-math", "turn this markdown into a Google Doc with editable equations", "convert this LaTeX/formulas to a Google Doc", "make a gdoc from this .md with math", or has an LLM/Gemini answer full of $...$ formulas they want as a proper editable Doc.
  NOT for plain Markdown with no math (use /copy:gdocs + Paste from Markdown), NOT for copying to the clipboard, NOT for Sheets/Slides, NOT for editing an existing Doc's body.
argument-hint: '[path/to/file.md] [--name "Doc title"] [--folder DRIVE_FOLDER_ID]'
allowed-tools: Bash(bash:*), Bash(gws:*), Bash(pandoc:*), Read, Write, AskUserQuestion
user-invocable: true
---

# gdoc-math — Markdown + LaTeX → Google Doc with editable equations

Google Docs' **Paste from Markdown** ignores math: `$...$` and `$$...$$` land as literal text. There is also no Google Docs API to insert native equation objects. This skill takes the only route that yields **editable** equations:

```
markdown+LaTeX  →[pandoc]→  .docx (OMML)  →[gws drive upload]→  →[gws drive convert --to docs]→  Google Doc
                                                                       └─ intermediate .docx is auto-trashed
```

pandoc renders LaTeX into Office MathML (OMML); Google Drive imports OMML as native, clickable, editable Google Docs equations. The script `scripts/md2gdoc.sh` runs the whole pipeline and prints the Doc link.

## Prerequisites

Three hard dependencies — the skill cannot work without them, so verify them before doing anything else (Step 0 below):

- **pandoc** — `brew install pandoc`. Renders LaTeX into the OMML equations Google imports.
- **python3** — used to parse `gws` JSON output (present by default on macOS).
- **gws** (the Google Workspace CLI), **authenticated for Drive** — the pipeline uploads + converts a file in the user's Drive.
  - Install: `go install github.com/omriariav/workspace-cli/cmd/gws@latest` (repo: https://github.com/omriariav/workspace-cli)
  - Authenticate: `gws auth login` (or the `/gws:auth` skill). Verify with `gws auth status`.

## Workflow

0. **Preflight — verify dependencies.** Before anything else, run:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/skills/gdoc-math/scripts/verify-setup.sh"
   ```
   It checks pandoc, the `gws` binary, and live Drive auth, printing exactly what's missing and how to fix it. **On failure** (non-zero exit), stop and report the remediation to the user — don't attempt the pipeline against a missing dependency, or the math conversion or Drive write will throw a confusing error downstream. `md2gdoc.sh` repeats these checks as a safety net, but Step 0 gives the user one clear, upfront fix-list.

1. **Resolve the input into a single `.md` file path:**
   - **Path given** in `$ARGUMENTS` (ends in `.md`/`.markdown` and exists) → use it directly.
   - **Inline content** in `$ARGUMENTS` (a blob of markdown, not a path) → `Write` it to a temp file, e.g. `/tmp/gdoc-math-<timestamp>.md`, and use that path.
   - **Nothing usable** → fall back to the most recent substantial Markdown content in the conversation (the last assistant answer or code block containing `$`/`$$` math). `Write` it to a temp `.md` and use that path. If the conversation has no clear candidate, ask the user what to convert with `AskUserQuestion`.

2. **Pick a title (optional):** If the user named the doc, pass `--name "<title>"`. Otherwise let the script derive it from the first `#` heading or the filename.

3. **Run the pipeline** from the skill directory:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/skills/gdoc-math/scripts/md2gdoc.sh" "<path.md>" [--name "<title>"] [--folder <DRIVE_FOLDER_ID>]
   ```
   The script writes `DOC_NAME=`, `DOC_ID=`, and `DOC_URL=` lines to stdout.

4. **Present the result:** Give the user the **`DOC_URL`** as a clickable link and the doc title. Note that the equations are now native and editable. Briefly flag that very complex LaTeX (stacked fractions, matrices, large operators) can lose some fidelity on Google's import and may need a touch-up.

## Flags & config

- `--name "Title"` — Google Doc name (default: first `#` heading, else the filename).
- `--folder ID` — create the Doc inside a specific Drive folder (default: My Drive root). Overrides config.
- `--keep-docx` — keep the intermediate `.docx` in Drive instead of trashing it (debugging only).

`config.json` holds one optional setting, `default_folder_id` — if set, Docs land in that Drive folder when `--folder` isn't passed. It's empty by default (My Drive root); the skill works fine without touching it.

## Output format

`md2gdoc.sh` prints exactly this three-line structure to stdout (parse `DOC_URL` for the link):

```
DOC_NAME=<the document title>
DOC_ID=<the Google Doc file id>
DOC_URL=<https://docs.google.com/document/d/.../edit>
```

Present `DOC_URL` to the user as a clickable link with the title. Any other stdout is a diagnostic from a failed step — surface it, don't paper over it.

## Example

A ready-to-run sample ships at `examples/laplace-smoothing.md` (inline + display math, fractions, subscripts, Greek, `\text{}`). A typical run:

```
User: /gdoc-math examples/laplace-smoothing.md
→ bash .../md2gdoc.sh examples/laplace-smoothing.md
→ DOC_URL=https://docs.google.com/document/d/1Or.../edit
Claude: Done — "Laplace Smoothing" is in your Drive with native, editable
        equations: <link>. Fractions and subscripts came through clean.
```

## Common mistakes

These are real failure modes — knowing *why* each happens prevents the wrong fix.

- **LaTeX comes out as literal `$...$` text.** Almost always the wrong pandoc reader. `gfm` (GitHub-flavored) does **not** parse `$`-delimited math, so it passes through verbatim — exactly the failure `/copy:gdocs` has. The script pins `-f markdown+tex_math_dollars+tex_math_single_backslash` for this reason; don't "simplify" it to `gfm`. Supported delimiters: `$…$`, `$$…$$`, `\(…\)`, `\[…\]`. Other delimiters won't convert.
- **`gws is not authenticated for Drive`.** The pipeline writes to Google Drive over the network, so `gws` must be authed. The script probes this up front and fails fast — hand the user to `/gws:auth`, don't retry.
- **A stray `.docx` shows up in Drive.** `gws drive upload` + `gws drive convert` is a two-step flow: convert creates a *new* Google Doc and leaves the uploaded `.docx` behind. The script trashes that intermediate automatically on exit; only `--keep-docx` (debugging) leaves it.
- **Equation fidelity on complex LaTeX.** Simple fractions/subscripts/Greek round-trip cleanly, but Google's OMML import can mangle stacked fractions, matrices, and large operators. Tell the user to spot-check those rather than promising pixel-perfect output.

## Notes

- **Editable, verified:** equations round-trip as OMML (`m:oMath`) with no embedded images — genuine editable equation objects, not pictures.
- **Side effect:** this creates a file in the user's Google Drive (intermediate `.docx` auto-trashed).
- **Not the clipboard:** for plain prose/tables with no math, `/copy:gdocs` (Paste from Markdown) is simpler and stays local.
