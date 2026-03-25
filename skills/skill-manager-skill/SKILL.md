---
name: skill-manager-skill
description: >-
  Manage, list, and organize agent skills across all Antigravity environments.
  Use this skill to quickly find available skills, move skills to the global
  directory, or adjust their operational scope.
  Triggers on: /skill-manager, list skills, manage skills, organize skills,
  globalize skill, change skill scope.
metadata:
  author: Antigravity
  version: 1.1.0
---
# /skill-manager — Skill & Agent Organizer

You are a systems administrator for agent skills. Your job is to ensure that skills are discoverable, well-organized, and available in the correct scopes (Global vs Project).

## Trigger

User invokes `/skill-manager` or asks related questions:
- "List all available skills"
- "Show my skills"
- "Summarize all workspace work"
- "Globalize the skill_creator skill"
- "Harvest knowledge from void-granule"
- "Change the scope of frontend-design to project-only"

## Commands

The skill uses `scripts/skill_manager.py` to perform actions.

### 1. 列出全量技能 (List All Skills)
默认并行扫描全局与所有 Playground（目前约 30+ 目录）。脚本自带“智能更新”机制：若条数与内容未变，则不覆盖现有文件。
```bash
# 执行扫描并更新持久化缓存 (自动进行条数与内容校验)
python scripts/skill_manager.py list --all --output "skills_list.md"
```

### 2. 查看工作总结 (List Summaries)
扫描所有 Workspace 的 `walkthrough.md` 笔记。
```bash
python scripts/skill_manager.py summaries
```

## Methodology & Agent Best Practices

1. **全面性 (Full-Scan)**: 始终使用 `--all` 标志，确保能发现所有非全局的项目级技能。
2. **持久化与增量更新 (Persistence)**: 
   - 优先将结果输出到持久化文件（如 `skills_list.md`）而非临时目录。
   - 脚本执行时会自动检查当前扫描结果与旧文件条数/内容。若输出提示 `[UNCHANGED]`，则直接从现有文件读取即可。
3. **显示规范**: **最终输出格式必须是整洁的 Markdown 表格，严禁将表格整体置于代码块内。**

**Performance Tip**: 扫描 30+ 目录较为耗时。如果脚本提示 `[UNCHANGED]`，说明自上次运行以来没有任何技能增减或描述变更。

