# Skill Review: publisher-lookup

> Example output from `/skill-reviewer publisher-lookup` — use as reference for report quality.

**Path**: `~/Code/taboola-pm-skills/plugins/publisher-lookup/skills/publisher-lookup/`
**Category**: Library & API Reference (confidence: high)
**Version**: 1.0.0

## Inventory

| Asset | Count | Details |
|-------|-------|---------|
| SKILL.md | 52 lines | - |
| references/ | 0 files | - |
| scripts/ | 5 files | get_publisher_master.sql, get_publisher_classification.sql, get_network_hierarchy.sql, get_tier.sql, search_by_name.sql |
| LEARNINGS.md | yes | 3 entries |
| config.json | no | - |
| plugin.json | yes | v1.0.0 |

## Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| D1: Progressive Disclosure | 2/3 | scripts/ well-populated. No references/ or templates/. |
| D2: Description Quality | 2/3 | Has trigger phrases ("Who is publisher X?"). No negative cases. |
| D3: Gotchas Section | 0/3 | No dedicated gotchas section in current SKILL.md. Column-name traps documented in LEARNINGS.md but not surfaced inline. |
| D4: Don't State the Obvious | 3/3 | Everything here is Taboola-specific tribal knowledge: `description` not `name`, advertisers IN publishers table, `has_campaigns=1` filter, FIRED accounts. Claude couldn't know any of this. |
| D5: Avoid Railroading | 2/3 | 4-step workflow with clear branching. Slightly prescriptive on output format. |
| D6: Setup & Configuration | 0/3 | No configuration mechanism. Hardcodes Sage MCP dependency. |
| D7: Memory & Data Storage | 1/3 | LEARNINGS.md exists but workflow does not read it back explicitly. |
| D8: Scripts & Composable Code | 3/3 | 5 SQL scripts Claude composes from. Best example of D8 in the marketplace. |
| D9: Frontmatter Quality | 1/3 | Only name + description (2/5 fields). Missing user-invocable, argument-hint, allowed-tools. |
| D10: Hooks Integration | 0/2 | No hooks. |
| **Total** | **15/29** | **Grade: C** |

## Anti-Patterns Found

- **No output format**: Skill says "return JSON" but no schema defined. The JSON structure in workflow is implicit.

## Top 3 Strengths

1. **D4=3**: Entirely org-specific tribal knowledge — `id` not `publisher_id`, `description` not `name`, advertisers inside the publishers table. Nothing Claude could know without the skill.
2. **D8=3**: SQL scripts as composable primitives. Claude calls `get_publisher_master.sql`, `get_network_hierarchy.sql` separately and merges — clean composition.
3. **LEARNINGS.md discipline**: 3 captured learnings from real failures. This is exactly the pattern to follow.

## Top 3 Improvements

1. **D9=1 → D9=3**: Add `user-invocable: true`, `argument-hint: <publisher-id-or-name>`, `allowed-tools: Read, Bash(python3*)` to frontmatter. +2 pts.
2. **D6=0 → D6=1**: No way to configure which Sage agent or fallback MCP to use. Add `argument-hint` to accept ID or name. +1 pt.
3. **No output format**: Add a JSON schema in references/ or inline at bottom of SKILL.md. +0 pts (anti-pattern, no direct rubric score).

## Quick Fixes

- [ ] Add `user-invocable: true` and `argument-hint: <publisher-id-or-name>` to frontmatter
- [ ] Add `allowed-tools: Read, Bash(python3*)` to frontmatter
- [ ] Define JSON output schema (inline or in references/)
