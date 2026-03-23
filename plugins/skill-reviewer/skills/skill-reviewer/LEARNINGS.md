# Learnings

Captured gotchas and patterns from real usage of `/skill-review`.

## Gotchas

**YAML frontmatter with `|` blocks and special chars fails PyYAML**
Multi-line descriptions using `|` combined with values containing `[`, `]`, `|` (common in argument-hint) cause PyYAML to throw. The fallback regex parser in score.py handles this — but Claude should also be aware when manually reading frontmatter.

**Stale references are noisy for project-local skills**
Skills like `interview-kit` that reference project-relative paths (`projects/hr/...`) will always show stale-reference anti-patterns when run from the skill directory. This is expected — those skills depend on the project context. Filter: if >5 stale refs and all follow the same path prefix, note it as "project-local dependency" not a real stale reference.

**D7=0 is correct for pure reasoning skills — don't inflate**
Initial rubric penalized stateless skills. score.py correctly assigns D7=0 for skills with no persistence. Only suggest LEARNINGS.md if the skill genuinely produces reusable cross-run outputs.

**Keyword classification produces false positives**
"PR" appears in both CI/CD and Runbooks skills. "template" appears in Scaffolding and Business Process. Always read the surrounding paragraph before classifying. If still ambiguous, mark confidence "low".

**D10 keyword detection false positive on "hook"**
First version of score.py scored D10=1 for any skill that mentioned "hook" (including in gotchas or documentation sections). Fixed to require actual `pretooluse`/`posttooluse` config or a `hooks.json` file.

## Patterns That Work

**Pre-scoring with score.py before semantic evaluation**: Running `python3 scripts/score.py <dir>` first gives the structural baseline in seconds. Claude then only needs to add D4 and D5 judgments, not re-derive all 10 dimensions from scratch.

**Codex as pre-merge reviewer**: Submitting the skill to codex review before merging caught 7 real issues (argument grammar, score math, filesystem traversal bounds, D7 bias). Worth running on any new skill before publishing.

## Version History

| Date | Change | Source |
|------|--------|--------|
| 2026-03-17 | Initial creation | skill-review v1.0.0 |
| 2026-03-17 | Added D7/D10 false positive fixes | codex review |
| 2026-03-17 | Added score.py structural pre-scorer | self-evaluation |
