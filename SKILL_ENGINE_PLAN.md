# 外贸 AI 技能引擎集成规划

> 目标：把 Claude Code Skills 的外贸能力翻译成项目后端可调用的服务

---

## 核心洞察

Skills 本质上是 **结构化提示词模板 + 工作流定义**。不需要"安装"它们到后端，而是：

1. 从 Skill 的 `SKILL.md` 中提取核心提示词逻辑
2. 封装成后端的 `ForeignTradeSkillService`
3. 通过现有 `AIEngine` 调用 LLM 执行
4. 暴露为 API，前端直接调用

---

## 架构设计

```
前端 (workspace/*)
    │
    ▼
API 路由 (foreign_trade_skills.py)
    │
    ▼
ForeignTradeSkillService
    ├── ProspectSkill        ← prospecting SKILL.md 核心逻辑
    ├── ColdEmailSkill       ← cold-email SKILL.md 核心逻辑
    ├── CustomerResearchSkill ← customer-research SKILL.md 核心逻辑
    ├── CompetitorProfileSkill ← competitor-profiling SKILL.md 核心逻辑
    ├── SalesEnablementSkill  ← sales-enablement SKILL.md 核心逻辑
    ├── SeoAuditSkill         ← seo-audit SKILL.md 核心逻辑
    └── CopywritingSkill      ← copywriting SKILL.md 核心逻辑
    │
    ▼
AIEngine (多 LLM 路由)
    ├── DeepSeek (成本优化)
    ├── Claude (高质量)
    └── OpenAI (通用)
```

---

## 文件清单

### 后端新增
| 文件 | 说明 |
|------|------|
| `backend/app/services/foreign_trade/__init__.py` | 技能引擎入口 |
| `backend/app/services/foreign_trade/skill_registry.py` | 技能注册表（动态发现+调用） |
| `backend/app/services/foreign_trade/prospect_skill.py` | 搜客技能 |
| `backend/app/services/foreign_trade/cold_email_skill.py` | 开发信技能 |
| `backend/app/services/foreign_trade/customer_research_skill.py` | 客户调研技能 |
| `backend/app/services/foreign_trade/competitor_profile_skill.py` | 竞品画像技能 |
| `backend/app/services/foreign_trade/sales_enablement_skill.py` | 销售赋能技能 |
| `backend/app/services/foreign_trade/seo_audit_skill.py` | SEO 审计技能 |
| `backend/app/services/foreign_trade/copywriting_skill.py` | 营销文案技能 |
| `backend/app/api/v1/routes/foreign_trade_skills.py` | API 路由 |

### 前端新增
| 文件 | 说明 |
|------|------|
| `frontend/admin/src/views/workspace/SkillConsole.vue` | 技能控制台（选择技能→输入参数→执行→查看结果） |
| `frontend/admin/src/components/workspace/SkillCard.vue` | 技能卡片组件 |

---

## 技能清单（7 个核心技能）

| # | 技能 | 对应 Skill | 核心能力 | 前端入口 |
|---|------|-----------|----------|----------|
| 1 | **智能搜客** | prospecting | ICP 定义→候选列表→评分→导出 | `/workspace/prospecting` (已建) |
| 2 | **开发信生成** | cold-email | 个性化主题→正文→A/B→序列 | `/workspace/outreach` (已建) |
| 3 | **客户调研** | customer-research | 客户画像→痛点提取→语言分析 | `/workspace/skills/research` |
| 4 | **竞品画像** | competitor-profiling | URL→爬取→结构化画像→打法卡 | `/workspace/skills/competitor` |
| 5 | **销售赋能** | sales-enablement | 报价话术→异议处理→案例素材 | `/workspace/skills/enablement` |
| 6 | **SEO 审计** | seo-audit | 页面审计→技术问题→优化建议 | `/workspace/skills/seo` |
| 7 | **营销文案** | copywriting | 产品描述→广告文案→社媒内容 | `/workspace/skills/copy` |

---

## 核心实现模式

每个技能都是一个 Python 类，核心方法 `execute(params) -> SkillResult`：

```python
class ProspectSkill:
    """搜客技能 — 对应 prospecting SKILL.md"""

    SKILL_PROMPT = """你是一位资深 B2B 获客专家。
    
根据以下 ICP（理想客户画像）搜索潜在客户：

{icp_description}

要求：
1. 优先使用公开数据源（Google、LinkedIn、行业目录）
2. 每个候选客户必须有：公司名、国家、行业、官网、联系人、邮箱
3. 按匹配度评分（0-100），筛选出 {top_n} 个高价值线索
4. 提供证据链（来源 URL、匹配依据）

输出 JSON 格式：
[{{"company": "...", "country": "...", "industry": "...", "website": "...", "contact": "...", "email": "...", "score": 85, "evidence": ["..."]}}]
"""

    def __init__(self, ai_engine: AIEngine):
        self.ai_engine = ai_engine

    async def execute(self, params: dict) -> SkillResult:
        """执行搜客技能"""
        prompt = self.SKILL_PROMPT.format(**params)
        llm = self.ai_engine.llms.get("cost_optimized")
        result = await llm.ainvoke(prompt)
        leads = json.loads(result.content)
        return SkillResult(success=True, data=leads)
```

---

## 执行顺序

```
第一批（基础框架）：
  1. skill_registry.py — 技能注册表
  2. foreign_trade_skills.py — API 路由
  3. prospect_skill.py — 搜客技能（复用已有 workspace 路由）
  4. cold_email_skill.py — 开发信技能（复用已有 OutreachEditor）

第二批（扩展技能）：
  5. customer_research_skill.py
  6. competitor_profile_skill.py
  7. sales_enablement_skill.py

第三批（高级技能）：
  8. seo_audit_skill.py
  9. copywriting_skill.py
  10. SkillConsole.vue — 统一技能控制台
```

---

## 与现有模块的关系

| 现有模块 | 与新技能的关系 |
|----------|---------------|
| `workspace.py` 路由 | 搜客/开发信直接复用，技能引擎是**增强层** |
| `AIEngine` | 技能通过 AIEngine 调用 LLM |
| `ProspectLead` 模型 | 搜客技能的结果存入此模型 |
| `prospect_scorer.py` | 搜客技能调用此服务评分 |
| `hermes/` 调度器 | 技能可通过 hermes 定时执行 |
| `SkillConsole.vue` | 新增统一入口，聚合所有技能 |

---

## 验证标准

- [ ] `POST /api/v1/skills/prospect` 能返回搜客结果
- [ ] `POST /api/v1/skills/cold-email` 能生成开发信
- [ ] `POST /api/v1/skills/competitor` 能生成竞品画像
- [ ] `GET /api/v1/skills` 能列出所有已注册技能
- [ ] SkillConsole.vue 能选择技能、输入参数、执行、查看结果