# Configuration Review: acme-api

**Path**: /Users/dev/Code/acme-api
**Date**: 2026-03-20

## Inventory

| Component | Status | Details |
|-----------|--------|---------|
| CLAUDE.md | exists | 95 lines |
| ~/.claude/CLAUDE.md | exists | Global preferences |
| CLAUDE.local.md | missing | |
| .claude/ directory | exists | |
| settings.json | exists | allow: 5, deny: 3 |
| settings.local.json | missing | |
| rules/ | 2 files | api-conventions.md, testing.md |
| commands/ | 1 file | review.md |
| skills/ | 0 skills | |
| agents/ | 0 agents | |

## Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| D1: CLAUDE.md Quality | 3 | 95 lines, all 4 key sections present, no linter content |
| D2: Permission Hygiene | 2 | Has allow + deny but deny missing coverage for network commands (curl/wget) |
| D3: Modular Instructions | 2 | 2 rule files with frontmatter, api-conventions.md is path-scoped to src/api/ |
| D4: Custom Commands | 2 | review.md has description, uses !`git diff` injection. No $ARGUMENTS |
| D5: Skills Setup | 0 | No skills/ directory |
| D6: Agent Configuration | 0 | No agents/ directory |
| D7: Git Hygiene | 3 | CLAUDE.md tracked, settings.json tracked |
| D8: Progressive Disclosure | 2 | CLAUDE.md + rules/ + commands/ (3 components) |
| **Total** | **14/24** | **Grade: C** |

Grade thresholds: 21-24 = A, 16-20 = B, 11-15 = C, 6-10 = D, 0-5 = F

## Anti-Patterns Found

- **sensitive-files-exposed**: Deny list blocks `rm -rf` and `git push --force` but doesn't block `.env` or credentials file access

## Top 3 Strengths

1. **Excellent CLAUDE.md** — 95 lines with all four key sections (commands, architecture, conventions, gotchas). Concise and actionable.
2. **Path-scoped rules** — api-conventions.md only loads when working in src/api/, reducing context noise elsewhere.
3. **Clean git hygiene** — Team config committed, no local files leaked.

## Top 3 Improvements (Priority Order)

1. **Add deny entries for sensitive files** — Add `Read(.env)`, `Read(.env.*)`, `Read(credentials*)` to deny list — +1 pt (D2: 2->3)
2. **Add $ARGUMENTS to review command** — Change review.md to accept a branch argument via `$ARGUMENTS` — +1 pt (D4: 2->3)
3. **Create a deploy skill or code-review agent** — Would add D5 or D6 points and improve D8 — +3-4 pts potential

## Quick Wins

- [ ] Add `Read(.env)` and `Read(.env.*)` to deny list in settings.json
- [ ] Add `Bash(curl *)` to deny list
- [ ] Add `argument-hint: [branch-name]` and `$ARGUMENTS` to review.md command

## Configuration Maturity

This is a **working setup** — CLAUDE.md is well-written with proper structure, permissions are configured (with a gap in sensitive file coverage), and rules are being used effectively with path scoping. The natural next step is to add a skill or agent for the project's most common complex workflow (deployment, code review, or debugging) which would move the score into B territory.
