#!/usr/bin/env python3
"""
skill_manager.py — Level 5 Skill Manager
Manages, lists, audits, and secures agent skills across all IDE environments.
"""

import os
import re
import sys
import io
import json
import shutil
import argparse
import platform
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Platform Configuration (Dynamic — no hardcoded project names)
# ---------------------------------------------------------------------------
IS_WINDOWS = platform.system() == "Windows"
HOME = Path.home()

GLOBAL_SKILLS_DIR = HOME / ".gemini" / "antigravity" / "skills"
BRAIN_DIR = HOME / ".gemini" / "antigravity" / "brain"

AGENT_PATHS = [
    Path(".agent/skills"),
    Path(".agents/skills"),
    Path(".claude/skills"),
    Path(".cursor/skills"),
    Path(".qwen/skills"),
    Path(".cursor/rules"),
    Path(".cursorrules"),
    Path(".clinerules"),
    Path("CLAUDE.md"),
]

# Security scan patterns
SECURITY_PATTERNS = [
    (r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*=\s*['\"][^'\"]{8,}['\"]",
     "Hardcoded credential"),
    (r"(?i)sk-[a-zA-Z0-9]{20,}", "OpenAI API key"),
    (r"(?i)ghp_[a-zA-Z0-9]{30,}", "GitHub token"),
    (r"os\.system\s*\(", "Unsafe os.system() call"),
    (r"subprocess\.call\(.*shell\s*=\s*True", "Unsafe shell=True subprocess"),
    (r"eval\s*\(", "Dangerous eval()"),
]

VERBOSE = False


def vprint(*args, **kwargs):
    """Print only when verbose mode is on."""
    if VERBOSE:
        print(*args, **kwargs)


# ---------------------------------------------------------------------------
# Dynamic Playground Discovery
# ---------------------------------------------------------------------------

def discover_playgrounds():
    """
    Dynamically discover all project directories under HOME that contain
    any known agent path. Replaces the old hardcoded 'projectv3' approach.
    """
    candidates = set()
    # Search first-level subdirs of HOME, then one level into common dev dirs
    search_roots = [HOME]
    for common in ["projectv3", "projects", "workspace", "work", "dev"]:
        p = HOME / common
        if p.is_dir():
            search_roots.append(p)

    seen = set()
    for root in search_roots:
        try:
            for child in root.iterdir():
                if child == Path.cwd() or child in seen:
                    continue
                seen.add(child)
                if not child.is_dir() or child.name.startswith("."):
                    continue
                # Check if this directory has any agent skill path
                for ap in AGENT_PATHS:
                    if (child / ap).exists():
                        candidates.add(child)
                        vprint(f"    [Playground] Discovered: {child}")
                        break
        except PermissionError:
            pass

    return list(candidates)


# ---------------------------------------------------------------------------
# YAML Frontmatter Parser
# ---------------------------------------------------------------------------

def get_frontmatter(file_path):
    try:
        content = file_path.read_text(encoding="utf-8-sig")
        content = content.replace('\r\n', '\n')
        match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL | re.MULTILINE)
        if match:
            yaml_content = match.group(1)
            metadata = {}
            current_key = None
            for line in yaml_content.splitlines():
                if not line.strip():
                    continue
                if (line.startswith("  ") or line.startswith("\t")) and current_key:
                    val = line.strip().strip(">").strip("-").strip()
                    if val:
                        metadata[current_key] = (metadata[current_key] + " " + val).replace("  ", " ").strip()
                elif ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    current_key = key
                    val = value.strip().strip(">").strip("-").strip()
                    metadata[key] = val
            return metadata
    except Exception:
        pass
    return {}


# ---------------------------------------------------------------------------
# Core Skill Discovery
# ---------------------------------------------------------------------------

def _extract_from_dir(target_dir, scope):
    """Extract skill entries from a directory, returning a list of records."""
    results = []
    paths_to_check = [target_dir] if target_dir.is_file() else list(target_dir.iterdir())
    for item in paths_to_check:
        skill_md = None
        is_rule = False

        if item.is_file() and (item.suffix in [".mdc", ".rules"] or
                               item.name in [".cursorrules", ".clinerules", ".roorules", "CLAUDE.md"]):
            skill_md = item
            is_rule = True
        elif item.is_file() and item.name == "SKILL.md":
            skill_md = item
        elif item.is_dir() and (item / "SKILL.md").exists():
            skill_md = item / "SKILL.md"
        elif item.is_dir() and "rules" in item.name.lower():
            for rule_file in item.glob("*.md*"):
                meta = get_frontmatter(rule_file)
                results.append({
                    "name": meta.get("name", rule_file.name),
                    "description": meta.get("description", "No description"),
                    "version": "1.0.0",
                    "path": str(rule_file),
                    "scope": scope,
                    "type": "Rule"
                })
            continue

        if skill_md:
            meta = get_frontmatter(skill_md)
            results.append({
                "name": meta.get("name", item.name),
                "description": meta.get("description", "No description"),
                "version": meta.get("version", "1.0.0"),
                "path": str(item),
                "scope": scope,
                "type": "Rule" if is_rule else "Skill"
            })
    return results


def find_skills(scan_all=False):
    skills = []
    seen_paths = set()

    def add(items):
        for s in items:
            if s["path"] not in seen_paths:
                seen_paths.add(s["path"])
                skills.append(s)

    # 1. Global skills
    if GLOBAL_SKILLS_DIR.exists():
        vprint(f"[Scan] Global: {GLOBAL_SKILLS_DIR}")
        for item in GLOBAL_SKILLS_DIR.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                meta = get_frontmatter(item / "SKILL.md")
                entry = {
                    "name": meta.get("name", item.name),
                    "description": meta.get("description", "No description"),
                    "version": meta.get("version", "N/A"),
                    "path": str(item),
                    "scope": "Global",
                    "type": "Skill"
                }
                if entry["path"] not in seen_paths:
                    seen_paths.add(entry["path"])
                    skills.append(entry)

    # 2. Current directory
    cwd = Path.cwd()
    for sub in AGENT_PATHS:
        target_dir = cwd / sub
        if target_dir.exists():
            vprint(f"[Scan] CWD/{sub}")
            add(_extract_from_dir(target_dir, "Project (Current)"))

    # 3. Dynamically discovered playgrounds
    if scan_all:
        vprint("[Scan] Discovering playgrounds dynamically...")
        playgrounds = discover_playgrounds()
        vprint(f"[Scan] Found {len(playgrounds)} playground(s)")
        for pg in playgrounds:
            if pg == cwd:
                continue
            for sub in AGENT_PATHS:
                target_dir = pg / sub
                if target_dir.exists():
                    vprint(f"[Scan] {pg.name}/{sub}")
                    add(_extract_from_dir(target_dir, f"Project ({pg.name})"))

    return skills


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def clean_str(s):
    if not s:
        return ""
    return re.sub(r'\s+', ' ', s.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')).strip()


def desensitize_path(path):
    try:
        return str(path).replace(str(Path.home()), "~")
    except Exception:
        return str(path)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def list_skills(scan_all=False, as_json=False, output_file=None, log_json=False):
    skills = find_skills(scan_all=scan_all)

    if as_json or log_json:
        output_content = json.dumps({
            "total": len(skills),
            "scanned_at": datetime.now().isoformat(),
            "skills": skills
        }, ensure_ascii=False, indent=2)
    else:
        lines = []
        if not skills:
            lines.append("No skills or rules found.")
        else:
            lines.append("| Name | Type | Scope | Description |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for s in skills:
                name = clean_str(s['name']).replace("|", "\\|")
                desc = clean_str(s['description']).replace("|", "\\|")
                scope = clean_str(s['scope'])
                stype = clean_str(s['type'])
                lines.append(f"| {name} | {stype} | {scope} | {desc} |")
        output_content = "\n".join(lines)

        # Auto-reconcile health warning
        non_std_found = False
        for s in skills:
            if s['scope'] != "Global":
                path = Path(s['path'])
                try:
                    rel_path = path.relative_to(Path.cwd())
                    if any(str(rel_path).startswith(p) for p in [".claude", ".cursor", ".qwen"]):
                        non_std_found = True
                        break
                except Exception:
                    pass

        if non_std_found:
            output_content += "\n\n> [!WARNING]\n"
            output_content += "> 检测到技能位于非标准目录（如 `.claude/skills`），Antigravity 可能无法识别。\n"
            output_content += "> 运行: `python3 skill_manager.py reconcile --mode link` 进行路径对齐。\n"

    if output_file:
        try:
            out_path = Path(output_file)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            should_write = True
            if out_path.exists():
                try:
                    old_content = out_path.read_text(encoding="utf-8")
                    if old_content.strip() == output_content.strip():
                        should_write = False
                except Exception:
                    pass
            if should_write:
                out_path.write_text(output_content, encoding="utf-8")
                print(f"[UPDATED] Saved to {output_file} (Total: {len(skills)} skills)")
            else:
                print(f"[UNCHANGED] Cache is up-to-date at {output_file} (Total: {len(skills)} skills)")
        except Exception as e:
            print(f"Error handling output file: {e}")
            print(output_content)
    else:
        print(output_content)


def refine_title(title):
    title = title.replace("Walkthrough", "").replace("Project", "").replace("-", " ").strip()
    return title


def list_summaries():
    summaries = []
    if BRAIN_DIR.exists():
        for session_dir in BRAIN_DIR.iterdir():
            if session_dir.is_dir():
                walkthrough = session_dir / "walkthrough.md"
                if walkthrough.exists():
                    title = "未命名总结"
                    try:
                        content = walkthrough.read_text(encoding="utf-8")
                        for line in content.splitlines():
                            if line.startswith("# "):
                                title = line.strip("# ").strip()
                                break
                    except Exception:
                        pass
                    mtime = datetime.fromtimestamp(walkthrough.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                    summaries.append({
                        "id": session_dir.name[:8],
                        "title": refine_title(title),
                        "date": mtime,
                        "path": str(walkthrough)
                    })
    summaries.sort(key=lambda x: x['date'], reverse=True)
    print(f"{'ID':<10} | {'DATE':<18} | {'TITLE'}")
    print("-" * 80)
    for s in summaries:
        print(f"{s['id']:<10} | {s['date']:<18} | {s['title']}")


def harvest_knowledge(project_name):
    print(f"--- Harvesting Knowledge from Project: {project_name} ---")
    playgrounds = discover_playgrounds()
    pg_path = None
    for pg in playgrounds:
        if pg.name == project_name:
            pg_path = pg
            break
    if not pg_path:
        # Fallback: direct path lookup
        for root in [HOME]:
            candidate = root / project_name
            if candidate.exists():
                pg_path = candidate
                break
    if not pg_path:
        print(f"Error: Project '{project_name}' not found in discovered playgrounds.")
        return

    markers = [
        pg_path / "README.md",
        pg_path / "ARCHITECTURE.md",
        pg_path / ".cursorrules",
        pg_path / ".clinerules",
        pg_path / ".agent/skills",
        pg_path / ".agents/skills",
        pg_path / ".github/skills",
    ]
    found_any = False
    for m in markers:
        if m.exists():
            found_any = True
            print(f"[FOUND] {m.name}")
    if not found_any:
        print("No specific knowledge markers found in project root.")
    else:
        print(f"\nSuggested: Use '/agent-skill-creator' to package into '{project_name}-knowledge-skill'")


def globalize(skill_path):
    src = Path(skill_path)
    if not src.exists():
        print(f"Error: Path {skill_path} does not exist.")
        return
    dest = GLOBAL_SKILLS_DIR / src.name
    if dest.exists():
        print(f"Error: Skill {src.name} already exists in Global directory.")
        return
    try:
        if src.is_dir():
            shutil.copytree(src, dest)
            print(f"Globalized folder: {src.name}")
        else:
            shutil.copy2(src, dest)
            print(f"Globalized file: {src.name}")
    except Exception as e:
        print(f"Failed to globalize: {e}")


# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------

PLATFORM_SKILL_DIRS = {
    "antigravity": HOME / ".gemini" / "antigravity" / "skills",
    "gemini":      HOME / ".gemini" / "skills",
    "claude":      HOME / ".claude" / "skills",
    "universal":   HOME / ".agents" / "skills",
    "cursor":      HOME / ".cursor" / "skills",
    "windsurf":    HOME / ".codeium" / "windsurf" / "skills",
    "cline":       HOME / ".clinerules" / "skills",
    "kiro":        HOME / ".kiro" / "skills",
    "qwen":        HOME / ".qwen" / "skills",
}


def detect_platforms():
    """Return list of platform names whose base directories exist on this machine."""
    detected = []
    # gemini without antigravity
    if (HOME / ".gemini").exists() and not (HOME / ".gemini" / "antigravity").exists():
        detected.append("gemini")
    checks = [
        ("antigravity", HOME / ".gemini" / "antigravity"),
        ("claude",      HOME / ".claude"),
        ("universal",   HOME / ".agents"),
        ("cursor",      HOME / ".cursor"),
        ("windsurf",    HOME / ".codeium" / "windsurf"),
        ("cline",       HOME / ".clinerules"),
        ("kiro",        HOME / ".kiro"),
        ("qwen",        HOME / ".qwen"),
    ]
    for name, path in checks:
        if path.exists():
            detected.append(name)
    return detected


def install_skill(skill_dir, platforms=None, install_all=False, dry_run=False):
    """
    Register skill_dir into each target platform's skills directory via symlink
    (or directory junction on Windows).
    """
    skill_dir = Path(skill_dir).resolve()
    skill_name = skill_dir.name

    if platforms:
        target_platforms = list(platforms)
    elif install_all:
        target_platforms = detect_platforms()
    else:
        detected = detect_platforms()
        target_platforms = detected[:1]  # highest-priority detected platform

    if not target_platforms:
        print("[!] No supported platforms detected. Use --platform to specify one.")
        print("    Available: " + ", ".join(PLATFORM_SKILL_DIRS.keys()))
        return

    for plat in target_platforms:
        dest_dir = PLATFORM_SKILL_DIRS.get(plat)
        if not dest_dir:
            print(f"[!] Unknown platform: {plat}")
            continue
        dest = dest_dir / skill_name
        if dry_run:
            print(f"[DRY-RUN] Would install: {skill_name} → {dest}")
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        if dest.is_symlink():
            dest.unlink()
        elif dest.exists():
            print(f"[SKIP] {dest} already exists as a real directory.")
            continue
        try:
            if IS_WINDOWS:
                import _winapi
                _winapi.CreateJunction(str(skill_dir), str(dest))
            else:
                dest.symlink_to(skill_dir)
            print(f"[✓] {plat}: {dest}")
        except Exception as e:
            print(f"[✗] {plat}: {e}")

    if not dry_run:
        print("\nDone. Restart your Agent and type /skill-manager.")


def check_paths():
    print("--- Skill Path Alignment Check ---")
    home = Path.home()
    targets = {
        "Antigravity": home / ".gemini" / "antigravity" / "skills",
        "Universal (.agents)": home / ".agents" / "skills",
        "Claude Code": home / ".claude" / "skills",
        "Qwen Code": home / ".qwen" / "skills",
        "Cursor (Global)": home / ".cursor" / "skills"
    }
    issues_found = False
    print(f"{'IDE/Agent':<25} | {'Path Existence':<18} | {'Status'}")
    print("-" * 85)
    paths_info = {}
    for name, path in targets.items():
        exists = "Found" if path.exists() else "Not Found"
        is_link = path.is_symlink()
        link_target = os.readlink(path) if is_link else "N/A"
        status = "[LINKED]" if is_link else "[DIR]" if path.exists() else "[MISSING]"
        print(f"{name:<25} | {exists:<18} | {status}")
        paths_info[name] = {"path": path, "status": status, "target": desensitize_path(link_target)}

    print("\n[Alignment Insight]")
    universal_path = targets["Universal (.agents)"]
    if not universal_path.exists():
        print(">> TIP: Create ~/.agents/skills/ as the master skills repository.")
    else:
        for name, info in paths_info.items():
            if name != "Universal (.agents)":
                if info['status'] == "[DIR]":
                    print(f">> WARNING: {name} ({desensitize_path(info['path'])}) is a separate directory. Recommend symlinking to ~/.agents/skills.")
                    issues_found = True
                elif info['status'] == "[MISSING]":
                    print(f">> Suggestion: ln -s ~/.agents/skills {desensitize_path(targets[name])}")
    if not issues_found:
        print("✓ All active environments are aligned via symlinks.")
    else:
        print("\n>> Pro-tip: Run 'python3 skill_manager.py align-platforms' to fix all alignment issues automatically.")


def align_platforms():
    print("--- Aligning Platform Skill Directories to Universal Master ---")
    master = PLATFORM_SKILL_DIRS["universal"]
    if not master.exists():
        master.mkdir(parents=True, exist_ok=True)
        print(f"Created master directory: {master}")

    for name, path in PLATFORM_SKILL_DIRS.items():
        if name == "universal":
            continue

        # Check if platform parent exists (e.g., ~/.claude exists)
        parent = path.parent
        # Small tweak for nested paths like windsurf
        if name == "windsurf":
             parent = path.parent.parent

        if not parent.exists():
            continue

        if path.exists():
            if path.is_symlink():
                try:
                    target = os.readlink(path)
                    if Path(target).expanduser().resolve() == master.resolve():
                        print(f"✓ {name:<12}: Already aligned.")
                        continue
                    else:
                        print(f"[!] {name:<12}: Aligned to different target. Updating...")
                        path.unlink()
                except Exception:
                    print(f"[!] {name:<12}: Broken symlink. Removing...")
                    path.unlink()
            else:
                # It's a real directory. Backup and link.
                backup = path.with_name(f"{path.name}_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}")
                print(f"[!] {name:<12}: Real directory found. Backing up to {backup.name}...")
                path.rename(backup)

        # Create symlink
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if IS_WINDOWS:
                import _winapi
                _winapi.CreateJunction(str(master), str(path))
            else:
                os.symlink(master, path)
            print(f"✓ {name:<12}: Successfully aligned to {desensitize_path(master)}")
        except Exception as e:
            print(f"✗ {name:<12}: Failed to align: {e}")


def update_gitignore(target_paths):
    gitignore = Path(".gitignore")
    content = ""
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
    lines = content.splitlines()
    marker_start = "# [SKILL-MANAGER] MANAGED SKILLS - START"
    marker_end = "# [SKILL-MANAGER] MANAGED SKILLS - END"
    new_lines = []
    in_block = False
    for line in lines:
        if line.strip() == marker_start:
            in_block = True
            continue
        if line.strip() == marker_end:
            in_block = False
            continue
        if not in_block:
            new_lines.append(line)
    if target_paths:
        roots = sorted(set(f"{Path(p.lstrip('/')).parts[0]}/" for p in target_paths if Path(p.lstrip('/')).parts))
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(marker_start)
        for p in roots:
            new_lines.append(p)
        new_lines.append(marker_end)
    gitignore.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"Updated .gitignore with {len(target_paths)} entries.")


def audit_skills():
    print("--- Skill Registry Audit (IDE Recognition Check) ---")
    cwd = Path.cwd()
    all_skills = find_skills(scan_all=False)
    standard = [Path(".agents/skills"), Path(".agent/skills")]
    non_standard = [Path(".claude/skills"), Path(".cursor/skills")]
    print(f"{'Skill Name':<25} | {'Scope':<15} | {'Path Status':<22} | {'Recommendation'}")
    print("-" * 110)
    for s in all_skills:
        path = Path(s['path'])
        scope = s['scope']
        status = "UNKNOWN"
        recommendation = "-"
        if scope == "Global":
            status = "PASS (Global)"
        else:
            try:
                rel_path = path.relative_to(cwd)
                if any(str(rel_path).startswith(str(p)) for p in standard):
                    status = "PASS (Standard)"
                elif any(str(rel_path).startswith(str(p)) for p in non_standard):
                    status = "WARNING (Non-std)"
                    recommendation = "Move/Link to .agents/skills/"
                else:
                    status = "NOTICE (Custom)"
            except ValueError:
                status = "EXTERNAL"
        print(f"{s['name']:<25} | {scope:<15} | {status:<22} | {recommendation}")


def reconcile_skills(source=None, target=None, mode="link", global_sync=False):
    print(f"--- Reconciling Skills (Mode: {mode}) ---")
    cwd = Path.cwd()
    if not target:
        target = cwd / ".agents/skills"
    else:
        target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    sources = []
    if global_sync and GLOBAL_SKILLS_DIR.exists():
        sources.append(GLOBAL_SKILLS_DIR)
    if source:
        sources.append(Path(source))
    elif not global_sync and (cwd / ".claude/skills").exists():
        sources.append(cwd / ".claude/skills")
    if not sources:
        print("No sources identified. Use --source or --global.")
        return
    managed_paths = []
    for src_dir in sources:
        print(f"Processing source: {src_dir}")
        for item in src_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                dest = target / item.name
                already_there = dest.exists()
                if src_dir.absolute() == target.absolute() or already_there:
                    if already_there:
                        rel_to_cwd = dest.absolute().relative_to(cwd.absolute())
                        managed_paths.append(f"/{rel_to_cwd}")
                    continue
                if dest.is_symlink():
                    dest.unlink()
                try:
                    if mode == "link":
                        os.symlink(item.absolute(), dest)
                    elif mode == "copy":
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                    elif mode == "move":
                        shutil.move(str(item), str(dest))
                    print(f"✓ {mode.capitalize()}ed: {item.name}")
                    rel_to_cwd = dest.absolute().relative_to(cwd.absolute())
                    managed_paths.append(f"/{rel_to_cwd}")
                except Exception as e:
                    print(f"Failed {item.name}: {e}")
    if managed_paths:
        update_gitignore(managed_paths)


def verify_skills(target_path=None):
    """
    Security scan: detect hardcoded credentials, unsafe patterns, and
    suspicious code in all discovered skills or a specific path.
    """
    print("--- Skill Security Verification ---")
    if target_path:
        scan_dirs = [Path(target_path)]
    else:
        skills = find_skills(scan_all=False)
        # Deduplicate: resolve symlinks so we don't scan the same skill twice
        seen = set()
        unique = []
        for s in skills:
            resolved = str(Path(s['path']).resolve())
            if resolved not in seen:
                seen.add(resolved)
                unique.append(s)
        scan_dirs = [Path(s['path']) for s in unique]

    issues = []
    scanned = 0
    for skill_dir in scan_dirs:
        if skill_dir.is_file():
            files = [skill_dir]
        elif skill_dir.is_dir():
            files = list(skill_dir.rglob("*.py")) + list(skill_dir.rglob("*.sh")) + list(skill_dir.rglob("*.md"))
        else:
            continue

        for f in files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                scanned += 1
                for pattern, label in SECURITY_PATTERNS:
                    for match in re.finditer(pattern, content):
                        line_no = content[:match.start()].count("\n") + 1
                        issues.append({
                            "file": desensitize_path(f),
                            "line": line_no,
                            "label": label,
                            "snippet": match.group(0)[:60]
                        })
            except Exception:
                pass

    print(f"\nScanned {scanned} file(s) across {len(scan_dirs)} skill(s).\n")
    if not issues:
        print("✓ No security issues found. All clear.")
    else:
        print(f"{'File':<45} | {'Line':>4} | {'Issue':<30} | {'Snippet'}")
        print("-" * 120)
        for i in issues:
            file_str = str(i['file'])[-44:]
            print(f"{file_str:<45} | {i['line']:>4} | {i['label']:<30} | {i['snippet']}")
        print(f"\n[!] Found {len(issues)} issue(s). Review and remediate before sharing.")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    global VERBOSE

    parser = argparse.ArgumentParser(
        description="Skill Manager CLI — Level 5 Agent Skill Organizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="See references/commands-reference.md for full documentation."
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose scan output")

    subparsers = parser.add_subparsers(dest="command")

    # list
    list_parser = subparsers.add_parser("list", help="List all skills and rules")
    list_parser.add_argument("--all", "-a", action="store_true", help="Scan all playgrounds (dynamic discovery)")
    list_parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    list_parser.add_argument("--log-json", action="store_true", help="Structured JSON output for agent pipelines")
    list_parser.add_argument("--output", "-o", help="Output to persistent file path")

    # audit
    subparsers.add_parser("audit", help="Audit skill placement and IDE recognition")

    # reconcile
    recon_parser = subparsers.add_parser("reconcile", help="Sync/migrate skills between directories")
    recon_parser.add_argument("--source", "-s", help="Source directory")
    recon_parser.add_argument("--target", "-t", help="Target directory (default: .agents/skills)")
    recon_parser.add_argument("--mode", "-m", choices=["link", "copy", "move"], default="link")
    recon_parser.add_argument("--global", "-g", action="store_true", dest="global_sync", help="Include global skills")

    # summaries
    subparsers.add_parser("summaries", help="List all workspace walkthrough summaries")

    # check-paths
    subparsers.add_parser("check-paths", help="Check and align skill paths across IDEs")

    # align-platforms
    subparsers.add_parser("align-platforms", help="Automatically align platform skill directories to ~/.agents/skills")

    # globalize
    glob_parser = subparsers.add_parser("globalize", help="Move a skill to global scope")
    glob_parser.add_argument("path", help="Path to the skill directory or file")

    # harvest
    harv_parser = subparsers.add_parser("harvest", help="Extract knowledge from a project")
    harv_parser.add_argument("project", help="Project name (e.g., void-granule)")

    # verify
    verify_parser = subparsers.add_parser("verify", help="Security scan skills for unsafe patterns")
    verify_parser.add_argument("path", nargs="?", help="Specific skill path to scan (default: all discovered)")

    # install
    install_parser = subparsers.add_parser("install", help="Register this skill to local Agent platform(s)")
    install_parser.add_argument("--platform", "-p", nargs="+", metavar="PLATFORM",
                                help="Target platform(s): " + ", ".join(PLATFORM_SKILL_DIRS.keys()))
    install_parser.add_argument("--all", "-a", action="store_true", dest="install_all",
                                help="Install to all detected platforms")
    install_parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")

    # Allow --verbose/-v to appear before OR after the subcommand
    args, _ = parser.parse_known_args()
    if not args.verbose:
        # Second pass to catch flags after subcommand
        for flag in ["-v", "--verbose"]:
            if flag in sys.argv:
                args.verbose = True
                break

    VERBOSE = args.verbose

    # UTF-8 stdout
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if args.command == "list":
        list_skills(scan_all=args.all, as_json=args.json, output_file=args.output, log_json=args.log_json)
    elif args.command == "audit":
        audit_skills()
    elif args.command == "reconcile":
        reconcile_skills(source=args.source, target=args.target, mode=args.mode, global_sync=args.global_sync)
    elif args.command == "summaries":
        list_summaries()
    elif args.command == "check-paths":
        check_paths()
    elif args.command == "align-platforms":
        align_platforms()
    elif args.command == "globalize":
        globalize(args.path)
    elif args.command == "harvest":
        harvest_knowledge(args.project)
    elif args.command == "verify":
        verify_skills(target_path=args.path)
    elif args.command == "install":
        skill_dir = Path(__file__).resolve().parent.parent
        install_skill(skill_dir, platforms=args.platform, install_all=args.install_all, dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
