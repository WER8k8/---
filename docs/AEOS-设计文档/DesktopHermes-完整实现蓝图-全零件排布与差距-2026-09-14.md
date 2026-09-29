
> ## 命名口径（法定 · 会话 #74 更名）
> | 层 | 法定名 | 别名（文档中可能出现） | 职责一句话 |
> |----|--------|------------------------|------------|
> | 外层 | **DSH** | DeepSeek Harness / Desktop Hermes / 认知沙箱 / L1 | 意图解构 + 技能包（Skill）热插拔 + 产出任务图意图 |
> | 内层 | **爱马仕** | 对内 Hermes / Hermes 调度核心 / DAG 微内核 / L2 | 智慧调度指挥分派 + 防环 + 数据总线 + 审批 + Saga + 计费 |
> | 插件 | 执行器 / 航道 | DeerFlow 2.0、n8n、TradeAI、GoodJob… | 按图执行，可替换 |
>
> 公式：**外层 DSH（技能包+意图）→ 内层爱马仕（智慧调度指挥分派）→ 任意编排插件（DeerFlow 2.0 + n8n + 24 执行器）= 无限可能场景**

# Desktop Hermes 完整实现蓝图 · 全零件排布 + 差距 + 施工顺序

> **目标法典**：`docs/DesktopHermes动态自由组合装配总案-2026-09-14.md`
> **核对日期**：2026-09-14 · 以 worktree 源码实测为准
> **目标公式**：


> ## 命名口径（法定 · 会话 #74 更名）
> | 层 | 法定名 | 别名（文档中可能出现） | 职责一句话 |
> |----|--------|------------------------|------------|
> | 外层 | **DSH** | DeepSeek Harness / Desktop Hermes / 认知沙箱 / L1 | 意图解构 + 技能包（Skill）热插拔 + 产出任务图意图 |
> | 内层 | **爱马仕** | 对内 Hermes / Hermes 调度核心 / DAG 微内核 / L2 | 智慧调度指挥分派 + 防环 + 数据总线 + 审批 + Saga + 计费 |
> | 插件 | 执行器 / 航道 | DeerFlow 2.0、n8n、TradeAI、GoodJob… | 按图执行，可替换 |
>
> 公式：**外层 DSH（技能包+意图）→ 内层爱马仕（智慧调度指挥分派）→ 任意编排插件（DeerFlow 2.0 + n8n + 24 执行器）= 无限可能场景**
> **外层 DSH（技能包+意图）→ 内层爱马仕 智慧调度指挥分派 → 任意编排插件（DeerFlow 2.0 + n8n + 24 执行器）= 无限可能场景**

---

## 0. 一句话结论

| 维度 | 完成度 | 说明 |
|------|--------|------|
| **零件在位率** | **~85%** | 执行器/Skill/调度内核/n8n/DeerFlow/DB 骨架基本都在 |
| **按设想可运行率** | **~25–35%** | 真正「任意意图→动态图→多插件真跑通」的路径很少 |
| **最大缺口** | **外层动态拆解 + 场景接线 + 数据注水 + 探针门禁** | 不是缺零件，是零件没焊成无限拼装 |

---

## 1. 目标架构（设想）与现状对照

```text
【设想】
用户任意自然语言
  → 外层 DSH：意图解构 + 76 Skill 热插拔 + Persona/SOP 注入
  → 内层爱马仕：动态 TaskGraph + JsonPath + wait_human + Saga + 计费
  → 插件层：24 执行器 / DeerFlow 2.0 / n8n 无限工作流 / Browser
  → 场景：建站 SEO ∥ 拓客 WA ∥ 履约单证 ∥ 任意复合超导网

【现状】
用户意图（from-intent / webhook / admin）
  → 外层：harness_gateway 仅作入口适配 → planner.decompose()
       L1 仅 3 条硬编码模板（site/research/outreach）
       L2 LLM 出图存在但无 Skill 包上下文、难稳定过阀
       L3 降级单节点 deerflow
  → 内层：✅ DAG/JsonPath/Saga/白名单/advance_plan 真实
  → 插件：执行器 24+ 已注册；真/半真/桩混杂
  → n8n：注册表 + 2 webhook 在；40+ 平台多为 STUB
  → DeerFlow：本机 Lite + 官方 2.0 sidecar 旁路（可降级）
```

---

# 2. 全库零件排布（按 Desktop Hermes 三层 + 支撑面）

## 2.1 外层 · DSH Hermes 意图与技能包（L1）

| 零件 | 物理位置 | 设想中的作用 | 现状 |
|------|----------|--------------|------|
| DeepSeek Harness 运行时 | `deepseek-harness/`（工作区） | 外层认知沙箱/规划 | 🟡 子系统在，未成为日常主入口 |
| Harness 客户端 | `backend/app/services/deepseek_harness/{client,config}.py` | SDK 懒加载调 dsh | 🟡 可用性探测 + run_turn |
| Harness 网关 | `backend/app/services/hermes/harness_gateway.py` | 最外层意图入口 | 🟢 **已改真**：交 `planner.decompose`，不再写死桩 |
| Harness API | `backend/app/api/v1/routes/deepseek_harness.py` | health / invoke | 🟡 有路由 |
| 爱马仕 MCP 暴露 | `hermes/hermes_mcp_server.py` + `api/v1/routes/mcp_sse.py` | 外层 DSH 当 MCP Client 调内层出图 | 🟡 代码在，联调未当主路径 |
| ACP 桌面协议 | `tools/youding_acp.py`（工作区 tools） | Desktop Hermes 本地交互 | 🟡 工具在，未产品化 |
| 意图结构 | `schemas/hermes_orchestration.py` IntentEvent | 标准化意图元组 | 🟢 结构可用 |
| 拆解器 | `services/hermes/planner_service.py` | L1/L2/L3 + 三道安全阀 | 🟡 **L1 仅 3 模板**；L2 有但弱 |
| 意图→任务 API | `api/v1/routes/orchestration.py` `POST .../from-intent` | 一句 NL→图→派发 | 🟢 链路接口存在 |
| 技能包加载 | `services/registry/skill_pack_loader.py` | 76 SKILL.md → 索引/匹配 | 🟢 解析器在，文内自述曾长期不入库 |
| 技能入库/匹配 | `services/registry/skill_service.py` seed/match | 意图召回 Skill | 🟡 seed 有；**未进 planner L2 Prompt** |
| 业务 Skill 磁盘 | `<worktree>/skills/` **76** | 热插拔插件池 | 🟢 文件在 |
| ECC 工程技能 | `_external/ecc/skills` ~286 | SOP/工程规约 | 🟡 默认扫描源可不含 ecc |
| AgencyZH 专家 | `_external/agency-agents-zh/` ~309 | persona_ref 角色 | 🟡 资产在，图节点少用 |
| ECC SOP | `_external/ecc/` 898 | sop_ref 约束 | 🟡 同上 |
| 经验注入 | `planner._enrich_with_experience` + `evolution/experience_store` | 反哺拆解 | 🟡 best-effort 已接 |
| 经验引擎 | `hermes/experience_engine.py` | 外层+内层自进化 | 🟡 模块在 |
| 桌面工作台 UI | 前端 admin 部分/未独立 | Intent 输入 + 审批队列 + 图可视化 | 🔴 **无完整 DSH Hermes 桌面客户端** |

**外层零件结论**：原料全，**动态选拔与「任意意图」未闭环**。

---

## 2.2 内层 · 爱马仕 调度微内核（L2）

| 零件 | 物理位置 | 设想作用 | 现状 |
|------|----------|----------|------|
| DAG 拓扑校验 | `task_control_supervisor._validate_dag_topology` | 防环/节点上限 | 🟢 真 |
| 图→任务落库 | `parse_graph_to_tasks` | plan 落 ai_tasks | 🟢 有（历史上曾缺调用方，from-intent 已串） |
| 状态推进 | `advance_plan` | 依赖判定 + JsonPath + 派发 | 🟢 真 |
| Saga 补偿 | `compensate_plan` | 失败逆向 | 🟡 有机制，覆盖外部副作用需加强 |
| 三道安全阀 | `planner.validate_graph` | 执行器/能力/拓扑 | 🟢 |
| 执行器注册表 | `executors/base.py` ExecutorRegistry | 插座字典 | 🟢 |
| 执行器物理包 | `executors/*` **24 业务 + base** | 执行终点 | 🟢 全量 import 注册 |
| 任务桥/路由器 | `services/tasks/hermes_task_bridge.py` | task_type→执行函数；`hermes_node:<executor>` | 🟢 插件路由真 |
| 统一编排 API | `orchestration.py` + ingest webhook | 唯一入口面 | 🟢 设计对 |
| 审批闸 wait_human | hermes 多文件含 wait_human | 真发/真扣前挂起 | 🟡 代码有，桌面端体验弱 |
| 图策略 | GraphPolicies max_parallel/budget | 并发与预算 | 🟡 schema 有，执行侧强化中 |
| MCP Server | `hermes_mcp_server.py` | 给外层出图/派发工具 | 🟡 |
| 持续迭代闭环 | `hermes_continuous_iteration_service.py` | L1采集→…→PM Inbox | 🟡 有，禁自动改代码 |
| Paperclip 审批/目标 | `models/paperclip.py` + hermes paperclip | 公司/Agent/Goal/心跳 | 🟡 模型与服务在，业务注水少 |
| 编排自检 | `backend/scripts/orchestration_selfcheck.py` | 19 项门禁 | 🟢 工具在（**须实跑全绿**） |

**内层零件结论**：**最接近设想的一层**，是全系统最硬资产。

---

## 2.3 插件层 · 24 执行器排布

物理：`backend/app/services/hermes/executors/`

| 执行器 | 能力（总案） | 零件依赖 | 完整度粗评 |
|--------|--------------|----------|------------|
| deerflow | research.deep_run, seo.optimize | services/deerflow + ubrain sidecar + _external/deer-flow | 🟢 核心真，2.0 旁路可选 |
| trade_ai_agent | prospect.scrape, outreach.whatsapp, inbox.classify | adapters/tradeai + _external/trade-ai-agent | 🟡 桥接在，运行时依赖服务/配置 |
| goodjob_crm | document.generate_pi/…, crm.sync_stage | services/goodjob + _external/goodjob-crm | 🟡 同上 |
| site_builder | site.generate, site.build | services/site_builder + ai_site | 🟡 |
| content | content.create | content 服务 + ai_engine | 🟡 |
| publish | publish.multi/single | publish_workers + platform_catalog | 🟡 8 LIVE / 42 STUB |
| nurture | nurture.create/advance | 养号轨迹 | 🟡 空表风险 |
| egress | egress.assign/provision | egress/IP 槽位 | 🟡 |
| inquiry | inquiry.capture | models.inquiry + CRM | 🟡 |
| product | order/product 相关 | product services | 🟡 |
| order | order.create/fulfill | orders + trade 字段 | 🟡 |
| logistics | logistics.track | 物流服务 | 🟡 真实化仍待 |
| billing | billing.meter | 三轨计费/token_ledger | 🟡 |
| accio | outreach.letter, prospect.enrich | ubrain accio | 🟡 |
| lead | lead.search/score | lead 服务 | 🟡 |
| seo | seo.rank | seo 服务/矩阵 | 🟡 |
| media | media.render | media factory | 🟡 未配引擎须诚实降级 |
| browser | browser.scrape | browser_runtime | 🟡 |
| ubrain | ubrain.chat | ubrain + 向量 | 🟡 |
| wangcai | wangcai.ask | services/wangcai | 🟡 |
| forum | forum.post | 论坛互动 | 🟡 |
| engagement | engagement.send | 私域发送 | 🟡 高危需 wait_human |
| ai_engine | ai.chat, ai.reason | ai_engine / ModelGateway | 🟡 |
| research | research.brief | deerflow/research 轻量 | 🟡 |

**插件结论**：**插座全在**；货真假取决于各服务/外部进程/空表，不是注册表问题。

---

## 2.4 可变编排路线（航道 / 无限场景）

| 航道 | 设想链路 | 模板/驱动 | 现状 |
|------|----------|-----------|------|
| A DeerFlow 深研+SEO | 产品→研报→EEAT→SSR→推送 | research 模板 + deerflow | 🟡 L1 有 research |
| B TradeAI 拓客 | 关键词→抓取→评分→WA→分类 | outreach 模板 | 🟡 L1 有 outreach |
| C GoodJob 履约 | 询盘→BOQ→PI→定金→CI→物流 | **当前 planner 无履约模板** | 🔴 会话曾加 `_fulfillment`，**现文件仅 3 模板** |
| D 复合超导 | 跨航道自由拼 | 依赖 L2 LLM + Skill 召回 | 🔴 未达产品级 |
| n8n 自定义场景 | webhook 入/出无限扩展 | workflow_registry | 🟡 注册表真，工作流以桩/2 条激活为主 |

**航道结论**：A/B 有壳；**C 与 D 是「无限可能」的主缺口**。

---

## 2.5 支撑面 · 数据 / 渠道 / 前端 / 基建

| 零件 | 位置 | 现状 |
|------|------|------|
| PostgreSQL 15.8 | @5433 youding_dev | 🟢 ENV-LOCK；~229–234 表 |
| Redis | @6379 | 🟢 |
| n8n | @5678 | 🟡 2 webhook 激活；场景矩阵未铺满 |
| Celery 队列 | celery/deerflow/cross_border/… | 🟡 |
| ai_tasks 统一任务面 | models | 🟢 编排唯一账本 |
| 平台渠道台账 | platform_catalog + publish_workers | 🟡 8 LIVE + 42 STUB |
| Admin 前端 | frontend/admin | 🟡 业务壳全；编排可视化弱 |
| 官网 | worktree Nuxt + 主要备份 Vite | 🟡 双形态未收敛 |
| 技能表 ai_skills | seed_skill_pack | 🟡 需确认已注水 |
| 业务空表 | 207+ 空表（历史口径） | 🔴 真跑断流主因 |
| 探针工具 | **工作区** `tools/{probe,capability_ledger,db_probe,verify_executors,smoke_orchestration}.py` | 🟡 **在工作区根，不在 worktree/tools** |
| 代码地图 | docs/CODE_ATLAS-* | 🟢 本轮已生成 |
| 第二大脑 | Obsidian Vault | 🟡 理念同步，非运行时 |

---

## 2.6 外部子系统（SYSTEM-LOCK-02 必须保留）

| # | 子系统 | 位置 | 编排角色 |
|---|--------|------|----------|
| ① | DeepSeek Harness | deepseek-harness/ + services/deepseek_harness | L1 认知 |
| ② | Hermes 内核 | services/hermes | L2 调度 |
| ③ | Site/Calc/BOQ | site_builder + calculators + goodjob 核价 | 执行插件 |
| ④ | DeerFlow | services/deerflow + _external/deer-flow | 深研内容插件 |
| ⑤ | Trade AI Agent | services/adapters + _external/trade-ai-agent | 拓客插件 |
| ⑥ | GoodJob CRM | services/goodjob + _external/goodjob-crm | 履约单证插件 |
| ⑦ | 350+ 资产 | skills + agency-zh + ecc | 外层上下文库 |
| ⑧ | Browser/n8n | browser_runtime + services/n8n | 出站取证 |

---

# 3. 差距总表（相对 09-14 设想）

| 设想条款 | 目标 | 现状 | 差距 | 优先级 |
|----------|------|------|------|--------|
| 0.3 探针工具箱五件套 | worktree 可一键跑 | 在**工作区 tools/**，worktree 无 | 路径/文档不一致 | P0 |
| 1.1 24 执行器 | 全注册且能力可用 | **注册✅**；业务深度不一 | 接线/凭证/数据 | P0-P1 |
| 1.2 76 Skill 热插拔 | 意图动态选拔进 Prompt | 磁盘+loader✅；**planner 未消费** | 外层断 | **P0** |
| 1.3–1.4 Persona/SOP | TaskNode 注入 | 图节点少用 persona_ref/sop_ref | 外层断 | P1 |
| 1.5 50 渠道 | 按需真发 | 8 LIVE / 42 STUB | 出站矩阵 | P2 |
| 1.6 数据密度 | 业务表有数据 | 大量空表 | 注水工程 | **P0** |
| 2.1 意图解构 JSON | 场景/国家/约束/动作 | IntentEvent 有；NL 解析弱 | L2+Skill | **P0** |
| 2.2 动态 TaskGraph | 运行时任意拼 | **L1 仅 3 模板** + 弱 L2 | 最大缺口 | **P0** |
| 2.3 航道 A–D | 四航道可演示 | A/B 有壳，C/D 弱 | 模板+真桥 | P0-P1 |
| 4 硬锁 | 五锁不破 | 设计层守住 | 回归门禁 | 持续 |
| DSH Hermes 桌面外壳 | 交互+审批+图 UI | ACP 工具级 | 产品化 | P2 |
| DeerFlow 2.0 | 官方能力 | sidecar 旁路+Lite 回退 | 部署与降级标注 | P1 |
| n8n 无限场景 | 工作流市场级 | 注册表+少量 webhook | 场景资产化 | P1 |
| 统一编排权 | 只经 Hermes | 基本如此；历史旁路需收口 | 治理 | P1 |

---

# 4. 完整实现施工顺序（从现在到「无限可能」）

## 阶段 0 · 对齐真相（0.5–1 天）

1. 把探针路径写死进 AGENTS/development：统一用 **工作区** `tools/*` + worktree `backend/scripts/orchestration_selfcheck.py`。  
2. 实跑并记录基线：  
   - `tools/probe.py`  
   - `tools/verify_executors.py`  
   - `tools/smoke_orchestration.py`  
   - `tools/capability_ledger.py`  
   - `tools/db_probe.py --density`  
   - `orchestration_selfcheck.py`（目标 19/19）  
3. 产出「基线 JSON」进 docs，后续每阶段对比。  
4. **Reality Gate 口径**：未过基线前，对外只说「模板航道可用」，不说全域无限编排。

## 阶段 1 · 外层「智能拆解」补齐（P0，1–2 周）——最大缺口

**目标**：任意 NL → 结构化 Intent → Skill 召回 → 合法 TaskGraph。

| 步骤 | 改哪里 | 验收 |
|------|--------|------|
| 1.1 IntentParser | `harness_gateway` / planner 前置 | NL→scene/product/country/constraints/actions（Pydantic） |
| 1.2 Skill 召回进 L2 | `planner._llm_decompose` prompt 拼 `match_skill_pack` top-k + SKILL 正文摘要 | 非模板意图带技能上下文出图 |
| 1.3 动态合成器 | 继续 L2，强制 JSON schema + validate_graph | 复合意图 source=L2_llm 且安全阀通过 |
| 1.4 恢复/补全 L1 模板 | **planner_service.py** 补：履约、社媒拓客、计费、物流等与已注册执行器对齐的图 | 模板数 ≥8，覆盖 7 步闭环关键段 |
| 1.5 路由只按 intent | 保持 session #68 结论 | payload 文案不劫持模板 |
| 1.6 from-intent 回归 | orchestration 路由 + 测试 | 每模板 ≥1 单测 + 1 真跑 |

**禁止**：L2 用未注册执行器；假成功；绕过 validate_graph。

## 阶段 2 · 数据注水 + 真桥（P0，与阶段 1 并行）

| 步骤 | 内容 |
|------|------|
| 2.1 | `seed` 业务主数据：HS 编码、BOQ 22 参数、汇率、PI 模板、平台台账、demo 租户 |
| 2.2 | 确认 `seed_skill_pack` 后 `ai_skills` 非空 |
| 2.3 | TradeAI / GoodJob：配置 `TRADEAI_BASE_URL` / `GOODJOB_BASE_URL` 或诚实 failed |
| 2.4 | 询盘→PI→物流链路空表定向注水 |
| 2.5 | `db_probe --density`：业务关键表从「空」升到可跑 |

## 阶段 3 · 内核可靠性（P0–P1）

1. 状态机枚举 + 中断恢复（ai_tasks 重放）。  
2. 副作用台账 `external_ref`（publish/wa/email/payment）。  
3. wait_human：管理端审批队列 API + 简单 UI（不必先做完整 Desktop）。  
4. Saga 覆盖外部副作用对账。  
5. property tests：环、重复完成、补偿、预算耗尽。

## 阶段 4 · 四航道产品化（P1）

| 航道 | 交付 |
|------|------|
| A | 意图「市场调研/上架」→ DeerFlow 真产出 → 内容/SEO 结果可见 |
| B | 意图「找客户/WhatsApp」→ 线索入 CRM；WA 节点 wait_human |
| C | 意图「询盘报价/履约」→ BOQ→PI→（可选）物流 track |
| D | 至少 1 条复合：调研+拓客+报价，记录 source=L2 或专用复合模板 |

每航道：E2E 脚本 + 失败诚实 + Token 账单可见。

## 阶段 5 · DeerFlow 2.0 + n8n 无限场景（P1）

| 项 | 做法 |
|----|------|
| DeerFlow 2.0 | sidecar 部署文档 + health；输出标 `deerflow_version` / `degraded` |
| n8n | 内核只留薄 webhook；**场景=注册表记录+Hermes 节点契约**；从 2 条扩到航道通知/分发/取证 |
| 场景资产 | `docs/scenes/*.md`：意图样例→期望 DAG→用的 Skill→执行器清单 |
| 禁止 | 运营在 n8n 画复杂业务绕过 Hermes |

## 阶段 6 · DSH Hermes 桌面外壳（P2）

1. ACP/管理端：意图输入、图预览、审批、费用预估。  
2. Skill 热插拔：上传/启停 SKILL.md，无需重启。  
3. 与 Obsidian 同步：只沉淀**已验证**场景与经验。

## 阶段 7 · 治理与门禁（持续）

- CI：selfcheck + smoke + unit  
- 新 Service 守门：capability_ledger 命中则禁止平行新建  
- 观测：trace_id、injected_assets、source(L1/L2/L3)、token  
- 口径：Reality Gate 全绿前不宣传「无限可能全自动」

---

# 5. 零件「谁属于谁」速查（施工时贴在工位）

```text
外层 L1
  deepseek-harness/ | services/deepseek_harness | hermes/harness_gateway
  planner.decompose | registry/skill_pack_* | skills/ | _external/{agency-zh,ecc}
  tools/youding_acp.py | evolution/experience_*

内层 L2
  hermes/planner_service | task_control_supervisor | executors/*
  tasks/hermes_task_bridge | orchestration.py | paperclip | experience_engine

插件 L3
  deerflow | trade_ai | goodjob | site/content/publish | n8n | browser
  platform_catalog | publish_workers | egress | model_gateway

数据/基建
  PG@5433 | Redis@6379 | n8n@5678 | ai_tasks | celery | frontend/admin
```

---

# 6. 里程碑定义（什么算「完整实现」）

| 级别 | 名称 | 判定 |
|------|------|------|
| M1 | 零件齐套 | verify_executors 通过；selfcheck 全绿 |
| M2 | 模板航道可用 | ≥3 条 L1 航道 E2E 真跑，无假成功 |
| M3 | 动态拆解可用 | 复合 NL 有概率 L2 过阀；Skill 上下文进入 Prompt |
| M4 | 无限可拼产品级 | 场景库≥N；n8n/DeerFlow 可替换；审批+计费+补偿闭环 |
| M5 | 桌面体验 | 非工程师可输入意图、看图、点批准 |

**当前估计：M1 接近、M2 部分、M3–M5 未到。**

---

# 7. 建议立刻执行的 10 件事（按序）

1. 实跑工作区探针 + selfcheck，固化基线  
2. 确认 PG/Redis/n8n/8001 活体  
3. planner 补齐履约/社媒等 L1 模板（只用已注册执行器）  
4. `_llm_decompose` 注入 match_skill_pack top-k  
5. seed_skill_pack + 业务主数据注水  
6. 跑通 from-intent：建站 / 研报 / 拓客 三条  
7. 打通 GoodJob/TradeAI 真桥或诚实降级  
8. 管理端 wait_human 审批列表  
9. n8n 场景注册与航道通知  
10. 场景库 + Reality Gate 写进 AGENTS/TODO  

---

*本蓝图与 `CODE_ATLAS-*`、`编排链路真伪核验-2026-09-10`、`DesktopHermes…总案` 配套使用。*
