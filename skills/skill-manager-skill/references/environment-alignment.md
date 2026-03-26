# Environment Alignment Guide

This guide explains how `skill-manager-skill` manages cross-platform path alignment and how to resolve common issues.

## Why Path Alignment Matters

Different AI IDEs use different directories to discover skills:

| IDE / Agent | Primary Skills Path |
| :--- | :--- |
| Antigravity | `~/.gemini/antigravity/skills/` |
| Claude Code | `~/.claude/skills/` |
| Cursor | `~/.cursor/skills/` or `.cursor/rules/` |
| Universal | `~/.agents/skills/` |
| Windsurf | `~/.codeium/windsurf/skills/` |

If a skill lives in `~/.claude/skills/` but you're using Antigravity, it will be **invisible** to the agent.

## Solution: Symlink Mode (Recommended)

Instead of copying skills into every IDE directory, create one canonical location and symlink others to it. The recommended canonical path is `~/.agents/skills/` (universally supported).

```bash
# Make ~/.agents/skills the master
mkdir -p ~/.agents/skills

# Symlink Antigravity to it
ln -s ~/.agents/skills ~/.gemini/antigravity/skills

# Symlink Claude Code to it
ln -s ~/.agents/skills ~/.claude/skills
```

Or let the skill do it automatically:
```bash
python skill_manager.py check-paths
python skill_manager.py reconcile --global --mode link
```

## Project-Level Skills

For project-scoped skills (in `.agents/skills/` inside a repo), the tool automatically adds the directory to `.gitignore` if they are symlinks sourced from global — to avoid committing symlinks to version control.

## Diagnosing Issues

Run the audit command to see the status of every discovered skill:
```bash
python skill_manager.py audit
```

Statuses:
- `PASS (Global)` — Correctly installed globally, visible everywhere.
- `PASS (Standard)` — In `.agents/skills/`, visible to Antigravity.
- `WARNING (Non-std)` — In a non-standard dir (e.g., `.claude/`), may be invisible.
- `EXTERNAL` — Outside the current project, handled separately.

## Troubleshooting

| Symptom | Likely Cause | Fix |
| :--- | :--- | :--- |
| Skill listed but not activating | Description keywords don't match | Update `description` in `SKILL.md` |
| Skill not listed at all | Wrong directory / no SKILL.md | Run `audit`, then `reconcile` |
| `/skill-manager` not working | Not installed for this IDE | Run `install.sh` |
