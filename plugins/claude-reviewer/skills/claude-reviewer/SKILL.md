---
name: claude-reviewer
description: |
  Review any project's .claude/ folder setup against Claude Code best practices. Scores 8 dimensions (24-point rubric), detects anti-patterns, and produces an actionable improvement report.
  Use when: "/claude-reviewer", "review my claude config", "audit .claude setup", "check my CLAUDE.md", "how good is my claude config", "rate this project's claude setup".
  NOT for: reviewing individual skill quality (use /skill-review), code review, PR review.
user-invocable: true
argument-hint: "[--global] [--verbose] [project-path]"
allowed-tools: Read, Glob, Grep, Bash(python3*), Bash(git*)
---

# /claude-reviewer - Claude Code Configuration Auditor

Review any project's `.claude/` folder against best practices from Anthropic's Claude Code configuration guidance.

## How It Differs from /skill-review

| | /skill-review | /claude-reviewer |
|---|---------|---------------|
| **Input** | A single skill directory | An entire project's .claude/ folder |
| **Evaluates** | Skill design quality (SKILL.md, scripts, references) | Config hygiene (CLAUDE.md, settings.json, rules/, commands/, skills/, agents/) |
| **When** | After building a skill | When setting up or auditing a project |
| **Output** | 10-dimension skill score (max 29) | 8-dimension config score (max 24) |

## Arguments

```
/claude-reviewer                      -> Review current working directory
/claude-reviewer ~/Code/myproject     -> Review specific project
/claude-reviewer --global             -> Review ONLY ~/.claude/ global config
/claude-reviewer --verbose            -> Include evidence quotes in report
```

**$ARGUMENTS** = `[--global] [--verbose] [project-path]`

Parse the argument before starting:
- Extract `--global` flag if present.
- Extract `--verbose` flag if present. When set, include evidence quotes.
- Remaining token is the project path.
- **Routing logic:**
  - `--global` → **Global mode**: audit only `~/.claude/`. Score 5 applicable dimensions (D1, D2, D4, D5, D6 — max 15). Ignore any project path. Use the Global Configuration report template only.
  - No `--global` → **Project mode**: audit the project path (or cwd if none given). Score all 8 dimensions (max 24). No global section.
- **Ask the user for confirmation before reading home directory contents** when `--global` is used.
- If the path doesn't exist, report "Directory not found: [path]."
- If the path has no `.claude/` directory AND no `CLAUDE.md` (project mode only), report "No Claude Code configuration found at [path]."

## Workflow

### Phase 1: Structural Scan

Run the deterministic scanner:

```bash
python3 scripts/scan.py <project-path> --json [--global]
```

If the scanner fails (non-zero exit, invalid JSON), stop and report the error to the user. Do not attempt to score manually without scanner output.

This returns JSON with:
- Full inventory of all `.claude/` components
- Structural scores for D1, D2, D3, D4, D7 (and partial D5, D6, D8)
- Anti-pattern detection
- CLAUDE.md content analysis (section headings, linter content, theory paragraphs)

Parse the JSON output. Use the structural scores directly for D1, D2, D3, D4, D7. Dimensions with `score: null` require your semantic evaluation in Phase 2.

### Phase 2: Semantic Evaluation

For dimensions the scanner cannot fully score:

**D5: Skills Setup** — Read each skill's SKILL.md. Does the description explain when to trigger AND when NOT to use? Are `allowed-tools` minimally scoped (no bare `Bash`)? Does the skill use progressive disclosure (references/, scripts/)? Is the description trigger-focused, not generic?

**D6: Agent Configuration** — Read each agent file. Is the model selection appropriate? (haiku for read-only, sonnet for balanced, opus for complex.) Are tools minimally scoped? Does each agent have a clear, distinct purpose?

**D8: Progressive Disclosure** — Holistic judgment: does CLAUDE.md serve as a lean hub that delegates to `.claude/` components? Are path-scoped rules used instead of cramming everything into CLAUDE.md? Is the overall structure proportional to the project's complexity?

Also review D3 and D4 for semantic quality the scanner cannot assess:
- **D3**: Are rule files each focused on a single concern? (Scanner caps at 2; bump to 3 if quality is excellent.)
- **D4**: Are commands genuinely useful team workflows? (Scanner caps at 2; bump to 3 if commands are high-value.)

Adjust a structural score only if you have specific evidence. Note the reason.

### Phase 3: Detect Anti-Patterns

The scanner auto-detects structural anti-patterns. Add semantic ones:
- CLAUDE.md contains content that belongs in linter/formatter configs
- CLAUDE.md has long theory paragraphs (instruction drift)
- Rules files try to cover multiple concerns
- Commands missing `$ARGUMENTS` for parameterization
- Skills with generic descriptions that won't trigger correctly
- Agents with overly broad tool access

### Phase 4: Generate Report

Read `references/report-template.md` and fill the appropriate sections.

**Project mode**: Score all 8 dimensions (D1-D8, max 24). Grade: 21-24=A, 16-20=B, 11-15=C, 6-10=D, 0-5=F.

**Global mode**: Use only the Global Configuration section of the template. Score 5 dimensions (D1, D2, D4, D5, D6 — max 15). Grade: 13-15=A, 10-12=B, 7-9=C, 4-6=D, 0-3=F.

### Phase 5: Actionable Recommendations

For each dimension scoring below 2, provide a specific, actionable recommendation. Prioritize by expected impact (points gained per effort).

Always include Quick Wins — concrete items achievable in under 5 minutes.

## Scoring Dimensions Summary

| Dim | Name | Max | Scanner | Claude |
|-----|------|-----|---------|--------|
| D1 | CLAUDE.md Quality | 3 | Partial (length, sections, linter content) | Content quality, conciseness judgment |
| D2 | Permission Hygiene | 3 | Full | — |
| D3 | Modular Instructions | 3 | Partial (existence, count, path scoping) | Single-concern quality, delegation |
| D4 | Custom Commands | 3 | Partial (frontmatter, $ARGUMENTS, backtick) | Usefulness, workflow coverage |
| D5 | Skills Setup | 3 | Structural signals only | Trigger quality, tool scoping, disclosure |
| D6 | Agent Configuration | 3 | Structural signals only | Model selection, tool scoping, purpose |
| D7 | Git Hygiene | 3 | Full | — |
| D8 | Progressive Disclosure | 3 | Partial (component count) | Holistic organization quality |

## References

- `references/best-practices.md` — 8-dimension scoring rubric with anchors
- `references/report-template.md` — output format template
- `scripts/scan.py` — structural scanner (D1-D4, D7 full; D5, D6, D8 partial)
- `examples/sample-review.md` — complete example report for calibration

## Gotchas

**Projects without .claude/ folder**: Some projects use only a root CLAUDE.md with no .claude/ directory. This is valid for simple projects. Score D2-D6 as 0 but note "Minimal configuration — appropriate for simple/early-stage projects" rather than treating it as a failure.

**Monorepo CLAUDE.md files**: Some projects have CLAUDE.md at multiple levels (root, packages/*, apps/*). Only score the root-level one for D1. Note nested files as a strength.

**Git operations require a git repo**: scan.py's git checks fail on non-git directories. It handles this gracefully (skips git checks, scores D7 as N/A).

**settings.local.json vs settings.json**: The local file should be gitignored; the non-local file should be committed. Don't confuse them.

**Empty .claude/ directories**: Some projects create .claude/ but leave it empty (only settings.local.json from plugin installs). Treat as "no configuration" for scoring.

**Global scope requires confirmation**: When `--global` is used, ask the user before reading `~/.claude/` contents. Home directory contents are personal.
