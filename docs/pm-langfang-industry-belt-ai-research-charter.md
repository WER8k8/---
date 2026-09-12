# 大城 + 河间 · 建筑相关产品名 · 多 AI 调研派工单 · PM-07

> **签发**：项目经理（PM-07）  
> **执行**：GW-MR 市场调研 × 平台 AI 配置  
> **核心问题**：**大城县和河间市这一带，都有哪些跟建筑相关的产品名字？包括主材和附属配套。**

---

## 一、调研要问什么（给老板一句话）

不是先猜某一类涂料，而是：

> **大城、河间这一产业带上，工厂常卖哪些「建筑相关产品名」？**  
> 保温岩棉是其一，还有钢结构防火漆、防腐漆、网格布、阴阳角、保温钉、密封条、砂浆、板材……**主材 + 附属配套都要列名字**。

AI 大模型调研 **只负责把品名清单拉出来**；真假、规格、能不能出口，仍靠实地/B2B 复核。

---

## 二、为什么要 PM 安排多模型一起问

同一问题问 **7 路大模型**（DeepSeek、通义、豆包、ChatGPT、Gemini、Claude、NVIDIA），看谁都说到的品名（高共识），谁单独胡说的（待删）。

---

## 三、与实地调研的关系

| 阶段 | 产出 | 能否入库 |
|------|------|----------|
| **A. 多 AI 品名清单** | `ai_dacheng_hejian_*.json` | ❌ pending |
| **B. 实地/B2B 复核** | 删幻觉、补证据 | ❌ pending |
| **C. PM approved** | merge 脚本 | ✅ |

---

## 四、PM 派工（Wave-0 优先）

### Wave-0 · 区域全量品名（P0，先做这一件）

| 批次 | 范围 | 问法 | 模型 | 目标 |
|------|------|------|------|------|
| **W0** | 大城县 + 河间市 | 见 Prompt 模板「核心调研问题」 | 7 路全跑 | ≥80 个不重复品名，含附属配套 |

**执行命令（默认）：**

```powershell
python scripts/run-industry-belt-ai-research.py --region dacheng_hejian
```

产出：`backend/app/data/industry_belt_survey_samples/ai_dacheng_hejian_YYYYMMDD.json`

### Wave-1 · 单品类加深（P1，W0 之后按需）

某类品名明显不够时再跑，例如：

```powershell
python scripts/run-industry-belt-ai-research.py --category finish_accessories
```

---

## 五、七大模型（与 GEO 引擎同源）

| model_id | 名称 | Key 环境变量 |
|----------|------|--------------|
| deepseek | DeepSeek | AI_DEEPSEEK_API_KEY |
| qwen | 通义千问 | AI_DASHSCOPE_API_KEY |
| doubao | 豆包 | AI_ARK_API_KEY |
| openai | ChatGPT | AI_OPENAI_API_KEY |
| gemini | Gemini | AI_GEMINI_API_KEY |
| anthropic | Claude | AI_ANTHROPIC_API_KEY |
| nvidia | NVIDIA NIM | AI_NVIDIA_API_KEY |

未配 Key → 跳过，不伪造。

---

## 六、验收（PM-07）

| ID | 条件 |
|----|------|
| AI-R0 | W0 交付物覆盖 **主材 + 至少 5 类附属配套**（网格布/护角/钉子/涂料/密封等） |
| AI-R1 | 已接通模型 100% 跑完 |
| AI-R2 | 共识品名 ≥80 |
| AI-R3 | spot-check 10 品名，错误率 ≤20% |
| AI-R4 | 未经 approved 禁止 merge |

---

## 七、分工

| 角色 | 职责 |
|------|------|
| PM-07 | 派 W0、审品名清单、批 approved |
| GW-MR | 跑脚本、写 2 页摘要、实地 spot-check |
| 研发 | 只维护脚本，不写品名 |
| 销售 | 对客户仍强调 **产品库优先** |

---

## 八、相关文件

- Prompt：`docs/templates/industry-belt-ai-research-prompt.md`  
- 脚本：`scripts/run-industry-belt-ai-research.py`  
- 实地宪章：`docs/pm-langfang-industry-belt-research-charter.md`  
- 待办：`backend/app/data/industry_belt_research_backlog.json`

---

*PM-07 · 大城+河间建筑品名调研 · 2026-06-03*
