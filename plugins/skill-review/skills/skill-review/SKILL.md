---
name: skill-review
description: |
  Evaluate any skill against best practices - structure, progressive disclosure, gotchas, description quality, scripts, memory, and anti-patterns.
  Use when: "/skill-review", "review this skill", "evaluate skill quality", "audit skill", "how good is this skill", "rate this skill".
  NOT for: conversation-level reflection (use /reflect), code review, or PR review.
user-invocable: true
argument-hint: [--fix] <skill-path-or-name> | --compare <left-skill> <right-skill>
allowed-tools: Read, Glob, Grep, Edit, Write, Bash(python3*)
---

# /skill-review - Skill Design Evaluation

Evaluate a skill's design quality against best practices from Anthropic's skill-building guidance and real-world patterns from high-quality skills.

## How It Differs from /reflect

| | /reflect | /skill-review |
|---|---------|---------------|
| **Input** | Current conversation history | Skill files on disk |
| **Evaluates** | What worked/failed during usage | Design, structure, documentation quality |
| **When** | After using a skill | Any time, even before first use |
| **Output** | Conversation learnings, SKILL.md patches | Scored evaluation with actionable recommendations |

## Arguments

```
/skill-review publisher-lookup          → Review by skill name (auto-discovers path)
/skill-review ./skills/my-skill/        → Review by path
/skill-review --fix publisher-lookup    → Review + apply quick fixes automatically
/skill-review --compare reflect taboolar → Side-by-side comparison of two skills
```

**$ARGUMENTS** = `[--fix] <skill-path-or-name>` OR `--compare <left-skill> <right-skill>`

Parse the argument before starting:
- If first token is `--compare`, expect exactly two skill names following it. Run comparison mode (Phase 7).
- If first token is `--fix`, the next token is the skill name. Run normal evaluation then apply fixes (Phase 6).
- Otherwise, the first token is the skill name. Run normal evaluation only.
- If no argument is provided, ask: "Which skill should I review?"

## Workflow

### Phase 1: Discover & Inventory

**Step 1 - Locate the skill.** Search these paths in order, stop at first match:

1. Exact path if argument looks like a path (`./`, `/`, `~/`)
2. `~/.claude/skills/<name>/SKILL.md`
3. `~/.claude/plugins/*/skills/<name>/SKILL.md`
4. `~/Code/taboola-pm-skills/plugins/<name>/skills/<name>/SKILL.md`
5. Current project's `.claude/skills/<name>/SKILL.md`
6. Glob `**/skills/<name>/SKILL.md` (exclude `.git/`, `node_modules/`, `.venv/`)

**If no SKILL.md found**: Stop. Report "Skill not found: <name>. Searched [list paths checked]. Try providing the full path."

**If multiple matches**: List all candidates and ask "Which skill did you mean?" before proceeding.

**Step 2 - Resolve symlinks.** If the located path is a symlink, resolve it once to the real path. Work from the real path for all subsequent steps. Do not follow further symlinks inside the skill directory.

**Step 3 - Inventory the skill root.** Check for these standard owned subfolders only:

- `SKILL.md` (required)
- `LEARNINGS.md`
- `CLAUDE.md`
- `references/` - list files
- `scripts/` - list files
- `templates/` - list files
- `data/` - list files
- `examples/` - list files

Do NOT recurse into nested `plugins/`, `.git/`, `node_modules/`, `vendor/`, `.venv/`, or additional `SKILL.md` files beyond the root unless the main SKILL.md explicitly delegates to them.

**Step 4 - Read SKILL.md** fully. Extract frontmatter fields and note body structure (sections, line count).

**Step 5 - Read supporting files** referenced by SKILL.md or needed to score a dimension. Do not read files speculatively.

**Step 6 - Count metrics**: SKILL.md line count, number of files per subfolder.

### Phase 1b: Check Prior Reviews

Before scoring, check if this skill has been reviewed before:

```bash
python3 scripts/history.py --skill <skill-name>
```

If prior reviews exist, note the previous score and grade. A re-review should explain what changed since the last evaluation.

### Phase 2: Classify

Read `references/evaluation-framework.md` for the 9 categories. Use the signal words table as **hints only** — confirm classification semantically from the surrounding text, not keyword presence alone.

A skill should fit ONE category cleanly. If evidence is mixed, mark confidence as `low` and explain why. Do not force a category.

### Phase 3: Score (10 Dimensions)

Read `references/evaluation-framework.md` for the full rubric with scoring anchors.

For each dimension, use keyword patterns as hints — confirm semantically before assigning a score. When evidence is ambiguous, round down and note what would raise the score.

**D1: Progressive Disclosure (0-3)** - Does it use the file system for context engineering?
- Check: references/ or scripts/ populated? Does SKILL.md point to them appropriately?
- Red flag: SKILL.md > 200 lines AND no sub-files at all

**D2: Description Quality (0-3)** - Is the frontmatter description trigger-focused?
- Check: Does it say when to use AND when NOT to use? Includes specific trigger phrases?
- Red flag: Generic "Does X" with no trigger guidance

**D3: Gotchas Section (0-3)** - Is there a section documenting known failures?
- Check: Look for failure documentation semantically - specific errors with root causes and fixes
- Red flag: No failure documentation anywhere in the skill

**D4: Don't State the Obvious (0-3)** - Is content non-obvious to Claude?
- Check: Would Claude already know this without the skill? Is it org-specific tribal knowledge?
- Red flag: Skill is mostly generic frameworks Claude knows (STAR method, agile, product frameworks)

**D5: Avoid Railroading (0-3)** - Is there flexibility for Claude to adapt?
- Check: Decision branches, "if X then Y" conditionals, room for judgment?
- Red flag: Every step hardcoded, no conditionals, no graceful degradation

**D6: Setup & Configuration (0-3)** - Are user-specific values configurable?
- Check: config.json pattern? Arguments? Hardcoded absolute paths or usernames?
- Red flag: `/Users/specific-name/`, hardcoded emails or IDs baked into the skill

**D7: Memory & Data Storage (0-3)** - Does it retain useful state across runs?
- **Important**: Score 0 is correct and acceptable for intentionally stateless skills. Only score higher if the skill produces outputs where retention would genuinely benefit future runs.
- Check: LEARNINGS.md? Log files? Structured persistence?
- Red flag: Skill produces outputs that could inform future runs but discards everything

**D8: Scripts & Composable Code (0-3)** - Does it provide reusable scripts?
- Check: scripts/ with SQL, shell, or Python utilities Claude can compose on top of?
- Red flag: Complex multi-step logic described only in prose with no code assets

**D9: Frontmatter Quality (0-3)** - Is the YAML frontmatter well-configured?
- Check: name, description, allowed-tools (minimally scoped), user-invocable, argument-hint
- Red flag: Missing fields, `Bash` without subcommand scope, no argument-hint

**D10: Hooks Integration (0-2)** - Does it use on-demand hooks?
- Note: Most skills legitimately don't need hooks. Score 0 is fine. Only flag if hooks would clearly prevent a real risk (e.g., destructive pipeline with no guardrails).
- Check: hooks config, safety guardrails tied to skill invocation

### Phase 4: Detect Anti-Patterns

`score.py` auto-detects the structural anti-patterns (persona-only, script-wrapper, monolithic, hardcoded-paths, no-error-handling, stale-references, overpermissioned unscoped Bash, no-output-format). Trust its output for those.

The following three **require your semantic judgment** — score.py does not detect them:

| Anti-Pattern | How to Detect (Claude only) |
|-------------|----------------------------|
| **Redundant knowledge** | Read the content — is this generic best-practice Claude already knows, or org-specific? |
| **Category straddling** | After classifying in Phase 2, does the skill pull equally hard in 2+ directions? |
| **Overpermissioned (unused tools)** | Do the listed `allowed-tools` all appear in the workflow? Score.py only catches unscoped `Bash`. |

### Phase 5: Generate Report

Read `references/report-template.md` and fill it completely. Every section is required except "Comparison to Gold Standard" (see benchmarks.md for when to include it).

Score total: D1+D2+D3+D4+D5+D6+D7+D8+D9 (each 0-3) + D10 (0-2) = max 29
Grade: 25-29=A, 20-24=B, 15-19=C, 10-14=D, 0-9=F

### Phase 6: Apply Fixes (--fix mode)

Only auto-apply safe, non-destructive improvements. Show each change before applying.

**Auto-apply:**
- Improve frontmatter: add missing `argument-hint`, tighten `allowed-tools` scope
- Add gotchas scaffold if completely absent: `## Common Mistakes\n\n<!-- TODO: document gotchas from real usage -->`
- Fix stale file references: remove or update pointers to non-existent files
- Create `references/` directory structure if SKILL.md > 150 lines and no subfolders exist
- Add `LEARNINGS.md` only if the skill produces outputs where cross-run retention makes sense (not for all skills)

**Never auto-apply:**
- Content quality changes (D4)
- Architectural splits of monolithic SKILL.md
- Adding scripts (requires domain knowledge)
- Category or purpose changes

### Phase 7: Comparison Mode (--compare)

Run Phase 1-4 for each skill independently. Then produce a side-by-side table:

```
## Comparison: [left-skill] vs [right-skill]

| Dimension | [left] | [right] | Winner |
|-----------|--------|---------|--------|
| D1 | X | Y | ... |
...
| **Total** | X/29 | Y/29 | ... |

## What [left] does better
...

## What [right] does better
...

## What each could adopt from the other
...
```

## Structural Pre-Score

Run this **before Phase 3**, not after. It gives D1, D2, D3, D6, D7, D8, D9, D10 plus anti-pattern detection in seconds:

```bash
python3 scripts/score.py <skill-directory> --json
```

Use `--json` so the output is machine-parseable. Feed the structural scores directly into the report table. Only D4 and D5 require your semantic judgment — add them to the structural total for the full score.

Adjust a structural score only if you have specific semantic evidence that contradicts it, and note the reason.

## Configuration

Read `config.json` at startup. Key settings:

- `history_log` — path to history log (default: `~/.claude/plugin-data/skill-review/history.log`)
- `default_verbose` — show evidence in table output
- `benchmarks_check` — whether to attempt benchmark comparison (default: true)
- `auto_fix_threshold` — only offer `--fix` mode if score is below this (default: 15)

## History Logging

After generating a report, append a one-line entry using the history script:

```bash
python3 scripts/history.py --append "YYYY-MM-DD | <skill-name> | <score>/29 | <grade> | <top-issue>"
```

To view past evaluations for a skill:

```bash
python3 scripts/history.py --skill <name>
```

This allows tracking improvement over time when a skill is reviewed repeatedly.

## Trigger: Update LEARNINGS.md

After every review session, check if anything new was discovered that isn't already in `LEARNINGS.md`:

- A false positive or false negative from `score.py`
- An anti-pattern the script missed
- A skill that scored unexpectedly high or low — and why
- An edge case in path resolution, frontmatter parsing, or category classification

If yes, append it to `LEARNINGS.md` under the relevant section (Gotchas, Patterns That Work, or Version History). Keep entries specific: include the skill name, what happened, and the fix or insight.

This trigger is the mechanism that makes D3 improve over time — LEARNINGS.md feeds back into the gotchas section as the skill accumulates real failure data.

## Examples

See `examples/publisher-lookup-review.md` for a complete example output to calibrate report quality.

## References

- `references/evaluation-framework.md` — 10-dimension scoring rubric with anchors
- `references/report-template.md` — output format template
- `references/benchmarks.md` — gold standard skills and their known paths
- `scripts/score.py` — structural scoring script (D1-D3, D6-D10 + anti-patterns)
- `scripts/history.py` — view and append to the evaluation history log
- `examples/publisher-lookup-review.md` — complete example report for calibration
- `config.json` — configurable history path and behaviour settings
- `LEARNINGS.md` — captured gotchas and patterns from real usage

## Gotchas

**Symlink resolution**: Resolve the symlink once, work from the real path. Do not chase further symlinks inside the skill. Some skills in taboola-pm-skills are symlinked 2-3 levels deep.

**Nested plugins**: This repo has `plugins/taboolar/skills/taboolar/plugins/` nested structure. Do not recurse into it — it's an artifact, not a skill substructure.

**Multiple matches**: Glob searches will find the same skill in both the plugin source and its symlinked location. Prefer the real path (plugin source) over the symlink.

**Stateless skills are not broken**: A thin skill that wraps a script and has no LEARNINGS.md may score D7=0 correctly. Don't inflate the score or auto-add LEARNINGS.md unless retention genuinely helps.

**Keyword classification is unreliable**: "PR" appears in Runbooks and CI/CD skills. "template" appears in Scaffolding and Business Process skills. Always read the surrounding text before classifying.
