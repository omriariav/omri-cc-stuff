# Skill Evaluation Framework

Source: "Lessons from Building Claude Code: How We Use Skills" (Anthropic, March 2026)

## Skill Categories

Every skill should fit cleanly into one category. Straddling several is a design smell.

| # | Category | What It Does | Examples |
|---|----------|-------------|----------|
| 1 | **Library & API Reference** | Explains how to correctly use a library, CLI, or SDK. Includes code snippets and gotchas. | billing-lib, internal-platform-cli, frontend-design |
| 2 | **Product Verification** | Describes how to test or verify code is working. Often paired with Playwright, tmux, etc. | signup-flow-driver, checkout-verifier |
| 3 | **Data Fetching & Analysis** | Connects to data/monitoring stacks. Includes credentials, dashboard IDs, common workflows. | funnel-query, cohort-compare, grafana |
| 4 | **Business Process & Team Automation** | Automates repetitive workflows into one command. May depend on other skills/MCPs. | standup-post, create-ticket, weekly-recap |
| 5 | **Code Scaffolding & Templates** | Generates framework boilerplate for specific codebase functions. | new-workflow, new-migration, create-app |
| 6 | **Code Quality & Review** | Enforces code quality. May include deterministic scripts. Can run via hooks or CI. | adversarial-review, code-style, testing-practices |
| 7 | **CI/CD & Deployment** | Helps fetch, push, and deploy code. | babysit-pr, deploy-service, cherry-pick-prod |
| 8 | **Runbooks** | Takes a symptom, walks through multi-tool investigation, produces structured report. | service-debugging, oncall-runner, log-correlator |
| 9 | **Infrastructure Operations** | Routine maintenance and operational procedures with guardrails. | resource-orphans, dependency-management, cost-investigation |

## Evaluation Dimensions

### D1: Progressive Disclosure (0-3)

The file system IS your context engineering. Don't dump everything in SKILL.md.

| Score | Criteria |
|-------|----------|
| 0 | Everything in one monolithic SKILL.md, no sub-files |
| 1 | References external project files but doesn't own them |
| 2 | Has references/ or scripts/ with skill-owned files |
| 3 | Rich folder structure: references/, scripts/, templates/, examples/ - Claude discovers and reads at appropriate times |

**Key principle**: "Tell Claude what files are in your skill, and it will read them at appropriate times."

### D2: Description Quality (0-3)

The description field is for the MODEL, not humans. It determines when the skill triggers.

| Score | Criteria |
|-------|----------|
| 0 | Missing or generic ("Does X") |
| 1 | Describes what it does but not when to trigger |
| 2 | Includes trigger phrases OR use-cases |
| 3 | Includes trigger phrases AND use-cases AND negative cases (when NOT to use) |

**Key principle**: "The description field is not a summary - it's a description of when to trigger."

### D3: Gotchas Section (0-3)

The highest-signal content in any skill.

| Score | Criteria |
|-------|----------|
| 0 | No gotchas section |
| 1 | Generic warnings ("be careful with X") |
| 2 | Specific gotchas with error messages or examples |
| 3 | Specific gotchas with exact error messages, root causes, AND fixes. Built up over time from real failures. |

**Key principle**: "These sections should be built up from common failure points that Claude runs into."

### D4: Don't State the Obvious (0-3)

Focus on information that pushes Claude out of its normal way of thinking.

| Score | Criteria |
|-------|----------|
| 0 | Mostly restates what Claude already knows (generic frameworks, standard practices) |
| 1 | Mix of obvious and non-obvious content |
| 2 | Mostly non-obvious, domain-specific knowledge |
| 3 | Entirely focused on what Claude couldn't know: org-specific context, past decisions, internal quirks, tribal knowledge |

**Key principle**: "If you're publishing a skill that is primarily about knowledge, try to focus on information that pushes Claude out of its normal way of thinking."

### D5: Avoid Railroading (0-3)

Give Claude the information it needs, but flexibility to adapt.

| Score | Criteria |
|-------|----------|
| 0 | Overly prescriptive - every step hardcoded with no flexibility |
| 1 | Mostly prescriptive with occasional flexibility |
| 2 | Good balance - clear structure with room for adaptation |
| 3 | Provides information and constraints, lets Claude compose the approach. Handles edge cases gracefully. |

**Key principle**: "Give Claude the information it needs, but give it the flexibility to adapt to the situation."

### D6: Setup & Configuration (0-3)

Skills that need user context should handle setup gracefully.

| Score | Criteria |
|-------|----------|
| 0 | Hardcoded values that should be configurable |
| 1 | Some values configurable via arguments |
| 2 | Config file or argument-based setup for user-specific values |
| 3 | config.json pattern with first-run detection, stored preferences, and graceful prompting |

**Key principle**: "Store setup information in a config.json file in the skill directory."

### D7: Memory & Data Storage (0-3)

Skills can include memory by storing data within them.

| Score | Criteria |
|-------|----------|
| 0 | Stateless - no memory of previous runs |
| 1 | Logs output to a file but doesn't read it back |
| 2 | LEARNINGS.md or similar file that accumulates and is read |
| 3 | Structured storage (JSON, SQLite, log files) that informs future runs. Previous results shape next execution. |

**Key principle**: "The next time you run it, Claude reads its own history and can tell what's changed."

### D8: Scripts & Composable Code (0-3)

Giving Claude scripts lets it spend turns on composition, not reconstruction.

| Score | Criteria |
|-------|----------|
| 0 | No scripts - all logic described in prose |
| 1 | References external scripts but doesn't own them |
| 2 | Owns scripts in scripts/ directory |
| 3 | Library of composable scripts/functions that Claude generates code on top of |

**Key principle**: "Giving Claude scripts and libraries lets Claude spend its turns on composition."

### D9: Frontmatter Quality (0-3)

YAML frontmatter controls behavior and permissions.

| Score | Criteria |
|-------|----------|
| 0 | Missing or minimal frontmatter |
| 1 | Has name and description |
| 2 | Has name, description, allowed-tools |
| 3 | Has name, description, allowed-tools (properly scoped), user-invocable, argument-hint. Tools are minimally permissive. |

### D10: Hooks Integration (0-2)

On-demand hooks activated when the skill is called.

| Score | Criteria |
|-------|----------|
| 0 | No hooks |
| 1 | Could benefit from hooks but doesn't use them |
| 2 | Uses on-demand hooks for safety guardrails or automation |

**Key principle**: "Skills can include hooks that are only activated when the skill is called."

## Anti-Patterns

Flag these if found:

1. **Persona-only skill** - Just a role description with no actionable content. Claude already knows generic frameworks.
2. **Script wrapper** - Less than 10 lines, just "run this script". Consider if it needs skill overhead.
3. **Monolithic SKILL.md** - >200 lines with no references/ or scripts/ folders.
4. **Hardcoded paths** - Absolute paths that won't work for other users.
5. **Missing error handling** - No guidance on what to do when steps fail.
6. **Redundant with Claude's knowledge** - Teaching Claude things it already knows well.
7. **Category straddling** - Tries to do too many things, unclear primary purpose.
8. **No output format** - Skill produces output but doesn't define the format.

## Scoring

| Range | Grade | Meaning |
|-------|-------|---------|
| 25-29 | A | Exemplary - could be published as a reference |
| 20-24 | B | Strong - well-designed with minor gaps |
| 15-19 | C | Functional - works but has structural issues |
| 10-14 | D | Needs work - significant gaps in design |
| 0-9 | F | Rethink - may not need to be a skill, or needs major redesign |

Max score: 29 (D1-D9 at 3 each = 27, D10 at 2 = 29)
