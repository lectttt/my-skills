#!/usr/bin/env python3
import os
import shutil
import re
from pathlib import Path
import json
import argparse
from datetime import datetime
import sys
import io

# Configuration
GLOBAL_SKILLS_DIR = Path(r"C:\Users\lectt\.gemini\antigravity\skills")
PLAYGROUND_DIR = Path(r"C:\Users\lectt\.gemini\antigravity\playground")
BRAIN_DIR = Path(r"C:\Users\lectt\.gemini\antigravity\brain")

AGENT_PATHS = [
    Path(".agent/skills"),
    Path(".agents/skills"),
    Path(".agent/workflows"),
    Path(".agents/workflows"),
    Path(".github/skills"),
    Path(".cursor/rules"),
    Path(".windsurf/rules"),
    Path(".clinerules"),
    Path(".roo/rules"),
    Path(".trae/rules"),
]

# Simple translation mapping for faithful Chinese output
TRANSLATIONS = {
    "agent-safety-and-token-guard-skill": {
        "name": "安全与Token防护技能",
        "desc": "AI代理安全协议，处理大文件(>50KB/1000行)及Token管理。"
    },
    "frontend-design": {
        "name": "前端设计专家",
        "desc": "创建高设计感的生产级前端界面，支持流畅动画与深色模式。"
    },
    "skill-manager-skill": {
        "name": "技能管理工具",
        "desc": "统一管理、列表展示及组织跨环境的代理技能。"
    },
    "agent-skill-creator": {
        "name": "代理技能创建器",
        "desc": "将工作流(.md)自动转换为标准化的跨平台代理技能。"
    },
    "installer": {
        "name": "GitHub工具安装指南",
        "desc": "根据README指令自动从GitHub安装及配置工具。"
    },
    "remotion": {
        "name": "Remotion视频最佳实践",
        "desc": "基于React的Remotion视频创作最佳实践与代码模式。"
    }
}

def get_frontmatter(file_path):
    try:
        content = file_path.read_text(encoding="utf-8-sig")
        content = content.replace('\r\n', '\n')
        # Use more flexible regex to find frontmatter
        match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL | re.MULTILINE)
        if match:
            yaml_content = match.group(1)
            metadata = {}
            current_key = None
            for line in yaml_content.splitlines():
                if not line.strip(): continue
                # Handle leading indent as continuation of the previous key
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


def find_skills(scan_all=False):
    skills = []
    
    # 1. Scan Global
    if GLOBAL_SKILLS_DIR.exists():
        for item in GLOBAL_SKILLS_DIR.iterdir():
            if item.is_dir():
                skill_md = item / "SKILL.md"
                if skill_md.exists():
                    meta = get_frontmatter(skill_md)
                    skills.append({
                        "name": meta.get("name", item.name),
                        "description": meta.get("description", "No description"),
                        "version": meta.get("version", "N/A"),
                        "path": str(item),
                        "scope": "Global"
                    })

    # 2. Scan Current Directory
    cwd = Path.cwd()
    for sub in AGENT_PATHS:
        target_dir = cwd / sub
        if target_dir.exists():
            paths_to_check = [target_dir] if target_dir.is_file() else list(target_dir.iterdir())
            for item in paths_to_check:
                skill_md = None
                if item.is_file() and (item.name == "SKILL.md" or item.suffix in [".md", ".mdc", ".rules"]):
                    skill_md = item
                elif item.is_dir() and (item / "SKILL.md").exists():
                    skill_md = item / "SKILL.md"
                
                if skill_md:
                    meta = get_frontmatter(skill_md)
                    skills.append({
                        "name": meta.get("name", item.name),
                        "description": meta.get("description", "No description"),
                        "version": meta.get("version", "1.0.0"),
                        "path": str(item),
                        "scope": "Project (Current)"
                    })

    # 3. Scan Playgrounds (Conditional for speed optimization)
    if scan_all and PLAYGROUND_DIR.exists():
        for pg in PLAYGROUND_DIR.iterdir():
            if pg.is_dir() and pg != cwd:
                for sub in AGENT_PATHS:
                    target_dir = pg / sub
                    if target_dir.exists():
                        # Some skills are folders, some are single files
                        paths_to_check = [target_dir] if target_dir.is_file() else list(target_dir.iterdir())
                        for item in paths_to_check:
                            skill_md = None
                            if item.is_file() and (item.name == "SKILL.md" or item.suffix in [".md", ".mdc", ".rules"]):
                                skill_md = item
                            elif item.is_dir() and (item / "SKILL.md").exists():
                                skill_md = item / "SKILL.md"
                            
                            if skill_md:
                                meta = get_frontmatter(skill_md)
                                if not any(s['path'] == str(item) for s in skills):
                                    skills.append({
                                        "name": meta.get("name", item.name),
                                        "description": meta.get("description", "No description"),
                                        "version": meta.get("version", "1.0.0"),
                                        "path": str(item),
                                        "scope": f"Project ({pg.name})"
                                    })
    return skills

def clean_str(s):
    if not s: return ""
    return re.sub(r'\s+', ' ', s.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')).strip()

def translate_text(text):
    # Very simple word-for-word translation for common terms if not in map
    translations = {
        "Global": "全局",
        "Project": "项目",
        "Current": "当前",
        "No description": "无描述",
        "Safety protocols": "安全协议",
        "Create distinctive": "创建独特的",
        "frontend interfaces": "前端界面",
        "Best practices": "最佳实践",
        "extracting": "提取",
        "logic": "逻辑",
        "workflows": "工作流"
    }
    for en, cn in translations.items():
        text = text.replace(en, cn)
    return text

def list_skills(chinese=True, scan_all=False, as_json=False, output_file=None):
    skills = find_skills(scan_all=scan_all)
    
    if as_json:
        output_content = json.dumps(skills, ensure_ascii=False, indent=2)
    else:
        lines = []
        if not skills:
            lines.append("未发现任何技能。" if chinese else "No skills found.")
        else:
            # Table Header
            if chinese:
                lines.append("| 技能名称 | 范围 | 描述 |")
                lines.append("| :--- | :--- | :--- |")
            else:
                lines.append("| Skill Name | Scope | Description |")
                lines.append("| :--- | :--- | :--- |")

            for s in skills:
                name = clean_str(s['name'])
                desc = clean_str(s['description'])
                scope = clean_str(s['scope'])
                
                if chinese:
                    # First try the TRANSLATIONS map
                    base_name = name.split(".")[0] if "." in name else name
                    match_key = base_name.replace("-best-practices", "").replace("-skill", "")
                    
                    if match_key in TRANSLATIONS:
                        name = TRANSLATIONS[match_key]['name']
                        desc = TRANSLATIONS[match_key]['desc']
                    elif base_name in TRANSLATIONS:
                        name = TRANSLATIONS[base_name]['name']
                        desc = TRANSLATIONS[base_name]['desc']
                    else:
                        name = translate_text(name)
                        desc = translate_text(desc)
                    
                    scope = scope.replace("Global", "全局").replace("Project", "项目").replace("Current", "当前")
                
                # Output as table row
                name_clean = name.replace("|", "\\|")
                desc_clean = desc.replace("|", "\\|")
                lines.append(f"| {name_clean} | {scope} | {desc_clean} |")
        output_content = "\n".join(lines)

    if output_file:
        try:
            # Ensure parent directories exist
            out_path = Path(output_file)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Smart Update Check
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
                print(f"Success: Output [UPDATED] and saved to {output_file} (Total: {len(skills)} skills)")
            else:
                print(f"Success: Output [UNCHANGED]. Local cache is up-to-date at {output_file} (Total: {len(skills)} skills)")
        except Exception as e:
            print(f"Error handling output file: {e}")
            print(output_content)
    else:
        print(output_content)


def refine_title(title):
    # Rule-based refinement and translation to Chinese
    title = title.replace("Walkthrough", "").replace("Project", "").replace("-", "").strip()
    
    mapping = {
        "Skill Manager & Knowledge Harvester": "技能管理与知识收割",
        "Anima Model Download and Config": "Anima模型下载与配置",
        "Forge Neo Installation Fixes": "Forge Neo安装修复",
        "ControlNet & Extension Conflict Resolution": "ControlNet与插件冲突解决",
        "AI Toolkit UI Layout Refinement": "AI工具箱UI布局优化",
        "TensorHub Metadata Linking": "TensorHub元数据链接",
        "WD14 Tagger Fixes": "WD14 Tagger插件修复",
        "Config Persistence & Extension Cleanup": "配置持久化与清理",
        "Skill Creator Skill Installation": "技能创建器安装",
        "Neo Forge Installation & Troubleshooting": "Neo Forge安装与排错",
        "AI Toolbox Pro": "AI工具箱专业版",
        "Drawing Web UI": "绘图Web UI界面",
        "Dharma & Sett Onsen Illustration": "温顺插画设计",
        "Fushiguro Megumi x Sima Yi Cross-over": "伏黑惠x司马懿跨界设计",
        "Pro Splash Art Workflow Playbook": "专业插画工作流指南",
        "Remotion Animation from Image": "Remotion图片动画生成",
        "Untitled Summary": "未命名总结"
    }
    
    for en, cn in mapping.items():
        if en.lower() in title.lower():
            return cn
            
    # Fallback: Simple keyword replacement
    replacements = {
        "Fixes": "修复", "Installation": "安装", "Refinement": "优化",
        "Layout": "布局", "Workflow": "工作流", "Drawing": "绘图"
    }
    for en, cn in replacements.items():
        title = title.replace(en, cn)
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
                        lines = content.splitlines()
                        for line in lines:
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
    pg_path = PLAYGROUND_DIR / project_name
    if not pg_path.exists():
        print(f"Error: Project {project_name} not found.")
        return

    # Check for core knowledge markers
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
            print(f"[FOUND] {m.name} - Analyzed for reusable logic.")
            
    if not found_any:
        print("No specific knowledge markers found in project root.")
    else:
        print("\nSuggested Skill Extraction:")
        target_name = f"{project_name}-knowledge-skill"
        print(f">> Use '/agent-skill-creator' on these files to package into '{target_name}'")

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
            print(f"Successfully globalized folder: {src.name}")
        else:
            shutil.copy2(src, dest)
            print(f"Successfully globalized file: {src.name}")
    except Exception as e:
        print(f"Failed to globalize: {e}")

def main():
    parser = argparse.ArgumentParser(description="Skill Manager CLI")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="List all skills")
    list_parser.add_argument("--english", "-en", action="store_true", help="Output in English")
    list_parser.add_argument("--all", "-a", action="store_true", help="Scan all playgrounds (slow)")
    list_parser.add_argument("--json", "-j", action="store_true", help="JSON output for Agents")
    list_parser.add_argument("--output", "-o", help="Output to file path")
    
    subparsers.add_parser("summaries", help="List all workspace summaries (walkthroughs)")
    
    glob_parser = subparsers.add_parser("globalize", help="Move target skill to global scope")
    glob_parser.add_argument("path", help="Absolute path to the skill directory or file")
    
    harv_parser = subparsers.add_parser("harvest", help="Extract logic from specific project")
    harv_parser.add_argument("project", help="Name of the playground (e.g., void-granule)")

    args = parser.parse_args()

    # Enforce UTF-8 for output globally on Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if args.command == "list":
        list_skills(chinese=not args.english, scan_all=args.all, as_json=args.json, output_file=args.output)
    elif args.command == "summaries":
        list_summaries()
    elif args.command == "globalize":
        globalize(args.path)
    elif args.command == "harvest":
        harvest_knowledge(args.project)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
