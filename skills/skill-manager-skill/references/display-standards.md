# Skill Display Standards (Listing Skills V2)

To ensure AI agents present the results of the `list` command clearly and beautifully, follow these mandatory display standards.

## 1. Aesthetic Grouping by Workspace
Skills MUST be grouped by their physical **Workspace Path**. Use clear headers with emojis to distinguish between Global and Project-level environments.

## 2. Mandatory Beautiful Format
When listing skills, use the following structure:

### 🗂️ 全量技能列表 (Total Skill List)

#### 🌐 Global 技能（全局可用）
| 技能名称 | 类型 | 描述 |
| :--- | :--- | :--- |
| **name** | **type** | Concise summary |

#### 📁 Project: [ProjectName] @ [Path]
| 技能名称 | 类型 | 描述 |
| :--- | :--- | :--- |
| **name** | **type** | Concise summary |

### 3. Summary Statistics
At the end of the list, provide a summary line:
**统计**：Global [N] 个 · [Project1] [M] 个 · [Project2] [L] 个，共 [Total] 项。

## Formatting Rules:
- **No Blocks**: DO NOT wrap the entire output in a code block.
- **Emojis**: Use 🌐 for Global, 📁 for Projects, 🗂️ for the main title.
- **Language**: Use the user's conversation language (e.g., Chinese as shown).
- **Redundancy**: If a skill exists in multiple places, list them in their respective workspace sections.
