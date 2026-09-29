# 竞品对标 | Accio Work vs 优丁 8 大子系统
> **日期**：2026-09-13
> **来源**：`.workbuddy/memory/竞品雷达-2026-09-13.md` 本期 24 条信号（Wikipedia 检索快照）
> **口径**：对照 `docs/AEOS_MASTER_CODEBASE_INDEX.md` 八大子系统；三态判定（领先/持平/落后）+ 来源可信度（已确认/待验证/传闻），与 `docs/多模型设计统一裁定书-2026-09-09.md` 判定三级链一致。

## 一、逐条信号 → 8 大子系统映射

| 信号摘要 | 来源可信度 | 对应子系统 | 判定 | 说明 |
|---|---|---|---|---|
| Accio 是构建在 Qwen 上的 AI 原生应用，生成市场洞察、回答 sourcing 问题 | 已确认（Wikipedia，多条目交叉引用） | ④ DeerFlow（研报与内容） | 落后 | 对方明确有"市场洞察生成"能力，我们 DeerFlow 侧目前是"9 意图深研与 EEAT 内容"，缺独立的"市场洞察/sourcing Q&A"对外能力 |
| Accio Work 使用多个分工 AI Agent：市场研究、趋势追踪、找供应商、比价、生成 listing、基础店铺运营 | 已确认 | ⑤ Trade AI Agent（全域社媒拓客与 WhatsApp 中枢） | 落后 | 我们 Trade AI Agent 侧重"社媒拓客+WhatsApp"，缺少"比价/供应商比较"这条采购侧能力链 |
| Accio Work 2026-03 发布，目标"全流程自动化电商与采购任务"，面向中小企业 | 已确认 | ② Hermes（受控调度） | 持平 | 我们的 Hermes 是 L2 状态机受控调度（内部执行器视角），对方是"全流程自动化"（用户任务视角），定位不同不算落后，但需留意对方是否延伸到任务编排层 |
| "Accio Work AI agent 可 30 分钟搭建在线店铺"（TechNode 报道，2026-08） | 待验证（单一媒体，未核实一手来源） | ③ Site/Calc/BOQ（建站与核价） | 落后 | 建站自动化的叙事对方已占位，我们 Site 子系统偏"租户官网搭建+22 参数核价"，若对方真的做到"30 分钟出店"，说明建站链路自动化程度我们偏低 |
| 韩国市场专项落地（Aju Press 报道，2026-08） | 待验证 | ⑤ Trade AI Agent | 落后（区域覆盖维度） | 对方已按区域市场分版本运营，我们目前无"按市场/语言做 Agent 特化"的公开口径，需评估是否跟进（例如先补一个目标市场的能力特化） |
| 与 Qwen3.8-Max 是"独立产品"（软评类文章转述） | 传闻 | —（不构成能力对标） | 忽略 | 仅是产品关系说明，不影响能力判定 |
| Wukong 与 Accio Work 是阿里两条并行的 agentic 线 | 已确认 | ①  DeepSeek Harness（认知沙箱） | 持平 | 对方双 agent 线内部竞争/分工，我们不直接对标，仅记录 |
| 供应商数据 + Qwen 底座 + Alipay AI Pay / Agentic Commerce Trust Protocol 结算 | 已确认（Wikipedia Agentic commerce 条目） | ⑧ Browser/n8n（出站与撮合） | 落后 | 对方已接入 agentic 结算协议（ACP/UCP 系），我们的 n8n 出站目前偏"取证+分发"，未接入 agentic 交易协议层 |
| Kuo Zhang 公开倡导"降低中小企业门槛" | 传闻（转述） | —（战略而非能力） | 忽略 | 记录即可，不进对标表 |

### 1.1 本期增补（2026-09-14 由 automation `competitor-radar` 自动补录）

| 信号摘要 | 来源可信度 | 对应子系统 | 判定 | 说明 |
|---|---|---|---|---|
| 2026-09-08 Shopify 把 **Meta 纳入其 "Agentic Storefronts" 渠道**，商家后台里"Meta"成为一个可选的 AI 销售渠道；同期 Meta 发布个人 AI agent（Stripe 驱动结账） | 已确认（Wikipedia Shopify 条目 "AI commerce protocol and AI commerce" 段，一手引用 Shopify Changelog 2026-09-08、The Paypers 2026-09-09） | ⑧ Browser/n8n（出站分发与撮合） | 落后 | 对方已把"AI agent 渠道"做成商家后台的一等公民渠道位；我们的出站层目前只有约 40 个内容平台分发 + n8n webhook，渠道分类里没有"agent 渠道"这一类，也没有可勾选/可观测的撮合出口 |
| 2026-01 Shopify 与 Google 共建 **Universal Commerce Protocol（UCP）** 开放标准，目标是让 AI agent 跨平台与商家连接并成交 | 已确认（同上条目，一手引用 Axios 2026-01-11） | ③ Site/Calc/BOQ（租户官网） | 落后 | 租户官网是"人看的网站"，缺少"agent 读得懂、能直接撮合"的机读出口（结构化商品/询盘端点）。这把上一轮 §二 里"⑧ 未接入 agentic 交易协议"的评估项从"值得看"升级成"有明确协议方与时间表在跑" |

## 二、8 大子系统缺口汇总（只保留"落后"项）

| 子系统 | 缺口 | 建议动作（可排期，避免空话） | 预估工作量 |
|---|---|---|---|
| ④ DeerFlow | 缺"市场洞察/sourcing Q&A"对外能力 | 在 DeerFlow 9 意图里加一条"市场洞察"意图（复用现有研报能力，输出结构化洞察卡），先落 1-2 个行业 profile 验证 | 2-3 人日 |
| ⑤ Trade AI Agent | 缺"比价/供应商比较"采购侧能力链 | 新增一个"供应商比较"Agent 分支（复用现有 Trade AI Agent 编排框架，输入=品名+目标市场，输出=排序卡），与 WhatsApp 拓客互不干扰 | 3-4 人日 |
| ③ Site/Calc/BOQ | 建站自动化程度偏低（对方 30min 出店） | 先不追"30min"数字，改为：给租户官网模板加"一键生成行业默认套模板"（22 参数核价结果直出页面），验证是否缩短租户建站时长 | 需先出设计方案 |
| ⑧ Browser/n8n | 未接入 agentic 交易/结算协议（ACP/UCP） | 先做评估：读 Agentic Commerce Trust Protocol / UCP 公开文档，判断是否要支持"结构化商品数据被 agent 直接撮合"，出一页纸评估（不写代码） | 1 人日（评估） |

### 2.1 本期新增缺口（2026-09-14）

| 子系统 | 缺口 | 建议动作（可排期，避免空话） | 预估工作量 |
|---|---|---|---|
| ⑧ Browser/n8n | 分发渠道矩阵没有"AI agent 渠道"类目，无法像 Shopify 那样把 Meta/agent 当成一个渠道位勾选与观测 | 在渠道清单与分发配置里新增"AI agent 渠道"类目（先占配置位与观测口径，不改撮合逻辑），对齐 Agentic Storefronts 的渠道位设计 | 1-2 人日 |
| ③ Site/Calc/BOQ | 租户官网无 agent 可机读出口（商品/询盘端点无协议层） | 先出 1 页 UCP 协议映射设计：我方租户官网要暴露什么结构化端点才能被 agent 撮合；依赖 ⑧ 的协议评估结论，不直接开写代码 | 1 人日（设计） |

## 三、保持领先项（记录，不动作）

- ⑥ GoodJob CRM：单证套打（PI/CI/箱单）、7 步履约 —— 对方信号中未提及单证类能力，属我方领先项，无需动作
- ② Hermes：受控调度（静态拓扑安全、4 大执行器）—— 定位不同，持平

## 四、本期结论

落后 4 项（④⑤③⑧），领先 1 项（⑥），持平 2 项（② ①）。
建议优先做：④ DeerFlow 市场洞察意图（工作量最小、直接补最明显的能力空白），其次是 ⑧ 的"是否接入 agentic 结算协议"评估（1 人日，先判断再决定要不要排期）。

**2026-09-14 复核**：③、⑧ 两项落后**加重**（对方出现一手协议方与渠道位落地，不再是叙事占位）；④⑤ 本期无新信号，判定维持。本轮新增落后 2 项，仍集中在 ③⑧。

> 本表为人工判定版（今日）；后续每日由 automation `competitor-radar` 自动更新信号，人工只需要复核"落后"项是否仍然成立、动作是否已排期。

## 五、待排期动作（- [ ] 待办，脚本会自动提取并同步到 TODO.md §11）

- [x] ④ DeerFlow 加"市场洞察"意图（2-3 人日）（2026-09-14 已落地：技能+intent+编排模板+副驾入口，543 tests / 19 门禁通过）
- [x] ⑤ Trade AI Agent 新增"供应商比较"Agent 分支（3-4 人日）（2026-09-14 已落地：技能+intent+编排模板+副驾入口，543 tests / 19 门禁通过）
- [ ] ③ Site 一键生成行业默认套模板设计方案（先出设计方案再排期）
- [ ] ⑧ ACP/UCP agentic 结算协议接入可行性评估（1 人日，先判断是否排期）

<!-- 2026-09-14 雷达自动补录 -->
- [ ] ⑧ 分发渠道矩阵新增"AI agent 渠道"类目（对标 Shopify Agentic Storefronts 渠道位设计，1-2 人日）
- [ ] ③ 租户官网 UCP 机读出口（商品/询盘端点）先出 1 页协议映射设计（依赖 ⑧ 评估结论，1 人日）

## 六、2026-09-14 复刻落地记录 + 事实订正

### 6.1 先订正两条判定的事实错误（重要，防止后续按错判排期）

| 原判定 | 实测结论 | 订正 |
|---|---|---|
| "④ DeerFlow 缺市场洞察/sourcing Q&A 对外能力" | **表述过重**。`market_research` 这个 intent 早已存在且接通：UBrain 副驾可触发，同步走 `commercial_os_bridge.run_market_research`，异步走 `deerflow_job_service._dispatch_intent`，产出 `executive_summary`/`findings`/审核态 | 真实差距不是"有没有"，而是**深度**：旧实现的 researcher 只调 `blue_ocean` + `export_feasibility` 两个内部函数（`source_type=internal_m0`、`url=None`），给不出需求驱动、价格带、准入壁垒、买家画像、动作清单这些 Accio 会给的维度 |
| "`research.brief` 已覆盖行业趋势/竞品/关键词机会" | **不成立**。`hermes/research_brief_service.py` 是**平台自我运维研究员**：24 槽位小时轮换、只读信号、`forbidden_auto_actions` 禁止改代码发信，其中 `market_research` 槽位也只会输出"关联 GW 待办"一句模板话 | 它与面向租户/买家的市场洞察无关，不能拿来抵账。两条能力同名不同物，后续排查勿混 |

另记一次同名陷阱：仓库里的 Hermes 执行器 `accio`（`accio_executor.py` + `ubrain/accio_sales_service.py`）是**我们自己的销售飞轮**（采购商候选/开发信/谈单话术），与阿里 Accio Work 无血缘。对标时别把它当"已经复刻完了"。

### 6.2 本轮已落地的复刻（已验证）

| 层 | 落点 | 状态 |
|---|---|---|
| 技能 | `foreign_trade/market_insight_skill.py`、`supplier_compare_skill.py`；输出强制带 `confidence` / `verification_required` / `disclaimer` | 已注册（技能总数 7 → 9） |
| DeerFlow intent | `market_insight`、`supplier_compare` + `_exec_*` 专属处理函数 | 门禁 7 由 9/9 变 11/11 |
| 编排模板 | `market_intelligence`（洞察 → 横向比较 → 转关键词） | 新增 |
| 顺带修修真 bug | 模板子任务此前**永远拿不到 job payload**，导致 `buyer_research`/`outreach_letter` 走模板路径必然降级；`create_plan` 现已合并 payload（`context` 不外泄，defn 显式参数优先） | 已修 + 已加回归测试 |
| Hermes 能力 | `research.market_insight`、`research.supplier_compare` 经 `_CAPABILITY_TO_INTENT` 翻译成 intent；能力名避让既有 `research.brief`/`research.prospect` | 已接 |
| 异步任务面 | `deerflow_job_service.run_subtask_intent` 复用同一执行器，副驾与计划不再各算一份 | 已接 |
| 副驾自然语言 | `orchestrator` 新增两路 intent；缺品类/市场/候选时**直接追问**，不入队烧 token、不替用户编参数 | 已接 |

验证口径：`tests/unit` **543 passed**（新增 36 条专测）；`orchestration_selfcheck.py` **19/19**。仓库内未装 ruff/flake8，静态 lint 本轮未能执行，属遗留验证缺口。

### 6.3 仍未复刻完的部分（objective 未闭合）

- ③ 建站自动化：`site_builder` 仍是人工选模板，无"行业 Profile 一键默认套"。
- ⑧ agentic 出口：租户官网有 `llms.txt` + JSON-LD（agent **读得懂**），但没有 UCP 式的商品/询盘**可撮合端点**（agent 能直接下单/发询盘）。这是决定"流量回官网"闭环会不会被 agent 从中间截走的那一条。
- 前端入口：新能力目前只有 API / 副驾 / 编排三面可达，业务台尚无独立页面把洞察卡渲染出来。
- 旧 `market_research` 与新 `market_insight` 并存，下一步应让前者在结论里引用后者的结构化产出，避免两套说法并行。
