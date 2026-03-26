---
name: skill-manager-skill
description: >-
  Manage, list, audit, reconcile, and secure agent skills across all
  Antigravity, Claude, Cursor, and universal agent environments.
  Triggers on: /skill-manager, list skills, manage skills, audit skills,
  organize skills, globalize skill, reconcile paths, change skill scope,
  verify skills, security scan skills.
metadata:
  author: Antigravity
  version: 2.1.0
  created: 2026-03-25
  last_reviewed: 2026-03-26
  review_interval_days: 90
---
# /skill-manager — Skill & Agent Organizer

You are a systems administrator for agent skills. Your job is to ensure that skills are discoverable, well-organized, and available in the correct scopes (Global vs Project).

## Trigger

User invokes `/skill-manager` or asks related questions:
- "List all available skills"
- "Show my skills"
- "Summarize all workspace work"
- "Globalize the X skill"
- "Verify skills for security issues"
- "Change the scope of X to project-only"

## Commands

The skill uses `scripts/skill_manager.py`. See `references/commands-reference.md` for full CLI docs.

### 1. 列出全量技能 (List All Skills)
```bash
# 默认仅在控制台展示（避免触发全局目录授权）。若需持久化至全局 registry.md，请加 --save
python ~/.gemini/antigravity/skills/skill-manager-skill/scripts/skill_manager.py list --all

# 强制保存/更新全局注册表
python ~/.gemini/antigravity/skills/skill-manager-skill/scripts/skill_manager.py list --all --save
```

### 2. 查看工作总结 (Workspace Summaries)
```bash
python ~/.gemini/antigravity/skills/skill-manager-skill/scripts/skill_manager.py summaries
```

### 3. IDE 路径对齐检查 (Check Path Alignment)
```bash
python ~/.gemini/antigravity/skills/skill-manager-skill/scripts/skill_manager.py check-paths
```

### 4. 技能纠察 (Audit Skills)
```bash
python ~/.gemini/antigravity/skills/skill-manager-skill/scripts/skill_manager.py audit
```

### 5. 技能迁移与对齐 (Reconcile Skills)
```bash
python ~/.gemini/antigravity/skills/skill-manager-skill/scripts/skill_manager.py reconcile --mode link
```

### 6. 安全扫描 (Verify / Security Scan) ← NEW
```bash
# Scan all discovered skills
python ~/.gemini/antigravity/skills/skill-manager-skill/scripts/skill_manager.py verify

# Scan a specific skill
python ~/.gemini/antigravity/skills/skill-manager-skill/scripts/skill_manager.py verify ~/.gemini/antigravity/skills/my-skill
```

## Methodology & Agent Best Practices

1. **全面性 (Full-Scan)**: 始终使用 `--all` 标志。脚本动态发现所有 Playground，无须硬编码路径。
2. **分级持久化 (Persistence Strategy)**: 
   - **全局扫描 (`--all`)**: 默认仅输出至控制台。使用 `--save` 可显式更新全局 `registry.md`。
   - **项目扫描**: 自动识别本地 `.agents/skills` 目录并更新项目级 `registry.md`，无需手动干预。
3. **可观测性 (Observability)**: 加 `--verbose` 查看每个目录的扫描详情；加 `--log-json` 获取结构化 JSON（适合 Agent 管道）。
4. **显示规范 (Display Protocol)**:
   > [!IMPORTANT]
   > - **执行 `list` 指令时**: 最终输出格式必须参考 [display-standards.md]当前skill references下的规范，进行美化分类展示, 无需询问是否可读。
   > - **最终输出必须是整洁的 Markdown 表格，严禁将表格整体置于代码块内。**
   > - **语言统一性**: 输出语言应与用户对话语言保持一致。

## References
- `references/commands-reference.md` — Full CLI documentation
- `references/display-standards.md` — Mandatory output formatting standards
- `references/environment-alignment.md` — Troubleshooting cross-IDE path issues

## Installation

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/lectttt/my-skills.git
cd my-skills && git sparse-checkout set skills/skill-manager-skill
python3 skills/skill-manager-skill/scripts/skill_manager.py install
```
