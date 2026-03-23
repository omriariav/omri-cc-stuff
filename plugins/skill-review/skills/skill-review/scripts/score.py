#!/usr/bin/env python3
"""
Structural scoring for Claude Code skills.

Deterministically scores the dimensions that can be measured from file structure
and content analysis. Leaves semantic dimensions (D4, D5) for Claude.

Usage:
    python3 scripts/score.py <skill-directory>
    python3 scripts/score.py <skill-directory> --json
    python3 scripts/score.py <skill-directory> --verbose

Output: JSON with per-dimension scores, evidence, and detected anti-patterns.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# yaml is optional — fall back to regex extraction
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def parse_frontmatter(skill_md_path: Path) -> dict:
    """Extract YAML frontmatter from SKILL.md.

    Tries PyYAML first. Falls back to line-by-line regex parsing if YAML
    fails (common with multi-line | blocks or unquoted special chars).
    """
    text = skill_md_path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    raw = match.group(1)

    # Try PyYAML first
    if HAS_YAML:
        try:
            result = yaml.safe_load(raw) or {}
            if isinstance(result, dict):
                return result
        except yaml.YAMLError:
            pass

    # Fallback: line-by-line key extraction for common frontmatter fields
    fm = {}
    current_key = None
    current_val_lines = []

    for line in raw.splitlines():
        # Top-level key: value
        kv = re.match(r"^(\w[\w-]*)\s*:\s*(.*)", line)
        if kv and not line.startswith("  "):
            if current_key:
                fm[current_key] = "\n".join(current_val_lines).strip()
            current_key = kv.group(1)
            val = kv.group(2).strip()
            current_val_lines = [val] if val and val != "|" else []
        elif current_key and line.startswith("  "):
            current_val_lines.append(line.strip())

    if current_key:
        fm[current_key] = "\n".join(current_val_lines).strip()

    # Normalize booleans
    for k, v in fm.items():
        if v == "true":
            fm[k] = True
        elif v == "false":
            fm[k] = False

    return fm


def inventory_skill(skill_dir: Path) -> dict:
    """Inventory all files in a skill directory."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {"error": f"No SKILL.md found in {skill_dir}"}

    inv = {
        "skill_md_lines": len(skill_md.read_text(encoding="utf-8").splitlines()),
        "skill_md_bytes": skill_md.stat().st_size,
        "has_learnings": (skill_dir / "LEARNINGS.md").exists(),
        "has_claude_md": (skill_dir / "CLAUDE.md").exists(),
        "has_config": (skill_dir / "config.json").exists(),
        "subfolders": {},
        "total_files": 0,
    }

    for subfolder in ["references", "scripts", "templates", "data", "examples"]:
        sub_path = skill_dir / subfolder
        if sub_path.is_dir():
            files = [f.name for f in sub_path.iterdir() if f.is_file()]
            inv["subfolders"][subfolder] = files
            inv["total_files"] += len(files)
        else:
            inv["subfolders"][subfolder] = []

    # Check for plugin.json
    plugin_json = skill_dir.parent.parent / ".claude-plugin" / "plugin.json"
    inv["has_plugin_json"] = plugin_json.exists()
    if plugin_json.exists():
        try:
            inv["plugin_meta"] = json.loads(plugin_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            inv["plugin_meta"] = None

    return inv


def score_d1_progressive_disclosure(inv: dict) -> dict:
    """D1: Progressive Disclosure (0-3).

    Rubric:
      0 = nothing in any subfolder
      1 = references external files but doesn't own them (no owned subfolders)
      2 = owns references/ OR scripts/ with files
      3 = rich structure: 2+ populated owned subfolders with 5+ total files
    """
    populated = {k: v for k, v in inv["subfolders"].items() if v}
    total_support_files = sum(len(v) for v in populated.values())

    if total_support_files == 0:
        score = 0
        evidence = "No sub-files in any standard subfolder"
    elif len(populated) >= 2 and total_support_files >= 5:
        score = 3
        evidence = f"Rich structure: {', '.join(f'{k}/ ({len(v)})' for k, v in populated.items())}"
    elif len(populated) >= 1:
        # Owning any populated subfolder = score 2 per rubric
        score = 2
        evidence = f"Owns {', '.join(populated.keys())} with {total_support_files} total files"
    else:
        score = 0
        evidence = "No owned subfolders"

    return {"score": score, "max": 3, "evidence": evidence}


def score_d2_description(fm: dict) -> dict:
    """D2: Description Quality (0-3)."""
    desc = fm.get("description", "")
    if not desc:
        return {"score": 0, "max": 3, "evidence": "No description in frontmatter"}

    desc_lower = desc.lower()
    has_triggers = any(
        phrase in desc_lower
        for phrase in ["use when", "use for", "trigger", "invoke when"]
    )
    has_negative = any(
        phrase in desc_lower for phrase in ["not for", "don't use", "not when", "instead use"]
    )

    if has_triggers and has_negative:
        score = 3
        evidence = "Has trigger phrases AND negative cases"
    elif has_triggers:
        score = 2
        evidence = "Has trigger phrases but no negative cases"
    elif len(desc) > 50:
        score = 1
        evidence = "Descriptive but no explicit trigger phrases"
    else:
        score = 0
        evidence = f"Too brief ({len(desc)} chars)"

    return {"score": score, "max": 3, "evidence": evidence}


def score_d3_gotchas(skill_md_path: Path) -> dict:
    """D3: Gotchas Section (0-3)."""
    text = skill_md_path.read_text(encoding="utf-8").lower()

    # Look for dedicated gotchas section
    gotcha_headers = re.findall(
        r"^#{1,3}\s+.*(gotcha|common mistake|pitfall|known issue|caveat|warning|don.t|avoid).*$",
        text,
        re.MULTILINE | re.IGNORECASE,
    )

    # Count specific error/failure documentation
    error_patterns = re.findall(
        r"(?:error|fail|crash|timeout|break|bug|wrong|incorrect).*?(?:because|due to|caused by|fix|solution|workaround|instead)",
        text,
        re.IGNORECASE,
    )

    # D3=3 requires quality judgment (exact messages, root causes, AND fixes) —
    # that cannot be determined structurally. Cap at 2 from script; Claude must
    # bump to 3 manually if the gotchas are genuinely excellent.
    if gotcha_headers and error_patterns:
        score = 2
        evidence = f"Section(s) present ({len(gotcha_headers)}) with {len(error_patterns)} error/fix pattern(s). Review quality for possible 3."
    elif gotcha_headers or len(error_patterns) >= 2:
        score = 2
        evidence = f"Has {len(gotcha_headers)} gotcha header(s), {len(error_patterns)} error pattern(s)"
    elif error_patterns:
        score = 1
        evidence = f"Some error mentions ({len(error_patterns)}) but no dedicated section"
    else:
        score = 0
        evidence = "No gotchas section and no error documentation found"

    return {"score": score, "max": 3, "evidence": evidence}


def _strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks and inline code from text for pattern matching."""
    # Remove fenced code blocks (```...```)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Remove inline code (`...`)
    text = re.sub(r"`[^`]+`", "", text)
    return text


def score_d6_configuration(fm: dict, skill_md_path: Path, inv: dict) -> dict:
    """D6: Setup & Configuration (0-3)."""
    text = skill_md_path.read_text(encoding="utf-8")
    # Check for hardcoded paths outside of code blocks and examples
    prose_text = _strip_code_blocks(text)

    has_config_json = inv["has_config"]
    has_arguments = bool(fm.get("argument-hint", ""))
    # Only flag real hardcoded user paths, not template placeholders like <name>
    hardcoded_matches = re.findall(r"/Users/\w+|/home/\w+|C:\\Users\\\w+", prose_text)
    # Filter out obvious example/template patterns
    hardcoded_matches = [m for m in hardcoded_matches if "specific" not in m.lower()]
    has_hardcoded = bool(hardcoded_matches)

    # First-run detection: the SKILL.md must explicitly describe a flow where
    # the skill checks for missing config and prompts the user. Use prose_text
    # only (not code blocks) and require tight phrases that imply active checking,
    # not incidental section headings or generic "if" statements.
    has_first_run = bool(re.search(
        r"(if config (is missing|not found|does not exist|doesn.t exist)"
        r"|config.*not.*exist"
        r"|first[- ]run"
        r"|missing.*config.*ask"
        r"|no config.*prompt"
        r"|ask.*if.*not.*config)",
        prose_text.lower()
    ))

    if has_hardcoded:
        score = 0
        evidence = "Hardcoded user paths found"
    elif has_config_json and has_first_run:
        score = 3
        evidence = "config.json + first-run detection + graceful prompting"
    elif has_config_json:
        score = 2
        evidence = "config.json with stored preferences (no first-run flow)"
    elif has_arguments:
        score = 1
        evidence = "Argument-based configuration only"
    else:
        score = 0
        evidence = "No configuration mechanism"

    return {"score": score, "max": 3, "evidence": evidence}


def score_d7_memory(inv: dict, skill_md_path: Path) -> dict:
    """D7: Memory & Data Storage (0-3)."""
    text = skill_md_path.read_text(encoding="utf-8").lower()

    has_learnings = inv["has_learnings"]
    has_data = bool(inv["subfolders"].get("data"))
    # Require multi-word persistence phrases to avoid false positives
    # (e.g. bare "append" matching string-formatting code unrelated to memory)
    has_persistence_mentions = any(
        phrase in text for phrase in [
            "sqlite", "json log", "history log", "previous run", "last run",
            "append to", "read.*history", "history.*read", "prior review",
        ]
    ) or bool(re.search(r"appends?\s+(?:a\s+)?(?:new\s+)?(?:entry|log|record|row)", text))

    if has_data and has_persistence_mentions:
        score = 3
        evidence = "data/ directory with persistence patterns in workflow"
    elif has_learnings and has_persistence_mentions:
        score = 2
        evidence = "LEARNINGS.md + persistence awareness"
    elif has_learnings or has_data:
        score = 1
        evidence = "Has storage (LEARNINGS.md or data/) but unclear if read back"
    else:
        score = 0
        evidence = "Stateless - no persistent storage"

    return {"score": score, "max": 3, "evidence": evidence}


def score_d8_scripts(inv: dict) -> dict:
    """D8: Scripts & Composable Code (0-3).

    Rubric:
      0 = no scripts
      1 = references external scripts but doesn't own them
      2 = owns scripts in scripts/ directory (any count)
      3 = library of composable scripts Claude generates code on top of (5+)
    """
    scripts = inv["subfolders"].get("scripts", [])

    if not scripts:
        score = 0
        evidence = "No scripts/ directory"
    elif len(scripts) >= 5:
        score = 3
        evidence = f"Script library: {', '.join(scripts[:5])}..."
    else:
        # Owning any scripts/ files = score 2 per rubric
        score = 2
        evidence = f"{len(scripts)} owned script(s): {', '.join(scripts)}"

    return {"score": score, "max": 3, "evidence": evidence}


def score_d9_frontmatter(fm: dict) -> dict:
    """D9: Frontmatter Quality (0-3)."""
    if not fm:
        return {"score": 0, "max": 3, "evidence": "No valid frontmatter"}

    fields = {
        "name": bool(fm.get("name")),
        "description": bool(fm.get("description")),
        "allowed-tools": bool(fm.get("allowed-tools")),
        "user-invocable": fm.get("user-invocable") is not None,
        "argument-hint": bool(fm.get("argument-hint")),
    }

    present = sum(fields.values())
    missing = [k for k, v in fields.items() if not v]

    # Check tool scoping
    tools_str = fm.get("allowed-tools", "")
    has_unscoped_bash = "Bash" in str(tools_str) and "Bash(" not in str(tools_str)

    # Rubric: score 2 requires the three core fields: name + description + allowed-tools
    core_present = fields["name"] and fields["description"] and fields["allowed-tools"]

    if present == 5 and not has_unscoped_bash:
        score = 3
        evidence = "All 5 fields present, tools properly scoped"
    elif core_present and not has_unscoped_bash:
        issues = [f"missing: {', '.join(missing)}"] if missing else []
        score = 2
        evidence = f"{present}/5 fields. {'; '.join(issues)}" if issues else f"{present}/5 fields"
    elif present >= 3:
        # Has 3+ fields but missing at least one core field
        score = 1
        evidence = f"{present}/5 fields but missing core field(s): {', '.join(k for k in ['name','description','allowed-tools'] if not fields[k])}"
    elif present >= 2:
        score = 1
        evidence = f"Only {present}/5 fields: {', '.join(k for k, v in fields.items() if v)}"
    else:
        score = 0
        evidence = f"Minimal frontmatter ({present}/5 fields)"

    return {"score": score, "max": 3, "evidence": evidence}


def score_d10_hooks(skill_dir: Path) -> dict:
    """D10: Hooks Integration (0-2).

    Only scores positively for actual hook configuration — not mentions
    of the word 'hook' in documentation or gotchas sections.
    """
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8").lower()

    # Look for actual hook configuration patterns, not just discussion
    has_hook_config = any(kw in text for kw in ["pretooluse", "posttooluse"])
    has_hook_file = (skill_dir / "hooks.json").exists() or (skill_dir / ".hooks").exists()

    if has_hook_config or has_hook_file:
        score = 2
        evidence = "Active hook configuration found"
    else:
        score = 0
        evidence = "No hooks configured"

    return {"score": score, "max": 2, "evidence": evidence}


def detect_anti_patterns(skill_md_path: Path, fm: dict, inv: dict) -> list:
    """Detect anti-patterns. Returns list of {name, evidence}."""
    text = skill_md_path.read_text(encoding="utf-8")
    text_lower = text.lower()
    patterns = []

    # Persona-only: mostly role description, no workflows
    step_patterns = len(re.findall(r"(?:step|phase|stage)\s+\d", text_lower))
    if step_patterns == 0 and ("role" in text_lower or "persona" in text_lower or "expert" in text_lower):
        persona_ratio = sum(1 for line in text.splitlines() if any(
            w in line.lower() for w in ["role", "persona", "expert", "years of experience", "framework"]
        )) / max(len(text.splitlines()), 1)
        if persona_ratio > 0.3:
            patterns.append({"name": "persona-only", "evidence": f"{persona_ratio:.0%} of lines are role/persona description"})

    # Script wrapper: too short
    if inv["skill_md_lines"] < 15:
        patterns.append({"name": "script-wrapper", "evidence": f"Only {inv['skill_md_lines']} lines"})

    # Monolithic: >200 lines and no subfolders
    total_support = sum(len(v) for v in inv["subfolders"].values())
    if inv["skill_md_lines"] > 200 and total_support == 0:
        patterns.append({"name": "monolithic", "evidence": f"{inv['skill_md_lines']} lines with 0 support files"})

    # Hardcoded paths (check prose only, not code blocks or examples)
    prose_text = _strip_code_blocks(text)
    hardcoded = re.findall(r"/Users/\w+[/\w.-]+|/home/\w+[/\w.-]+", prose_text)
    hardcoded = [h for h in hardcoded if "specific" not in h.lower()]
    if hardcoded:
        patterns.append({"name": "hardcoded-paths", "evidence": f"Found: {', '.join(set(hardcoded[:3]))}"})

    # No error handling (multi-step with no failure guidance)
    if step_patterns >= 2:
        failure_terms = len(re.findall(r"if (?:it )?fail|error|stop and report|on failure", text_lower))
        if failure_terms == 0:
            patterns.append({"name": "no-error-handling", "evidence": f"{step_patterns} steps but no failure guidance"})

    # No output format — check prose for template/format mentions; code blocks
    # alone (command examples) do not count as defining an output format
    prose_lower = _strip_code_blocks(text).lower()
    produces_output = any(kw in prose_lower for kw in ["output", "report", "generate", "produce", "write to"])
    has_format = any(kw in prose_lower for kw in ["template", "output format", "report format", "schema", "structure"])
    # Also allow: a references/report-template.md file counts as a defined format
    has_format = has_format or bool(inv.get("subfolders", {}).get("references") and
                                     any("template" in f for f in inv["subfolders"].get("references", [])))
    if produces_output and not has_format:
        patterns.append({"name": "no-output-format", "evidence": "Produces output but no format/template defined"})

    # Overpermissioned tools
    tools_str = str(fm.get("allowed-tools", ""))
    if "Bash" in tools_str and "Bash(" not in tools_str:
        patterns.append({"name": "overpermissioned", "evidence": "Unscoped Bash in allowed-tools"})

    # Stale references: check file pointers (only concrete paths, not templates)
    file_refs = re.findall(r"`([^`]+/[^`]+\.\w+)`", text)
    for ref in file_refs:
        # Skip template patterns (<name>, **/glob, ~/, http), variable references ($)
        if any(skip in ref for skip in ["<", ">", "**", "~", "http", "$", "*", "[", "{"]):
            continue
        ref_path = skill_md_path.parent / ref
        if not ref_path.exists():
            patterns.append({"name": "stale-reference", "evidence": f"Referenced file not found: {ref}"})

    return patterns


def load_config() -> dict:
    """Load config.json from skill root. Returns defaults if missing."""
    config_path = Path(__file__).parent.parent / "config.json"
    defaults = {
        "history_log": "~/.claude/plugin-data/skill-review/history.log",
        "default_verbose": False,
        "benchmarks_check": True,
        "auto_fix_threshold": 15,
    }
    try:
        loaded = json.loads(config_path.read_text())
        return {**defaults, **loaded}
    except (OSError, json.JSONDecodeError):
        return defaults


def main():
    config = load_config()

    parser = argparse.ArgumentParser(description="Structural scoring for Claude Code skills")
    parser.add_argument("skill_dir", help="Path to skill directory (containing SKILL.md)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--verbose", action="store_true", help="Show detailed evidence")
    args = parser.parse_args()

    # Apply config defaults (CLI flags override)
    if not args.verbose and config.get("default_verbose"):
        args.verbose = True

    # Resolve symlink exactly once. Do NOT call .resolve() before checking
    # is_symlink() — that would eagerly follow all links.
    raw_path = Path(args.skill_dir)
    if raw_path.is_symlink():
        skill_dir = raw_path.readlink() if hasattr(raw_path, "readlink") else Path(os.readlink(raw_path))
        # Make absolute relative to cwd if needed
        if not skill_dir.is_absolute():
            skill_dir = raw_path.parent / skill_dir
    else:
        skill_dir = raw_path
    skill_dir = skill_dir.resolve()  # normalize . and .. only after one-hop

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(json.dumps({"error": f"No SKILL.md in {skill_dir}"}))
        sys.exit(1)

    # Inventory
    inv = inventory_skill(skill_dir)
    fm = parse_frontmatter(skill_md)

    # Score each dimension
    scores = {
        "D1_progressive_disclosure": score_d1_progressive_disclosure(inv),
        "D2_description_quality": score_d2_description(fm),
        "D3_gotchas": score_d3_gotchas(skill_md),
        "D6_configuration": score_d6_configuration(fm, skill_md, inv),
        "D7_memory": score_d7_memory(inv, skill_md),
        "D8_scripts": score_d8_scripts(inv),
        "D9_frontmatter": score_d9_frontmatter(fm),
        "D10_hooks": score_d10_hooks(skill_dir),
    }

    # Semantic dimensions left for Claude
    scores["D4_dont_state_obvious"] = {"score": None, "max": 3, "evidence": "Requires semantic evaluation by Claude"}
    scores["D5_avoid_railroading"] = {"score": None, "max": 3, "evidence": "Requires semantic evaluation by Claude"}

    # Totals
    structural_total = sum(s["score"] for s in scores.values() if s["score"] is not None)
    structural_max = sum(s["max"] for s in scores.values() if s["score"] is not None)
    full_max = 29

    # Anti-patterns
    anti_patterns = detect_anti_patterns(skill_md, fm, inv)

    fix_suggested = structural_total < config.get("auto_fix_threshold", 15)

    result = {
        "skill": skill_dir.name,
        "path": str(skill_dir),
        "inventory": inv,
        "frontmatter": fm,
        "scores": scores,
        "structural_total": structural_total,
        "structural_max": structural_max,
        "full_max": full_max,
        "anti_patterns": anti_patterns,
        "fix_suggested": fix_suggested,
        "benchmarks_check": config.get("benchmarks_check", True),
        "note": "D4 and D5 require semantic evaluation. Add their scores to structural_total for the full score.",
    }

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        # Pretty table output
        name = result["skill"]
        print(f"\n  Skill Review: {name}")
        print(f"  Path: {result['path']}")
        print(f"  SKILL.md: {inv['skill_md_lines']} lines")
        print()

        print("  Dimension                     Score   Evidence")
        print("  " + "-" * 70)
        for dim_key, dim in sorted(scores.items()):
            label = dim_key.replace("_", " ").replace("D", "D", 1)
            s = dim["score"]
            m = dim["max"]
            score_str = f"{s}/{m}" if s is not None else f"?/{m}"
            ev = dim["evidence"]
            if not args.verbose and len(ev) > 45:
                ev = ev[:42] + "..."
            print(f"  {label:<30}  {score_str:<6}  {ev}")

        print("  " + "-" * 70)
        print(f"  Structural total: {structural_total}/{structural_max}  (D4+D5 pending)")
        print(f"  Full max: {full_max}")
        print()

        if anti_patterns:
            print(f"  Anti-patterns: {len(anti_patterns)} found")
            for ap in anti_patterns:
                print(f"    - {ap['name']}: {ap['evidence']}")
        else:
            print("  Anti-patterns: none detected")
        print()


if __name__ == "__main__":
    main()
