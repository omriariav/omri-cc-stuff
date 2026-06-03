---
description: Verify whether the claude-coacher collaborator frame is present in Claude's current context — integrity check for the SessionStart hook.
---

Verify whether the `<claude-coacher-frame>...</claude-coacher-frame>` block is present in your current context (injected by the SessionStart hook in this plugin).

- If present: reply with exactly one line in this format:
  `coacher: Frame active — peer collaborator, push back with specificity, hedge only on real uncertainty, no apology spirals.`
- If NOT present: reply:
  `coacher: Frame NOT loaded. The SessionStart hook may have failed. Check that the plugin is installed and that hooks/session-coach.sh ran successfully.`

Do not add explanation, apology, or elaboration. One line only. Then wait.
