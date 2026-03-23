#!/usr/bin/env python3
"""
Structural scanner for Claude Code project configuration.

Inventories a project's .claude/ folder and CLAUDE.md, scores 8 dimensions
of configuration quality, and detects anti-patterns. Leaves semantic
evaluation (D5, D6, D8 partially) to Claude.

Usage:
    python3 scripts/scan.py <project-directory>
    python3 scripts/scan.py <project-directory> --json
    python3 scripts/scan.py <project-directory> --global
    python3 scripts/scan.py <project-directory> --json --global
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_frontmatter(md_path: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    try:
        text = md_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}

    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    raw = match.group(1)

    if HAS_YAML:
        try:
            result = yaml.safe_load(raw) or {}
            if isinstance(result, dict):
                return result
        except yaml.YAMLError:
            pass

    # Fallback: line-by-line
    fm = {}
    current_key = None
    current_val_lines = []

    for line in raw.splitlines():
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

    for k, v in fm.items():
        if v == "true":
            fm[k] = True
        elif v == "false":
            fm[k] = False

    return fm


def git_cmd(project_dir: Path, *args: str) -> tuple[int, str]:
    """Run a git command in the project directory. Returns (returncode, stdout)."""
    try:
        result = subprocess.run(
            ["git", "-C", str(project_dir)] + list(args),
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 1, ""


def is_git_repo(project_dir: Path) -> bool:
    rc, _ = git_cmd(project_dir, "rev-parse", "--is-inside-work-tree")
    return rc == 0


def is_gitignored(project_dir: Path, rel_path: str) -> bool:
    rc, _ = git_cmd(project_dir, "check-ignore", "-q", rel_path)
    return rc == 0


def is_tracked(project_dir: Path, rel_path: str) -> bool:
    rc, out = git_cmd(project_dir, "ls-files", rel_path)
    return rc == 0 and out.strip() != ""


def list_md_files(directory: Path) -> list[str]:
    """List .md files in a directory."""
    if not directory.is_dir():
        return []
    return sorted(f.name for f in directory.iterdir() if f.is_file() and f.suffix == ".md")


def list_skill_dirs(skills_dir: Path) -> list[dict]:
    """Inventory each skill subdirectory."""
    if not skills_dir.is_dir():
        return []
    results = []
    for sub in sorted(skills_dir.iterdir()):
        if not sub.is_dir():
            continue
        skill_md = sub / "SKILL.md"
        info = {
            "name": sub.name,
            "has_skill_md": skill_md.exists(),
            "has_references": (sub / "references").is_dir(),
            "has_scripts": (sub / "scripts").is_dir(),
            "frontmatter": parse_frontmatter(skill_md) if skill_md.exists() else {},
        }
        results.append(info)
    return results


def list_agent_files(agents_dir: Path) -> list[dict]:
    """Inventory each agent definition file."""
    if not agents_dir.is_dir():
        return []
    results = []
    for f in sorted(agents_dir.iterdir()):
        if not f.is_file() or f.suffix != ".md":
            continue
        fm = parse_frontmatter(f)
        results.append({
            "name": f.stem,
            "frontmatter": fm,
            "has_name": bool(fm.get("name")),
            "has_description": bool(fm.get("description")),
            "has_model": bool(fm.get("model")),
            "has_tools": bool(fm.get("tools")),
        })
    return results


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

def inventory_project(project_dir: Path) -> dict:
    """Full inventory of a project's Claude Code configuration."""
    claude_md = project_dir / "CLAUDE.md"
    claude_local_md = project_dir / "CLAUDE.local.md"
    claude_dir = project_dir / ".claude"
    settings_json = claude_dir / "settings.json"
    settings_local = claude_dir / "settings.local.json"
    rules_dir = claude_dir / "rules"
    commands_dir = claude_dir / "commands"
    skills_dir = claude_dir / "skills"
    agents_dir = claude_dir / "agents"
    home_claude_md = Path.home() / ".claude" / "CLAUDE.md"

    inv = {
        "project_name": project_dir.name,
        "project_path": str(project_dir),
    }

    # CLAUDE.md
    if claude_md.exists():
        try:
            text = claude_md.read_text(encoding="utf-8")
            lines = text.splitlines()
            inv["claude_md"] = {
                "exists": True,
                "lines": len(lines),
                "bytes": claude_md.stat().st_size,
            }
        except (OSError, UnicodeDecodeError):
            inv["claude_md"] = {"exists": True, "lines": 0, "bytes": 0}
    else:
        inv["claude_md"] = {"exists": False, "lines": 0, "bytes": 0}

    inv["global_claude_md"] = {"exists": home_claude_md.exists()}
    inv["claude_local_md"] = {"exists": claude_local_md.exists()}
    inv["claude_dir"] = {"exists": claude_dir.is_dir()}

    # settings.json
    if settings_json.exists():
        try:
            settings = json.loads(settings_json.read_text(encoding="utf-8"))
            perms = settings.get("permissions", {})
            inv["settings_json"] = {
                "exists": True,
                "has_schema": bool(settings.get("$schema")),
                "has_allow": bool(perms.get("allow")),
                "has_deny": bool(perms.get("deny")),
                "allow_entries": perms.get("allow", []),
                "deny_entries": perms.get("deny", []),
            }
        except (json.JSONDecodeError, OSError):
            inv["settings_json"] = {"exists": True, "has_schema": False,
                                     "has_allow": False, "has_deny": False,
                                     "allow_entries": [], "deny_entries": []}
    else:
        inv["settings_json"] = {"exists": False, "has_schema": False,
                                 "has_allow": False, "has_deny": False,
                                 "allow_entries": [], "deny_entries": []}

    inv["settings_local_json"] = {"exists": settings_local.exists()}

    # Rules
    rule_files = list_md_files(rules_dir)
    path_scoped = 0
    for rf in rule_files:
        fm = parse_frontmatter(rules_dir / rf)
        if fm.get("paths"):
            path_scoped += 1
    inv["rules"] = {
        "exists": rules_dir.is_dir(),
        "count": len(rule_files),
        "files": rule_files,
        "path_scoped_count": path_scoped,
    }

    # Commands
    cmd_files = list_md_files(commands_dir)
    with_frontmatter = 0
    with_arguments = 0
    with_backtick = 0
    for cf in cmd_files:
        fp = commands_dir / cf
        fm = parse_frontmatter(fp)
        if fm.get("description"):
            with_frontmatter += 1
        try:
            content = fp.read_text(encoding="utf-8")
            if "$ARGUMENTS" in content:
                with_arguments += 1
            if "!`" in content:
                with_backtick += 1
        except (OSError, UnicodeDecodeError):
            pass
    inv["commands"] = {
        "exists": commands_dir.is_dir(),
        "count": len(cmd_files),
        "files": cmd_files,
        "with_frontmatter": with_frontmatter,
        "with_arguments": with_arguments,
        "with_backtick": with_backtick,
    }

    # Skills
    skill_details = list_skill_dirs(skills_dir)
    inv["skills"] = {
        "exists": skills_dir.is_dir(),
        "count": len(skill_details),
        "details": skill_details,
    }

    # Agents
    agent_details = list_agent_files(agents_dir)
    inv["agents"] = {
        "exists": agents_dir.is_dir(),
        "count": len(agent_details),
        "details": agent_details,
    }

    return inv


def inventory_global() -> dict:
    """Inventory ~/.claude/ global configuration."""
    home_claude = Path.home() / ".claude"
    inv = {"path": str(home_claude)}

    claude_md = home_claude / "CLAUDE.md"
    if claude_md.exists():
        text = claude_md.read_text(encoding="utf-8")
        inv["claude_md"] = {"exists": True, "lines": len(text.splitlines()), "bytes": claude_md.stat().st_size}
    else:
        inv["claude_md"] = {"exists": False, "lines": 0, "bytes": 0}

    settings_json = home_claude / "settings.json"
    if settings_json.exists():
        try:
            settings = json.loads(settings_json.read_text(encoding="utf-8"))
            perms = settings.get("permissions", {})
            inv["settings_json"] = {
                "exists": True,
                "has_schema": bool(settings.get("$schema")),
                "has_allow": bool(perms.get("allow")),
                "has_deny": bool(perms.get("deny")),
                "allow_entries": perms.get("allow", []),
                "deny_entries": perms.get("deny", []),
            }
        except (json.JSONDecodeError, OSError):
            inv["settings_json"] = {"exists": True, "has_schema": False,
                                     "has_allow": False, "has_deny": False,
                                     "allow_entries": [], "deny_entries": []}
    else:
        inv["settings_json"] = {"exists": False, "has_schema": False,
                                 "has_allow": False, "has_deny": False,
                                 "allow_entries": [], "deny_entries": []}

    commands_dir = home_claude / "commands"
    cmd_files = list_md_files(commands_dir)
    inv["commands"] = {"exists": commands_dir.is_dir(), "count": len(cmd_files), "files": cmd_files}

    skills_dir = home_claude / "skills"
    skill_details = list_skill_dirs(skills_dir)
    inv["skills"] = {"exists": skills_dir.is_dir(), "count": len(skill_details), "details": skill_details}

    agents_dir = home_claude / "agents"
    agent_details = list_agent_files(agents_dir)
    inv["agents"] = {"exists": agents_dir.is_dir(), "count": len(agent_details), "details": agent_details}

    return inv


# ---------------------------------------------------------------------------
# CLAUDE.md analysis
# ---------------------------------------------------------------------------

def analyze_claude_md(project_dir: Path) -> dict:
    """Deep analysis of CLAUDE.md content."""
    claude_md = project_dir / "CLAUDE.md"
    if not claude_md.exists():
        return {"exists": False}

    try:
        text = claude_md.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"exists": True, "lines": 0, "sections_found": 0}
    text_lower = text.lower()
    lines = text.splitlines()

    # Section detection via headings
    has_commands = bool(re.search(
        r"^#{1,3}\s+.*(command|build|test|lint|run|script|install).*$",
        text, re.MULTILINE | re.IGNORECASE,
    ))
    has_architecture = bool(re.search(
        r"^#{1,3}\s+.*(architecture|structure|design|stack|layout|overview).*$",
        text, re.MULTILINE | re.IGNORECASE,
    ))
    has_conventions = bool(re.search(
        r"^#{1,3}\s+.*(convention|style|naming|pattern|rule|standard).*$",
        text, re.MULTILINE | re.IGNORECASE,
    ))
    has_gotchas = bool(re.search(
        r"^#{1,3}\s+.*(gotcha|caveat|warning|watch out|don.t|avoid|pitfall|note).*$",
        text, re.MULTILINE | re.IGNORECASE,
    ))

    # Anti-pattern: linter/formatter config in CLAUDE.md
    linter_patterns = re.findall(
        r"(eslint|prettier|tsconfig|\.eslintrc|stylelint|pylint|flake8|black\s+config|rubocop)",
        text_lower,
    )

    # Anti-pattern: theory paragraphs (5+ consecutive non-empty lines with no
    # code block, list, or heading)
    theory_count = 0
    consecutive_prose = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith(("#", "-", "*", ">", "`", "|", "```")):
            consecutive_prose += 1
        else:
            if consecutive_prose >= 5:
                theory_count += 1
            consecutive_prose = 0
    if consecutive_prose >= 5:
        theory_count += 1

    return {
        "exists": True,
        "lines": len(lines),
        "has_commands": has_commands,
        "has_architecture": has_architecture,
        "has_conventions": has_conventions,
        "has_gotchas": has_gotchas,
        "sections_found": sum([has_commands, has_architecture, has_conventions, has_gotchas]),
        "linter_content": linter_patterns,
        "theory_paragraphs": theory_count,
    }


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_d1_claude_md(inv: dict, analysis: dict) -> dict:
    """D1: CLAUDE.md Quality (0-3). Structural portion."""
    if not inv["claude_md"]["exists"]:
        return {"score": 0, "max": 3, "evidence": "No CLAUDE.md found"}

    line_count = inv["claude_md"]["lines"]
    sections = analysis.get("sections_found", 0)
    has_linter = bool(analysis.get("linter_content"))
    has_theory = analysis.get("theory_paragraphs", 0) > 0

    issues = []
    if line_count > 200:
        issues.append(f"too long ({line_count} lines, recommended <200)")
    if has_linter:
        issues.append(f"linter config found: {', '.join(analysis['linter_content'][:3])}")
    if has_theory:
        issues.append(f"{analysis['theory_paragraphs']} theory paragraph(s)")

    if not issues and sections >= 4 and line_count <= 150:
        score = 3
        evidence = f"Lean ({line_count} lines), {sections}/4 key sections, no anti-patterns"
    elif sections >= 2 and line_count <= 200 and not has_linter:
        score = 2
        evidence = f"{line_count} lines, {sections}/4 key sections"
        if issues:
            evidence += f". Minor: {'; '.join(issues)}"
    elif inv["claude_md"]["exists"]:
        score = 1
        evidence = f"{line_count} lines, {sections}/4 key sections"
        if issues:
            evidence += f". Issues: {'; '.join(issues)}"
    else:
        score = 0
        evidence = "No CLAUDE.md"

    return {"score": score, "max": 3, "evidence": evidence}


def score_d2_permissions(inv: dict) -> dict:
    """D2: Permission Hygiene (0-3). Fully structural."""
    sj = inv["settings_json"]
    if not sj["exists"]:
        return {"score": 0, "max": 3, "evidence": "No .claude/settings.json"}

    if not sj["has_allow"] and not sj["has_deny"]:
        return {"score": 1, "max": 3, "evidence": "settings.json exists but no allow/deny configured"}

    if not sj["has_allow"] or not sj["has_deny"]:
        which = "allow" if sj["has_allow"] else "deny"
        return {"score": 2, "max": 3, "evidence": f"Has {which} list but missing {'deny' if which == 'allow' else 'allow'}"}

    # Both present — check deny quality
    deny_str = " ".join(str(d) for d in sj["deny_entries"]).lower()
    blocks_destructive = any(term in deny_str for term in ["rm -rf", "rm -r", "force"])
    blocks_network = any(term in deny_str for term in ["curl", "wget"])
    blocks_env = any(term in deny_str for term in [".env", "credentials", "secrets"])

    deny_quality = sum([blocks_destructive, blocks_network, blocks_env])
    if deny_quality == 3:
        score = 3
        evidence = f"Allow ({len(sj['allow_entries'])}) + Deny ({len(sj['deny_entries'])}), blocks destructive + network + sensitive"
    else:
        missing = []
        if not blocks_destructive:
            missing.append("destructive commands")
        if not blocks_network:
            missing.append("network commands")
        if not blocks_env:
            missing.append("sensitive files")
        score = 2
        evidence = f"Allow + Deny present but deny missing coverage for: {', '.join(missing)}"

    return {"score": score, "max": 3, "evidence": evidence}


def score_d3_rules(inv: dict) -> dict:
    """D3: Modular Instructions (0-3). Partial — Claude adds semantic evaluation."""
    rules = inv["rules"]
    if not rules["exists"] or rules["count"] == 0:
        return {"score": 0, "max": 3, "evidence": "No .claude/rules/ or empty"}

    score = 1  # base: has files
    evidence_parts = [f"{rules['count']} rule file(s)"]

    if rules["path_scoped_count"] > 0:
        score += 1
        evidence_parts.append(f"{rules['path_scoped_count']} path-scoped")

    # Check if files have frontmatter (at least half)
    fm_count = 0
    rules_dir = Path(inv.get("project_path", ".")) / ".claude" / "rules"
    if rules_dir.is_dir():
        for rf in rules["files"]:
            fm = parse_frontmatter(rules_dir / rf)
            if fm:
                fm_count += 1

    if fm_count > 0:
        evidence_parts.append(f"{fm_count} with frontmatter")
        if score < 2:
            score = 2

    # Cap structural at 2; Claude evaluates single-concern quality for 3
    if score > 2:
        score = 2

    return {"score": score, "max": 3, "evidence": ". ".join(evidence_parts) + ". Review quality for possible 3."}


def score_d4_commands(inv: dict) -> dict:
    """D4: Custom Commands (0-3). Partial."""
    cmds = inv["commands"]
    if not cmds["exists"] or cmds["count"] == 0:
        return {"score": 0, "max": 3, "evidence": "No .claude/commands/ or empty"}

    score = 1  # base: has files
    evidence_parts = [f"{cmds['count']} command(s)"]

    if cmds["with_frontmatter"] > 0:
        score = 2
        evidence_parts.append(f"{cmds['with_frontmatter']} with description frontmatter")

    if cmds["with_arguments"] > 0:
        evidence_parts.append(f"{cmds['with_arguments']} use $ARGUMENTS")
    if cmds["with_backtick"] > 0:
        evidence_parts.append(f"{cmds['with_backtick']} use !backtick injection")

    if cmds["with_frontmatter"] > 0 and cmds["with_arguments"] > 0:
        # Cap structural at 2; Claude evaluates usefulness for 3
        score = 2
        evidence_parts.append("Review usefulness for possible 3")

    return {"score": min(score, 2), "max": 3, "evidence": ". ".join(evidence_parts)}


def score_d5_skills(inv: dict) -> dict:
    """D5: Skills Setup (0-3). Mostly semantic — returns structural data."""
    skills = inv["skills"]
    if not skills["exists"] or skills["count"] == 0:
        return {"score": 0, "max": 3, "evidence": "No .claude/skills/ or empty"}

    # Structural signals
    with_skill_md = sum(1 for s in skills["details"] if s["has_skill_md"])
    with_refs = sum(1 for s in skills["details"] if s["has_references"])
    with_scripts = sum(1 for s in skills["details"] if s["has_scripts"])
    with_fm = sum(1 for s in skills["details"] if s["frontmatter"])

    evidence = (f"{skills['count']} skill(s): {with_skill_md} with SKILL.md, "
                f"{with_fm} with frontmatter, {with_refs} with references/, "
                f"{with_scripts} with scripts/")

    if with_skill_md == 0:
        return {"score": 0, "max": 3, "evidence": evidence}

    # Provide structural score hint but defer to Claude
    if with_fm > 0 and (with_refs > 0 or with_scripts > 0):
        return {"score": None, "max": 3, "evidence": evidence + ". Structural signals strong — semantic eval needed for final score."}

    return {"score": None, "max": 3, "evidence": evidence + ". Requires semantic evaluation."}


def score_d6_agents(inv: dict) -> dict:
    """D6: Agent Configuration (0-3). Mostly semantic."""
    agents = inv["agents"]
    if not agents["exists"] or agents["count"] == 0:
        return {"score": 0, "max": 3, "evidence": "No .claude/agents/ or empty"}

    with_name = sum(1 for a in agents["details"] if a["has_name"])
    with_desc = sum(1 for a in agents["details"] if a["has_description"])
    with_model = sum(1 for a in agents["details"] if a["has_model"])
    with_tools = sum(1 for a in agents["details"] if a["has_tools"])

    evidence = (f"{agents['count']} agent(s): {with_name} with name, {with_desc} with description, "
                f"{with_model} with model, {with_tools} with tools")

    return {"score": None, "max": 3, "evidence": evidence + ". Requires semantic evaluation."}


def score_d7_git(project_dir: Path, inv: dict) -> dict:
    """D7: Git Hygiene (0-3). Fully structural."""
    if not is_git_repo(project_dir):
        return {"score": None, "max": 3, "evidence": "Not a git repository — skipped"}

    checks = {}

    # Team files should be committed
    if inv["claude_md"]["exists"]:
        checks["CLAUDE.md tracked"] = is_tracked(project_dir, "CLAUDE.md")
    if inv["settings_json"]["exists"]:
        checks["settings.json tracked"] = is_tracked(project_dir, ".claude/settings.json")

    # Personal files should be gitignored (or not exist)
    if inv["claude_local_md"]["exists"]:
        checks["CLAUDE.local.md gitignored"] = is_gitignored(project_dir, "CLAUDE.local.md")
    if inv["settings_local_json"]["exists"]:
        checks["settings.local.json gitignored"] = is_gitignored(project_dir, ".claude/settings.local.json")

    if not checks:
        return {"score": 0, "max": 3, "evidence": "No config files to check"}

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)

    # Critical: local files actually tracked in git is a failure
    local_committed = False
    if inv["claude_local_md"]["exists"] and is_tracked(project_dir, "CLAUDE.local.md"):
        local_committed = True
    if inv["settings_local_json"]["exists"] and is_tracked(project_dir, ".claude/settings.local.json"):
        local_committed = True

    if local_committed:
        score = 0
        evidence = "Local config files tracked in git (security risk)"
    elif passed == total:
        score = 3
        evidence = f"All {total} checks pass: {', '.join(checks.keys())}"
    elif passed >= total * 0.6:
        score = 2
        failed = [k for k, v in checks.items() if not v]
        evidence = f"{passed}/{total} checks pass. Failed: {', '.join(failed)}"
    else:
        score = 1
        failed = [k for k, v in checks.items() if not v]
        evidence = f"Only {passed}/{total} checks pass. Failed: {', '.join(failed)}"

    return {"score": score, "max": 3, "evidence": evidence}


def score_d8_disclosure(inv: dict) -> dict:
    """D8: Progressive Disclosure (0-3). Partial — Claude adds holistic judgment."""
    components = []
    if inv["rules"]["exists"] and inv["rules"]["count"] > 0:
        components.append("rules/")
    if inv["commands"]["exists"] and inv["commands"]["count"] > 0:
        components.append("commands/")
    if inv["skills"]["exists"] and inv["skills"]["count"] > 0:
        components.append("skills/")
    if inv["agents"]["exists"] and inv["agents"]["count"] > 0:
        components.append("agents/")

    has_claude_md = inv["claude_md"]["exists"]
    line_count = inv["claude_md"].get("lines", 0)

    if not has_claude_md and not components:
        return {"score": 0, "max": 3, "evidence": "No CLAUDE.md and no .claude/ components"}

    if not components:
        evidence = f"Only CLAUDE.md ({line_count} lines), no .claude/ components"
        if line_count > 150:
            evidence += " — monolithic, would benefit from rules/"
        return {"score": 0 if not has_claude_md else 1, "max": 3, "evidence": evidence}

    # Structural score based on component count
    if len(components) >= 3:
        score = 2  # Claude bumps to 3 if delegation is well-structured
        evidence = f"CLAUDE.md + {len(components)} components: {', '.join(components)}. Review delegation quality for possible 3."
    elif len(components) >= 1:
        score = 1 if len(components) == 1 else 2
        evidence = f"CLAUDE.md + {len(components)} component(s): {', '.join(components)}"
    else:
        score = 1
        evidence = "CLAUDE.md only"

    # Flag monolithic anti-pattern
    if line_count > 150 and inv["rules"]["count"] == 0:
        evidence += f". Warning: CLAUDE.md is {line_count} lines with no rules/ to offload"

    return {"score": score, "max": 3, "evidence": evidence}


# ---------------------------------------------------------------------------
# Anti-patterns
# ---------------------------------------------------------------------------

def detect_anti_patterns(project_dir: Path, inv: dict, analysis: dict) -> list:
    """Detect configuration anti-patterns."""
    patterns = []

    # Monolithic CLAUDE.md
    line_count = inv["claude_md"].get("lines", 0)
    if line_count > 200 and inv["rules"]["count"] == 0:
        patterns.append({
            "name": "monolithic-claude-md",
            "evidence": f"CLAUDE.md is {line_count} lines with no .claude/rules/ to split into",
        })

    # No permissions
    if not inv["settings_json"]["exists"]:
        patterns.append({
            "name": "no-permissions",
            "evidence": "No .claude/settings.json — Claude has no permission boundaries",
        })
    elif not inv["settings_json"]["has_deny"]:
        patterns.append({
            "name": "no-deny-list",
            "evidence": "settings.json exists but no deny list — destructive commands are not blocked",
        })

    # Sensitive files exposed
    if inv["settings_json"]["exists"] and inv["settings_json"]["has_deny"]:
        deny_str = " ".join(str(d) for d in inv["settings_json"]["deny_entries"]).lower()
        if ".env" not in deny_str and "credentials" not in deny_str and "secret" not in deny_str:
            patterns.append({
                "name": "sensitive-files-exposed",
                "evidence": "Deny list doesn't block .env, credentials, or secrets files",
            })

    # Linter config in CLAUDE.md
    if analysis.get("linter_content"):
        patterns.append({
            "name": "linter-in-claude-md",
            "evidence": f"Found linter/formatter config references: {', '.join(analysis['linter_content'][:3])}",
        })

    # Local files committed
    if is_git_repo(project_dir):
        if inv["claude_local_md"]["exists"] and not is_gitignored(project_dir, "CLAUDE.local.md"):
            if is_tracked(project_dir, "CLAUDE.local.md"):
                patterns.append({
                    "name": "local-files-committed",
                    "evidence": "CLAUDE.local.md is tracked in git (should be gitignored)",
                })
        if inv["settings_local_json"]["exists"] and not is_gitignored(project_dir, ".claude/settings.local.json"):
            if is_tracked(project_dir, ".claude/settings.local.json"):
                patterns.append({
                    "name": "local-files-committed",
                    "evidence": "settings.local.json is tracked in git (should be gitignored)",
                })

        # Team config not committed
        if inv["settings_json"]["exists"] and not is_tracked(project_dir, ".claude/settings.json"):
            patterns.append({
                "name": "team-config-not-committed",
                "evidence": ".claude/settings.json exists but is not tracked in git",
            })

    # Theory paragraphs
    if analysis.get("theory_paragraphs", 0) > 0:
        patterns.append({
            "name": "theory-paragraphs",
            "evidence": f"{analysis['theory_paragraphs']} block(s) of 5+ consecutive prose lines in CLAUDE.md",
        })

    # Commands without frontmatter
    cmds = inv["commands"]
    if cmds["count"] > 0 and cmds["with_frontmatter"] == 0:
        patterns.append({
            "name": "commands-no-frontmatter",
            "evidence": f"{cmds['count']} command(s) but none have description frontmatter",
        })

    return patterns


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Structural scanner for Claude Code configuration")
    parser.add_argument("project_dir", nargs="?", default=".",
                        help="Path to project directory (ignored in --global mode)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--verbose", action="store_true", help="Show detailed evidence")
    parser.add_argument("--global", dest="scan_global", action="store_true",
                        help="Scan ONLY ~/.claude/ global configuration")
    args = parser.parse_args()

    # Global-only mode
    if args.scan_global:
        global_inv = inventory_global()
        result = {
            "mode": "global",
            "path": str(Path.home() / ".claude"),
            "inventory": global_inv,
            "note": "Global-only mode. Scores require semantic evaluation by Claude.",
        }
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            gi = global_inv
            print("\n  Global Configuration Review: ~/.claude/")
            print(f"  CLAUDE.md: {'yes' if gi['claude_md']['exists'] else 'no'}" +
                  (f" ({gi['claude_md']['lines']} lines)" if gi['claude_md']['exists'] else ""))
            print(f"  settings.json: {'yes' if gi['settings_json']['exists'] else 'no'}")
            print(f"  commands/: {gi['commands']['count']} file(s)")
            print(f"  skills/: {gi['skills']['count']} skill(s)")
            print(f"  agents/: {gi['agents']['count']} agent(s)")
            print()
        return

    # Project mode
    project_dir = Path(args.project_dir).resolve()
    if not project_dir.is_dir():
        print(json.dumps({"error": f"Not a directory: {project_dir}"}))
        sys.exit(1)

    # Inventory
    inv = inventory_project(project_dir)
    analysis = analyze_claude_md(project_dir)

    # Score each dimension
    scores = {
        "D1_claude_md_quality": score_d1_claude_md(inv, analysis),
        "D2_permission_hygiene": score_d2_permissions(inv),
        "D3_modular_instructions": score_d3_rules(inv),
        "D4_custom_commands": score_d4_commands(inv),
        "D5_skills_setup": score_d5_skills(inv),
        "D6_agent_configuration": score_d6_agents(inv),
        "D7_git_hygiene": score_d7_git(project_dir, inv),
        "D8_progressive_disclosure": score_d8_disclosure(inv),
    }

    # Totals
    structural_total = sum(s["score"] for s in scores.values() if s["score"] is not None)
    structural_max = sum(s["max"] for s in scores.values() if s["score"] is not None)
    full_max = 24

    # Anti-patterns
    anti_patterns = detect_anti_patterns(project_dir, inv, analysis)

    result = {
        "mode": "project",
        "project": project_dir.name,
        "path": str(project_dir),
        "inventory": inv,
        "claude_md_analysis": analysis,
        "scores": scores,
        "structural_total": structural_total,
        "structural_max": structural_max,
        "full_max": full_max,
        "anti_patterns": anti_patterns,
        "note": "Dimensions with score=null require semantic evaluation by Claude.",
    }

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        name = result["project"]
        print(f"\n  Claude Config Review: {name}")
        print(f"  Path: {result['path']}")
        if inv["claude_md"]["exists"]:
            print(f"  CLAUDE.md: {inv['claude_md']['lines']} lines")
        else:
            print("  CLAUDE.md: not found")
        print()

        print("  Dimension                     Score   Evidence")
        print("  " + "-" * 72)
        for dim_key, dim in sorted(scores.items()):
            label = dim_key.replace("_", " ").replace("D", "D", 1)
            s = dim["score"]
            m = dim["max"]
            score_str = f"{s}/{m}" if s is not None else f"?/{m}"
            ev = dim["evidence"]
            if not args.verbose and len(ev) > 45:
                ev = ev[:42] + "..."
            print(f"  {label:<30}  {score_str:<6}  {ev}")

        print("  " + "-" * 72)
        print(f"  Structural total: {structural_total}/{structural_max}  (semantic dims pending)")
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
