# Claude Code Configuration Review Template

Fill every section. Never omit a section.

---

# Configuration Review: [project-name]

**Path**: [absolute project path]
**Date**: [YYYY-MM-DD]

## Inventory

| Component | Status | Details |
|-----------|--------|---------|
| CLAUDE.md | [exists/missing] | [N lines] |
| ~/.claude/CLAUDE.md | [exists/missing] | Global preferences |
| CLAUDE.local.md | [exists/missing] | Personal overrides |
| .claude/ directory | [exists/missing] | |
| settings.json | [exists/missing] | [allow: N, deny: N] |
| settings.local.json | [exists/missing] | |
| rules/ | [N files] | [filenames] |
| commands/ | [N files] | [filenames] |
| skills/ | [N skills] | [skill names] |
| agents/ | [N agents] | [agent names] |

## Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| D1: CLAUDE.md Quality | [0-3] | [one-line justification] |
| D2: Permission Hygiene | [0-3] | [one-line justification] |
| D3: Modular Instructions | [0-3] | [one-line justification] |
| D4: Custom Commands | [0-3] | [one-line justification] |
| D5: Skills Setup | [0-3] | [one-line justification] |
| D6: Agent Configuration | [0-3] | [one-line justification] |
| D7: Git Hygiene | [0-3] | [one-line justification] |
| D8: Progressive Disclosure | [0-3] | [one-line justification] |
| **Total** | **[N]/24** | **Grade: [A/B/C/D/F]** |

Grade thresholds: 21-24 = A, 16-20 = B, 11-15 = C, 6-10 = D, 0-5 = F

## Anti-Patterns Found

[List each detected anti-pattern with specific evidence, or "None detected"]

## Top 3 Strengths

1. [strength with specific evidence]
2. [strength]
3. [strength]

## Top 3 Improvements (Priority Order)

1. **[issue]** — [what to change] — [expected score impact: +N pts]
2. **[issue]** — [what to change] — [expected score impact: +N pts]
3. **[issue]** — [what to change] — [expected score impact: +N pts]

## Quick Wins

Actionable items that can be done in under 5 minutes:

- [ ] [specific actionable item]
- [ ] [item]
- [ ] [item]

## Configuration Maturity

[One paragraph: is this a minimal setup (just getting started), a working setup
(covers basics), or a mature setup (full ecosystem)? What's the natural next
step for this project's maturity level?]

---

## Global Configuration (~/.claude/)

> Only include this section if `--global` was used.

| Component | Status | Details |
|-----------|--------|---------|
| CLAUDE.md | [exists/missing] | [N lines] |
| settings.json | [exists/missing] | [allow: N, deny: N] |
| commands/ | [N files] | [filenames] |
| skills/ | [N skills] | [skill names] |
| agents/ | [N agents] | [agent names] |

### Global Mini-Scores (applicable dimensions only)

| Dimension | Score | Notes |
|-----------|-------|-------|
| D1: CLAUDE.md Quality | [0-3] | |
| D2: Permission Hygiene | [0-3] | |
| D4: Custom Commands | [0-3] | |
| D5: Skills Setup | [0-3] | |
| D6: Agent Configuration | [0-3] | |
| **Total** | **[N]/15** | |

### Global Recommendations

[Specific recommendations for improving the global configuration]
