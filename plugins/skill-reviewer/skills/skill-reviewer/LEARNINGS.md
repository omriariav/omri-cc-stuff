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

**D3 false-negative: gotchas under a non-"Gotchas" heading**
score.py initially scored `gdoc-math` D3=0 (no gotchas) because its failure modes (gfm reader won't parse `$` math, complex-LaTeX fidelity loss, the Drive-write side-effect) were documented under a limitations-framed heading rather than `Gotchas`/`Common Mistakes`. score.py keys on those heading names plus error keywords, so it misses failure docs filed under a differently-named section. When the body documents real failures under any heading, adjust D3 up semantically (partial = 1, full error→cause→fix from real usage = 3) and note the reason. (The skill was later given an explicit `## Common mistakes` section, which score.py then detected.)

**D1 false positive: references/ owned by a deprecated sibling skill**
score.py scored the `amq-squad` compatibility-router skill D1=2 ("owns references with 4 total files") — but the router's own body says "do not run setup ... from this router", and no skill in the plugin (including `wizard`, which actually composes rosters and team rules) points at those four templates. Owning files is not progressive disclosure; being *pointed at* is. When a skill's `references/` are unreachable from any body text, adjust D1 down to 1 and surface it as orphaned assets.

**Undetected anti-pattern: spec-prose skill wrapping a rich CLI**
The four amq-squad skills (275 lines total, 2 code fences; `cli` and `orchestrator` have zero) restate invariants the Go binary already enforces ("readiness fails closed when...", "task completion atomically records one exact completion generation") without ever naming the command that produces them — 51 CLI verbs exist, ~10 are named, and `next` (the binary's one-shot "what should the operator do now", with a documented action-object contract) appears in none. score.py cannot see this: it scores structure, not whether normative prose is paired with an executable. Useful diagnostic ratio for any CLI-wrapper skill: **normative tokens (never/must/always/require) per 100 lines vs. code fences per 100 lines.** amq-squad ran 13 vs. 1; the amq-cli benchmark ran 4 vs. 8. An inverted ratio means the model re-derives the command surface every turn.

**Check for a rich guide outside the skill before recommending new content**
amq-squad already had `docs/skills.md` — 755 lines, 22 fences, a which-skill-do-I-reach-for table, an operator-primitive decision table, and a symptom→cause→exact-fix troubleshooting table (amq-cli-grade content). No SKILL.md linked to it, and the guide's closing line pointed *back* at the thin SKILL.md files. Before writing "author references/", grep the repo for `docs/*skill*`, `README`, or a `docs/` guide: the fix is often extraction-and-linking, not authoring.

**Rubric artifact: CLI-wrapper skills cap around C**
D6 (config), D7 (memory), D8 (scripts), and D10 (hooks) all legitimately score 0–1 for a skill documenting someone else's binary, since the binary owns state, config, and guardrails. The amq-cli benchmark still only totalled 15/29. For this skill class, treat D2/D3/D4/D5 as the signal and report the relative gap, not the absolute grade.

**stale-reference false positive on runtime artifacts**
score.py flagged `wizard`'s mention of `.amq-squad/team.json` as a stale reference. That path is a runtime artifact the CLI creates in the *user's project*, not a skill-owned asset. When a flagged path is something the documented tool writes at runtime, discard the flag.

**no-output-format false positive on verbatim-passthrough contracts**
score.py flagged `orchestrator` as "produces output but no format/template defined" — but the skill's explicit output contract is "print CLI output verbatim in a fenced block; never re-render". A passthrough rule IS the output format; score.py only recognizes owned templates. Override semantically.

**D9 evidence bug: "5/5 fields but missing core field(s): <empty>"**
On all three amq-squad skills score.py emitted D9=1 with an empty missing-fields list while every core field (name, description, allowed-tools, argument-hint, user-invocable) was present. Score D9 manually when the evidence string self-contradicts; the real deduction there was only unscoped `Bash` (→ 2, not 1).

**D8=1, not 0, for CLI-wrapper skills**
The D8 anchor for 1 is "references external scripts but doesn't own them." A skill whose whole purpose is composing a rich external binary (amq-squad) satisfies that anchor even with no scripts/ dir. score.py can only see the directory, so it under-scores this class by one point.

**no-output-format false positive when the format lives under `## Output` in plain prose**
publisher-lookup defines its output precisely ("Return results as JSON with sections: master data, classification, ...") under a `## Output` heading, but score.py's `has_format` keys on the words template/"output format"/schema/structure — none present — so it flagged no-output-format. When a section enumerates the exact fields/sections of the result, that IS a defined format; override the flag.

**cleaner_checks duplicate keep-priority can invert source of truth**
The duplicates signal (keep-priority: plugin > personal > repo) labeled the taboola-pm-skills plugin source tree "repo" and recommended keeping `~/.claude/skills/publisher-lookup` — a stale Feb 2026 hand-copy still mandating the retired `mcp__sage__execute`, 4 versions behind the plugin. Root-class priority is a heuristic only: before acting on a duplicate recommendation, compare mtimes and content (retired tools, missing sections) and keep the maintained source, which for marketplace plugins is the repo/plugin tree. Stale personal-dir copies also explain "I fixed the skill but it still fails" — the old copy keeps triggering.

**Pre-scoring with score.py before semantic evaluation**: Running `python3 scripts/score.py <dir>` first gives the structural baseline in seconds. Claude then only needs to add D4 and D5 judgments, not re-derive all 10 dimensions from scratch.

**Codex as pre-merge reviewer**: Submitting the skill to codex review before merging caught 7 real issues (argument grammar, score math, filesystem traversal bounds, D7 bias). Worth running on any new skill before publishing.

## Version History

| Date | Change | Source |
|------|--------|--------|
| 2026-03-17 | Initial creation | skill-review v1.0.0 |
| 2026-03-17 | Added D7/D10 false positive fixes | codex review |
| 2026-03-17 | Added score.py structural pre-scorer | self-evaluation |
| 2026-07-26 | Added CLI-wrapper gotchas: orphaned references/ D1 false positive, spec-prose anti-pattern + normative:fence ratio, check-for-external-guide, C-cap rubric artifact | amq-squad vs amq-cli review |
| 2026-08-06 | Added runtime-artifact stale-ref FP, verbatim-passthrough output-format FP, D9 empty-missing-fields bug, D8=1 anchor for CLI wrappers | amq-squad v2.28.1 re-review |
| 2026-09-01 | Added `## Output` prose-format FP, duplicate keep-priority inversion (stale personal copy vs plugin source) | publisher-lookup v1.0.4 review |
