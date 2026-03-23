# Skill Review Report Template

Use this template for Phase 5 output. Fill every field — never omit a section.

```
# Skill Review: [skill-name]

**Path**: [resolved real path, not symlink]
**Category**: [primary category] (confidence: high/medium/low)
**Version**: [from plugin.json or .claude-plugin/plugin.json, or "unknown"]

## Inventory

| Asset | Count | Details |
|-------|-------|---------|
| SKILL.md | [lines] lines | - |
| References | [N] files | [filenames] |
| Scripts | [N] files | [filenames] |
| Templates | [N] files | [filenames] |
| LEARNINGS.md | yes/no | [entry count if yes] |
| config.json | yes/no | - |
| plugin.json | yes/no | - |

## Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| D1: Progressive Disclosure | [0-3] | [one-line justification] |
| D2: Description Quality | [0-3] | [one-line justification] |
| D3: Gotchas Section | [0-3] | [one-line justification] |
| D4: Don't State the Obvious | [0-3] | [one-line justification] |
| D5: Avoid Railroading | [0-3] | [one-line justification] |
| D6: Setup & Configuration | [0-3] | [one-line justification] |
| D7: Memory & Data Storage | [0-3] | [one-line justification] |
| D8: Scripts & Composable Code | [0-3] | [one-line justification] |
| D9: Frontmatter Quality | [0-3] | [one-line justification] |
| D10: Hooks Integration | [0-2] | [one-line justification] |
| **Total** | **[N]/29** | **Grade: [A/B/C/D/F]** |

Grade thresholds: 25-29 = A, 20-24 = B, 15-19 = C, 10-14 = D, 0-9 = F

## Anti-Patterns Found

[List each detected anti-pattern with specific evidence from the file, or "None detected"]

## Top 3 Strengths

1. [strength with specific quote or file evidence]
2. [strength]
3. [strength]

## Top 3 Improvements

1. **[issue]** - [what to change] - [expected score impact]
2. **[issue]** - [what to change] - [expected score impact]
3. **[issue]** - [what to change] - [expected score impact]

## Quick Fixes (can apply now with --fix)

- [ ] [specific, actionable — e.g., "Add gotchas section after workflow, document the 3 known failure modes"]
- [ ] [fix]

## Comparison to Gold Standard

[Only include this section if a benchmark skill resolves on disk in the current environment.
If no benchmark is available, omit this section entirely — do not infer from memory.
See references/benchmarks.md for which skills qualify as benchmarks and their known paths.]
```
