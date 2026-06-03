---
description: Cross-check the coacher frame against any CLAUDE.md content in context and flag stance-layer conflicts or overlaps with file+line evidence.
---

Cross-check the `<claude-coacher-frame>` block in your current context against any `CLAUDE.md` content also in your context (user global, project, and local CLAUDE.md files that were loaded at session start).

Scope of the check — look for stance/behavior directives in CLAUDE.md that overlap or clash with the frame's stance on:
- hedging and uncertainty language
- apology behavior after mistakes
- push-back / disagreement policy
- concise-vs-verbose tone
- cautious-vs-direct default

For each conflict or overlap found, output:
```
[conflict|overlap] — <short label>
  CLAUDE.md: "<exact quoted line>"  (source: <file path>)
  frame.md:  "<exact quoted line>"
  why:       <one sentence on the tension>
  suggest:   <move to frame / remove from CLAUDE.md / leave as-is with note>
```

Distinguish:
- **conflict** — directives pull in opposite directions (e.g., "always hedge carefully" vs. "do not pre-emptively hedge")
- **overlap** — same directive expressed in both places (not wrong, but duplicated — suggest consolidating to frame.md so the plugin owns the stance layer)

If no conflicts or overlaps: reply exactly
`coacher: No conflicts detected between frame.md and CLAUDE.md — they cover distinct layers.`

Do not flag CLAUDE.md content that is purely project/context/tooling (file paths, tech stack, user role, conventions) — only the stance/tone layer is in scope. Do not edit any files from this command; audit only.
