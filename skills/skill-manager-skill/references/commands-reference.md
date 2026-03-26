# Commands Reference

Full CLI documentation for `skill_manager.py`.

## Global Flags

| Flag | Description |
| :--- | :--- |
| `--verbose` / `-v` | Show per-directory scan summaries and discovered playgrounds |

---

## `list` — Discover and Display All Skills

```bash
python skill_manager.py list [--all] [--json] [--log-json] [--output FILE] [--verbose]
```

| Flag | Description |
| :--- | :--- |
| `--all` / `-a` | Scan all dynamically discovered playground directories |
| `--json` / `-j` | Output as JSON array |
| `--log-json` | Output as structured JSON object with metadata (for agent pipelines) |
| `--output FILE` / `-o` | Save to a persistent file (uses smart diff to avoid unnecessary writes) |

**Examples:**
```bash
# Quick list of current project + global skills
python skill_manager.py list

# Full scan with persistent cache
python skill_manager.py list --all --output skills_list.md

# JSON output for agent consumption
python skill_manager.py list --log-json
```

---

## `audit` — IDE Recognition Health Check

```bash
python skill_manager.py audit
```
Reports every skill's path status: `PASS`, `WARNING`, or `EXTERNAL`.

---

## `reconcile` — Migrate Skills to Standard Paths

```bash
python skill_manager.py reconcile [--source DIR] [--target DIR] [--mode link|copy|move] [--global]
```

| Flag | Description |
| :--- | :--- |
| `--source` / `-s` | Source directory (auto-detects `.claude/skills` if omitted) |
| `--target` / `-t` | Destination directory (default: `.agents/skills`) |
| `--mode` / `-m` | `link` (symlink, recommended), `copy`, or `move` |
| `--global` / `-g` | Include global skills directory as source |

---

## `verify` — Security Scan (NEW)

```bash
python skill_manager.py verify [path]
```
Scans skills for security issues:
- Hardcoded API keys / tokens
- Unsafe `os.system()` calls
- `eval()` usage
- `shell=True` subprocess calls

If no path is given, scans all currently discoverable skills.

---

## `summaries` — List Workspace Walkthroughs

```bash
python skill_manager.py summaries
```
Lists all `walkthrough.md` files across past conversation sessions.

---

## `check-paths` — Cross-IDE Path Alignment

```bash
python skill_manager.py check-paths
```
Shows whether each IDE's skill path is a symlink, directory, or missing, and recommends alignment actions.

---

## `globalize` — Promote a Skill to Global Scope

```bash
python skill_manager.py globalize /path/to/my-skill
```
Copies the skill into `~/.gemini/antigravity/skills/` for global availability.

---

## `harvest` — Extract Knowledge from a Project

```bash
python skill_manager.py harvest <project-name>
```
Scans a project directory for reusable knowledge markers (README, ARCHITECTURE, skill directories) and recommends using `/agent-skill-creator` to package them.
