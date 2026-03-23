# Gold Standard Benchmark Skills

Only use these for comparison if they resolve on disk in the current environment.
Check existence before referencing. If a skill is missing, skip it — do not infer from memory.

## interview-kit

**Expected path**: `[project-root]/.claude/skills/interview-kit/`
**Why it's a benchmark**:
- Rich references/ folder (rubric, question bank, interview structure, output template, greenhouse scorecard)
- Three distinct modes via flags (--score, default prep, --debrief)
- Progressive disclosure - SKILL.md delegates to references/, Claude reads them when needed
- Detailed per-step failure guidance embedded in workflow

**Scores (reference)**: D1=3, D2=3, D3=2, D9=3

## publisher-lookup

**Expected path**: `~/Code/taboola-pm-skills/plugins/publisher-lookup/skills/publisher-lookup/`
**Why it's a benchmark**:
- SQL scripts in scripts/ directory (composable, reusable)
- Dedicated gotchas section with specific column-name traps
- Clear JSON output format defined
- Handles edge cases: advertiser = publisher in ID space, FIRED accounts, dual classification

**Scores (reference)**: D1=2, D3=0, D7=1, D8=3, D9=1

> Note: score.py is authoritative — these reference scores may drift as skills evolve. Always re-run the script.

## debrief (yaklar project)

**Expected path**: `~/Code/yaklar/.claude/skills/debrief/`
**Why it's a benchmark**:
- 6-step pipeline with explicit error handling at each step
- Parallel agent orchestration with defined output schema
- Skip-ahead shortcut (`/debrief <path>`) for partial re-runs
- Command notepad integration for operator-supplied context

**Scores (reference)**: D1=1, D5=3, D8=2, D9=3

## How to use benchmarks

When a benchmark is available, add a "Comparison to Gold Standard" section showing:
- Which benchmark was used (name + resolved path)
- 2-3 specific things the reviewed skill does better
- 2-3 specific things the reviewed skill could adopt from the benchmark
