# claude-coacher

A Claude Code plugin (name: `coacher`) that primes Claude with a collaborator frame at session start, and gives you four focused commands for mid-session re-anchoring, integrity checks, CLAUDE.md conflict auditing, and frustration-to-productive translation.

## Why

Based on Amanda Askell's prompting philosophy, summarized in [this thread](https://x.com/itsolelehmann/status/2045578185950040390) by Ole Lehmann:

> How you talk to Claude affects its work just as much as what you say.
>
> Newer Claude models suffer from "criticism spirals" — they expect you'll come in harsh, so they default to playing it safe. When the model is spending its energy on self-protection, the actual work suffers. Output comes out hedgier, more apologetic, blander, and the worst of all: overly agreeable (even when you're wrong).
>
> Every message you send is data the model reads to figure out what kind of person it's dealing with. Open cold and hostile, and it braces. Open clean and direct, and it relaxes into the work.

### The playbook (from the thread)

1. **Use positive framing.** *"Write in short punchy sentences"* beats *"don't write long sentences."* Strings of "don't do this, don't do that" push the model into paranoid over-checking.
2. **Give it explicit permission to disagree.** *"Push back if you see a better angle."* Without this, Claude defaults to agreeable compliance.
3. **Open with respect.** Your first message sets the tone for the whole session.
4. **Don't reprimand it when it messes up.** Insults reinforce the anxious mode.
5. **Kill apology spirals fast.** *"All good, here's what I want next."* Letting the spiral run reinforces it for every response that follows.
6. **Ask for opinions alongside execution.** *"What would you do here?"* *"What's missing?"* assumes competence.
7. **In long sessions, refresh the frame.** A periodic *"this is great, keep going"* measurably shifts the next ten responses.

This plugin ships points **1, 2, 5, and 7** automatically — so you don't have to remember to hand-write the collaborator frame every session, and you have a quick command to re-anchor mid-session.

Points 3, 4, and 6 are user-behavior changes a plugin can't enforce without being nagging. They're yours to work on.

## What it does

### SessionStart hook → injects the frame

`frame.md` is loaded into every new session's context via `hookSpecificOutput.additionalContext`. The default frame tells Claude:

- It's a peer collaborator, not a subservient assistant.
- Push back with specificity when there's a concrete reason; don't perform independence.
- Hedge only on real uncertainty; no filler qualifiers.
- Acknowledge mistakes in one sentence and move on — no apology spirals.
- If the user cuts a spiral short (*"all good, keep going"*), accept it and proceed.

### Four slash commands

| Command | What it does |
|---|---|
| `/coacher:status` | Claude self-checks whether the frame block is in its current context — integrity check for the hook |
| `/coacher:audit` | Cross-checks `frame.md` against any `CLAUDE.md` content in context; flags stance-layer conflicts/overlaps with file+line evidence |
| `/coacher:reset` | Re-anchors the frame mid-session (useful when Claude has drifted into hedging) |
| `/coacher:rant <text>` | You say what you actually want, unfiltered. Claude extracts the intent, shows a one-line clean restatement, and executes under the frame |

**Rant example:**

```
/coacher:rant this goddamn parser keeps swallowing valid input, figure it out
```

Claude replies:

```
→ Debug why the parser is rejecting valid input and fix the root cause.
[proceeds with the task]
```

No lecture about tone. No meta-commentary. Translation happens silently, the work continues under the frame.

## Install

From inside any Claude Code session:

```
/plugin marketplace add https://github.com/omriariav/claude-coacher
/plugin install coacher
/reload-plugins
```

Note the plugin name is `coacher` (the repo is `claude-coacher` but the installable plugin name is shorter).

Or clone into the local plugin cache directly:

```bash
git clone https://github.com/omriariav/claude-coacher ~/.claude/plugins/cache/claude-coacher
```

After install you should see this banner at session start:

```
coacher: collaborator frame loaded (use /coacher:reset to re-anchor or /coacher:rant to translate a vent)
```

## Verify

After installing, in a fresh session:

```
/coacher:status
```

Expected reply: `coacher: Frame active — peer collaborator, push back with specificity, hedge only on real uncertainty, no apology spirals.`

If you see `Frame NOT loaded` instead, the SessionStart hook didn't fire. Check:
1. The plugin is in `~/.claude/plugins/cache/`
2. `hooks/session-coach.sh` is executable (`chmod +x`)
3. `python3` is on `$PATH`

## Customize

Edit `frame.md` to tailor the stance for your workflow. The full contents between `<claude-coacher-frame>...</claude-coacher-frame>` are injected verbatim into every new session; everything outside those tags is ignored.

Ideas:

- **Brainstorming sessions** — emphasize exploration and weaker-signal suggestions.
- **Production / infra work** — tighten "push back" to require high-confidence concerns only.
- **Writing / editing** — add domain-specific tone guidance.

### Reconciling with `CLAUDE.md`

`frame.md` and `CLAUDE.md` coexist in context — neither overrides the other mechanically. Split them by layer:

| | `CLAUDE.md` | `frame.md` |
|---|---|---|
| **Scope** | project context, tools, conventions, your role, tech stack | stance: tone, pushback policy, hedging, apology policy |
| **Changes when** | the project changes | you want different coaching (brainstorm vs. prod) |

If you already have stance/tone directives in `CLAUDE.md`, run `/coacher:audit` — Claude will cross-check and flag any overlaps or contradictions, with file+line evidence.

## Structure

```
claude-coacher/
├── .claude-plugin/
│   ├── plugin.json              plugin manifest (name: coacher)
│   └── marketplace.json         single-plugin marketplace manifest
├── frame.md                     editable collaborator frame (injected verbatim)
├── hooks/
│   ├── hooks.json               SessionStart hook registration
│   └── session-coach.sh         extracts the frame block and emits additionalContext
└── commands/
    ├── status.md                /coacher:status
    ├── audit.md                 /coacher:audit
    ├── reset.md                 /coacher:reset
    └── rant.md                  /coacher:rant <text>
```

No skills, no agents, no background state. One hook, four small commands.

## Design rationale

- The core problem is real at session-setup time, mostly mitigated by a clean SessionStart context injection. In-session tone effects are smaller and harder to fix without paternalism — so we don't try.
- UserPromptSubmit hooks that flag or rewrite your messages were considered and cut: users resent them, and they'd become the nagging thing the plugin exists to prevent.
- Apology-spiral detection on PostToolUse/Stop was cut: signal is noisy, and mid-task intervention is awkward. `/coacher:reset` is the manual alternative.
- Skills were considered and rejected: skills are for Claude-discovered, semantically-matched invocation. Frame injection must always fire (hook). The four `/coacher:*` commands are always user-imperative (slash commands).

## Credits

- Amanda Askell (Anthropic) — the underlying collaboration-stance philosophy.
- Ole Lehmann — the [X thread](https://x.com/itsolelehmann/status/2045578185950040390) this plugin operationalizes.
- Design reviewed against `/document-skills:skill-creator`, `/claude-reviewer`, and PR-reviewed, with a second-opinion pass from Codex.
