# Claude Code Configuration Best Practices

Scoring rubric for evaluating a project's `.claude/` folder setup.
Source: "Anatomy of the .claude/ folder" guidance and patterns from well-configured projects.

## D1: CLAUDE.md Quality (0-3)

CLAUDE.md is the project's instruction manual for Claude. It should be concise, actionable, and focused on what Claude can't infer from code alone.

| Score | Criteria |
|-------|----------|
| 0 | No CLAUDE.md exists |
| 1 | Exists but too long (>200 lines), missing key sections, or contains linter/theory content |
| 2 | Concise (<200 lines), has build/test commands AND architecture/conventions. Minor issues acceptable |
| 3 | Lean (<150 lines), all 4 key sections present, no linter content, no theory paragraphs. Aware of CLAUDE.local.md |

**Key sections:**
- Build/test/lint commands (how to run the project)
- Architecture decisions (folder structure, key patterns)
- Conventions (naming, code style beyond linters)
- Gotchas (project-specific pitfalls)

**Content that does NOT belong:**
- Linter/formatter configurations (belongs in .eslintrc, prettier.config, etc.)
- Full API documentation (link to it instead)
- Long theory paragraphs about methodology
- Information Claude already knows (standard library usage, common patterns)

## D2: Permission Hygiene (0-3)

settings.json controls what Claude can do. Balance safety with usability.

| Score | Criteria |
|-------|----------|
| 0 | No .claude/settings.json exists |
| 1 | settings.json exists but no allow/deny lists |
| 2 | Has allow OR deny list (but not both) |
| 3 | Both allow AND deny. Deny blocks destructive commands (rm -rf), network (curl/wget), and sensitive files (.env). Allow covers safe operations |

**Critical deny entries:**
- `Bash(rm -rf *)` — destructive deletion
- `Bash(curl *)`, `Bash(wget *)` — network exfiltration
- `Read(.env)`, `Read(.env.*)` — credentials exposure

**Good allow entries:**
- `Bash(npm run *)` or `Bash(make *)` — project scripts
- `Bash(git status)`, `Bash(git diff *)` — read-only git
- `Read`, `Write`, `Edit`, `Glob`, `Grep` — file operations

## D3: Modular Instructions (0-3)

Rules files split CLAUDE.md into focused, maintainable pieces. Path-scoped rules are especially powerful.

| Score | Criteria |
|-------|----------|
| 0 | No .claude/rules/ directory or empty |
| 1 | Has rule files but no frontmatter or path scoping |
| 2 | Rule files have proper frontmatter, each focused on one concern |
| 3 | Uses path scoping (paths: frontmatter), single-concern files, CLAUDE.md delegates detailed instructions to rules/ |

**Best practices:**
- Split when CLAUDE.md exceeds ~150 lines
- One concern per file (testing.md, api-conventions.md, security.md)
- Use `paths:` frontmatter to scope rules to specific directories
- Descriptive filenames (not rule-1.md, rule-2.md)

## D4: Custom Commands (0-3)

Commands give the team reusable slash-command workflows.

| Score | Criteria |
|-------|----------|
| 0 | No .claude/commands/ directory |
| 1 | Commands exist but lack frontmatter or are trivially simple |
| 2 | Commands have `description` frontmatter and are genuinely useful |
| 3 | Commands use `$ARGUMENTS` for parameterization, `!backtick` syntax for dynamic context, cover common workflows |

**Best practices:**
- `description` frontmatter is required (shows in /help)
- `argument-hint` tells users what to pass
- `$ARGUMENTS` makes commands flexible
- `` !`command` `` syntax injects live context (git diff, test output)

## D5: Skills Setup (0-3)

Skills are auto-invoked workflows with progressive disclosure.

| Score | Criteria |
|-------|----------|
| 0 | No .claude/skills/ directory |
| 1 | Skills exist but minimal SKILL.md (no frontmatter, no supporting files) |
| 2 | Proper frontmatter (name, description, allowed-tools), some supporting files |
| 3 | Full progressive disclosure: trigger-focused descriptions, references/, scripts/, minimally-scoped tools |

**Key frontmatter fields:**
- `name`, `description` (trigger-focused with positive AND negative cases)
- `allowed-tools` (scoped, e.g., `Bash(python3*)` not bare `Bash`)
- `user-invocable`, `argument-hint`

## D6: Agent Configuration (0-3)

Agents are subagent personas with dedicated tool access and model selection.

| Score | Criteria |
|-------|----------|
| 0 | No .claude/agents/ directory |
| 1 | Agents exist but lack proper frontmatter or use overly broad tools |
| 2 | Agents have name, description, model, tools with reasonable scoping |
| 3 | Model selection appropriate (haiku for read-only, sonnet for balanced, opus for complex). Tools minimally scoped. Clear purpose |

**Model selection guide:**
- haiku: read-only analysis, quick lookups, formatting
- sonnet: balanced tasks, code review, moderate complexity
- opus: complex reasoning, multi-step workflows, architectural decisions

## D7: Git Hygiene (0-3)

Team config must be committed. Personal config must be gitignored.

| Score | Criteria |
|-------|----------|
| 0 | Not a git repo, or local files committed (security risk) |
| 1 | Some files correctly handled but gaps |
| 2 | Most files correct |
| 3 | All correct: CLAUDE.md tracked, settings.json tracked, CLAUDE.local.md gitignored, settings.local.json gitignored |

**Should be committed (team-shared):**
- `CLAUDE.md`, `.claude/settings.json`, `.claude/rules/*`, `.claude/commands/*`

**Should be gitignored (personal):**
- `CLAUDE.local.md`, `.claude/settings.local.json`

## D8: Progressive Disclosure (0-3)

The overall .claude/ structure should follow progressive disclosure: CLAUDE.md is the lean entry point, detailed instructions live in rules/, reusable workflows in commands/ and skills/.

| Score | Criteria |
|-------|----------|
| 0 | Only CLAUDE.md (or nothing), no .claude/ structure |
| 1 | CLAUDE.md + one .claude/ component |
| 2 | CLAUDE.md + 2-3 populated .claude/ components |
| 3 | Full ecosystem: lean CLAUDE.md hub + rules/ + commands/ + skills/ or agents/. CLAUDE.md under 150 lines with delegation |

## Anti-Patterns

| Pattern | Description |
|---------|-------------|
| monolithic-claude-md | >200 lines with no rules/ to split into |
| no-permissions | No settings.json or empty permissions |
| no-deny-list | settings.json exists but no deny list |
| sensitive-files-exposed | Deny list doesn't block .env/credentials |
| linter-in-claude-md | Config that belongs in tool-specific files |
| local-files-committed | CLAUDE.local.md or settings.local.json in git |
| team-config-not-committed | settings.json exists but not tracked |
| theory-paragraphs | Long prose blocks that don't give actionable instruction |
| commands-no-frontmatter | Commands missing description frontmatter |

## Grading

| Range | Grade | Meaning |
|-------|-------|---------|
| 21-24 | A | Exemplary — well-organized, secure, team-ready |
| 16-20 | B | Strong — good foundation with minor gaps |
| 11-15 | C | Functional — works but missing key components |
| 6-10  | D | Needs work — significant gaps |
| 0-5   | F | Minimal — needs major setup |
