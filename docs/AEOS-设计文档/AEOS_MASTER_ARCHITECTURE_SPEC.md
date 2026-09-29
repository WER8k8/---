# AEOS (Autonomous Enterprise Operating System) 全域企业级 AI 操作系统 · 终极宏图架构与全链路流转总纲 (v1.0)

> **文件定位**：全域 8 大子系统、350+ 智能资产、Chrome 原生缓存五大设计、无行业偏见通用 B2B 闭环流转的最高设计法典。  
> **设计准则**：业界最先进技术标准 · 极度严格 · 节点全流畅驱动 · 零假交付 · 绝对可落地。  
> **生效时间**：2026-09-08 | **架构师核准**：Chief Architect & System Designer  

---

## 目录
1. [第一章：系统哲学与去行业化通用 B2B 抽象](#第一章系统哲学与去行业化通用-b2b-抽象)
2. [第二章：全景八大子系统物理拓扑图（SYSTEM-LOCK-02）](#第二章全景八大子系统物理拓扑图system-lock-02)
3. [第三章：双层 Agent 拓扑（DeepSeek Harness 外层 ↔ Hermes 内层）](#第三章双层-agent-拓扑deepseek-harness-外层--hermes-内层)
4. [第四章：主动拓客闭环（Trade AI Agent + Apollo/Clay 模式）](#第四章主动拓客闭环trade-ai-agent--apolloclay-模式)
5. [第五章：入站转化与 BOQ/参数化核价中枢（Site + Calc Engine）](#第五章入站转化与-boq参数化核价中枢site--calc-engine)
6. [第六章：7 步履约、WhatsApp 实时翻译与外贸单证工作室（GoodJob CRM）](#第六章7-步履约whatsapp-实时翻译与外贸单证工作室goodjob-crm)
7. [第七章：350+ 智能资产网络与 PSSP 组装编排](#第七章350-智能资产网络与-pssp-组装编排)
8. [第八章：取证持久化与出站广播网络（Browser + n8n）](#第八章取证持久化与出站广播网络browser--n8n)
9. [第九章：自进化引擎与企业长期记忆（Experience Engine TASK-041~050）](#第九章自进化引擎与企业长期记忆experience-engine-task-041050)
10. [第十章：七轨商业变现模型与 Billing 计量账本（TASK-071~080）](#第十章七轨商业变现模型与-billing-计量账本task-071080)
11. [第十一章：DAG Governor 拓扑防爆与 19 项全景自检门禁法典](#第十一章dag-governor-拓扑防爆与-19-项全景自检门禁法典)

---

## 第一章：系统哲学与去行业化通用 B2B 抽象

### 1.1 摒弃特定商品滤镜的通用抽象
本系统不再局限于单一实体行业（如建材、服装、机械），而是将全球商业经营提炼为**四维通用数学抽象模型**：
1. **Catalog Item（参数化商品标的）**：
   $$\text{Item} = \{ \text{SKU}, \text{Specs Matrix}(\text{公差, 材质, 规格, 认证}), \text{Price Function}(Q, \text{Terms}), \text{MOQ}, \text{LeadTime} \}$$
   - 支持从毫米级公差的物理构件、非标定制加工品，到数字化企业服务的统一参数化建模。
2. **Counterparty（交易对手方画像）**：
   $$\text{Party} = \{ \text{Domain}, \text{Country}, \text{Persona}(\text{采购决策链}), \text{Credit Rating}, \text{Preferred Channel} \}$$
3. **Deal Pipeline（履约推进状态机）**：
   严格的不可逆 7 步外贸漏斗状态机：
   $$\text{Inquiry} \longrightarrow \text{Contacted} \longrightarrow \text{Quoted} \longrightarrow \text{Sample} \longrightarrow \text{Negotiation} \longrightarrow \text{Won} \longrightarrow \text{Fulfillment}$$
4. **Commercial Instrument（商业与法定单证）**：
   包含形式发票 (PI)、商业发票 (CI)、装箱单 (PL)、提单提样、报关草单的通用合规票据树。

---

## 第二章：全景八大子系统物理拓扑图（SYSTEM-LOCK-02）

```text
                                ┌──────────────────────────────────────────────┐
                                │      1. DeepSeek Harness (外层认知沙箱)        │
                                │   Everything is a Plugin · Cordis JSON-RPC   │
                                └──────────────────────┬───────────────────────┘
                                                       │ 1. 意图解析 & 生成 TaskGraph
                                                       ▼
                                ┌──────────────────────────────────────────────┐
                                │       2. Hermes Control Plane (受控核心面)    │
                                │      FastAPI + PostgreSQL 15.8 (229表) @5433 │
                                │    DAG Supervisor (Governor防爆 + JsonPath)  │
                                └──────────────────────┬───────────────────────┘
                                                       │ 2. 契约分发 hermes_node:<executor>
         ┌──────────────────────────────┬──────────────┴────────────────┬─────────────────────────────┐
         ▼                              ▼                               ▼                             ▼
┌──────────────────┐          ┌───────────────────┐          ┌────────────────────┐          ┌───────────────────┐
│ 3. Trade AI Agent│          │    4. DeerFlow    │          │  5. GoodJob CRM    │          │6. Site/Calc Engine│
│ (全域Outbound拓客)│          │ (深度研报/内容工厂) │          │ (7步履约/单证工作室)│          │(独立站/22参数核价) │
│ - 社媒/Maps 潜客  │          │ - 9大 Intent 真执行│          │ - 7步状态机流转    │          │- 22模块高转化站   │
│ - WhatsApp 批量外联│         │ - Programmatic SEO│          │ - WhatsApp双向翻译 │          │- BOQ 标书清单解析 │
│ - 统一收件箱意图分类│        │ - 40+多渠道母版   │          │ - PI形式发票自动开具│          │- 动态实时计算器   │
│ - 多轮冷邮件序列 │          │ - 关键词雷达探测  │          │ - CI/PL成套报关出口│          │- Case Study信任库 │
└────────┬─────────┘          └─────────┬─────────┘          └─────────┬──────────┘          └─────────┬─────────┘
         │                              │                              │                               │
         └──────────────────────────────┼──────────────────────────────┴───────────────────────────────┘
                                        │ 3. 产物与证据归流 (Data Flow)
                                        ▼
         ┌─────────────────────────────────────────────────────────────┐
         │          7. 350+ 专家资产网络 (PSSP 动态组装与知识注入)        │
         │  76 业务技能 (skills/) + 276 角色 (agency/) + 286 ECC 防错规约 │
         └──────────────────────────────┬──────────────────────────────┘
                                        │ 4. 执行取证与出站分发 (Delivery)
                                        ▼
         ┌─────────────────────────────────────────────────────────────┐
         │         8. Browser Runtime & n8n 40+ 全球出站履约网络        │
         │ - Browser: 无头沙箱运行 + Disk JSONL & DB TaskTrace 双轨取证 │
         │ - n8n: 5678 容器出站 Webhook (`site_built` / `content_pub`) │
         └─────────────────────────────────────────────────────────────┘
```

---

## 第三章：双层 Agent 拓扑（DeepSeek Harness 外层 ↔ Hermes 内层）

### 3.1 架构分工（宪法级隔离）
- **外层（DeepSeek Harness）**：
  - 定位：**认知、规划、探索与非受控意图拆解沙箱**。
  - 技术栈：开源 Cordis 架构，Python SDK 通过 `stdio` 与预构建原生 `dsh.exe` 驱动子进程。
  - 输出物：严谨的 `TaskGraphSpec`（JSON 格式计划图）。
  - **禁令**：禁止直接读写物理生产数据库，禁止直接执行破坏性金融交易。
- **内层（Hermes Agent & DAG Supervisor）**：
  - 定位：**企业受控执行内核、状态机仲裁者与安全防火墙**。
  - 技术栈：FastAPI + Celery + PostgreSQL 15.8，驱动 `ExecutorRegistry`。
  - 核心职责：DAG 拓扑防爆校验、JsonPath 动态数据解析、Saga 逆向补偿、Token 计量、安全鉴权。

---

## 第四章：主动拓客闭环（Trade AI Agent + Apollo/Clay 模式）

### 4.1 四步 Outbound 自动猎手流水线
1. **潜客雷达探测 (`prospect.scrape`)**：
   - 调度 `skill_social_scraper.py`，按区域（如中东、欧美、东南亚）、关键词、采购意向进行自动化探测。
   - 萃取买家结构化档案：`{ company_name, country, contact_name, email, whatsapp, intent_score }`。
2. **多通道冷触达外联 (`outreach.whatsapp` / `outreach.email`)**：
   - 调度 `skill_auto_sender.py`，采用高转化率多语言模板，支持时区定时与随机时间间隔防封号。
3. **多语言智能收件箱意图分类 (`inbox.classify`)**：
   - 对外联回复进行语义解析，打标分类：
     - `RFQ / Price Inquiry`（询盘报价，置信度高，自动建档并通知销售）
     - `Sample Request`（样品申请，流转至样品履约）
     - `General Inquiry`（常规问答，由 AI 辅助草拟回复）
     - `Opt-Out`（退订要求，自动进黑名单并终止序列）

---

## 第五章：入站转化与 BOQ/参数化核价中枢（Site + Calc Engine）

### 5.1 BOQ (Bill of Quantities) 标书工程量清单智能抽取
- **痛点**：B2B 采购通常发来几十页复杂的 PDF / Excel 标书清单，人工核算需要数天。
- **实现**：
  - 通过视觉模型与表格抽取算法解析多层级结构：`物料编号 | 描述 | 参数标准 | 预估工程量 | 单位`。
  - 自动归一化单位（如平米、立方米、吨、支、箱），并与产品数据库进行参数模糊匹配。

### 5.2 22 模块垂直参数核价计算器
- **计算逻辑**：
  $$\text{Unit Price} = \left( \text{Raw Material Base}(\text{材质, 规格}) + \text{Processing Cost}(\text{工艺, 表面处理}) \right) \times (1 + \text{Gross Margin}) + \text{Incoterm Cost}(\text{FOB/CIF 海运费})$$
- 秒级输出带有工程量清单、公差技术说明与阶梯核价明细的结构化核价单。

---

## 第六章：7 步履约、WhatsApp 实时翻译与外贸单证工作室（GoodJob CRM）

### 6.1 外贸 7 步销售管道状态机
由 `GoodJobCrmExecutor` 严格托管的交易漏斗：
$$\text{Stage} \in \{ \text{Inquiry}, \text{Contacted}, \text{Quoted}, \text{Sample}, \text{Negotiation}, \text{Won}, \text{Fulfillment} \}$$

### 6.2 WhatsApp 本地双轨插件与实时双向翻译 (`whatsapp-plugin/`)
- **连接层**：独立 Node.js 服务，基于 **Baileys 协议** 真实直连 WhatsApp Web。
- **实时双向翻译链路**：
  $$\text{海外买家 (阿拉伯语/西语/英语)} \xrightarrow{\text{Baileys}} \text{接收} \xrightarrow{\text{AI 实时翻译}} \text{中文 (卖家销售端)}$$
  $$\text{卖家销售端 (中文回复)} \xrightarrow{\text{AI 精翻}} \text{买家母语} \xrightarrow{\text{Baileys}} \text{发送给买家}$$
- 沟通零语言障碍，对话历史全链路持久化并挂接至 CRM 客户时间轴。

### 6.3 智能形式发票生成器 (PI Generator)
- 契约能力：`document.generate_pi`
- 自动提取买卖双方抬头、银行账户信息（开户行、SWIFT Code、账号、受益人）。
- 自动换算汇率与中英文金额大写（例如：`USD TWENTY-FIVE THOUSAND ONLY`）。
- 注入贸易条款（FOB/CIF）、付款方式（30% T/T Deposit, 70% before shipment）与交期声明。
- 秒级生成标准 PDF / Excel 供买家签署转款。

### 6.4 成套外贸出口单证工作室 (Trade Docs Studio)
- 契约能力：`document.generate_trade_docs`
- 基于统一核准的 PI 数据源，一键同步派生成套出口合规单据：
  1. **商业发票 (Commercial Invoice - CI)**
  2. **装箱单 (Packing List - PL)**：包含毛重 (Gross Weight)、净重 (Net Weight)、体积 (CBM) 与件数分配
  3. **报关草单与原产地证 (COO) 申办草案**

---

## 第七章：350+ 智能资产网络与 PSSP 组装编排

### 7.1 三层资产分类法
| 资产族 | 数量 | 物理路径 | 核心职责 |
|---|---|---|---|
| **Business Skills** | 76 | `skills/` | 业务原子能力：SEO、A/B测试、冷邮件、广告投放、用户研究等 |
| **Agency Roles** | 276 | `_external/agency-agents-zh/` | 细分行业专家人设：外贸总监、技术工程师、合规审计师等 |
| **ECC Engineering SOP** | 286 | `_external/ecc/` | 质量工程门禁：代码合规、防错检查单、发布标准等 |

### 7.2 PSSP (Persona-Skill-SOP-Prompt) 动态组装机制
在 Hermes 调度任意节点时，调度器自动根据任务属性动态装配执行体：
$$\text{Agent Container} = \text{Persona}(\text{选定角色}) \oplus \text{Skill}(\text{选定业务技能}) \oplus \text{SOP}(\text{工程防错规范}) \oplus \text{Dynamic Context}$$

---

## 第八章：取证持久化与出站广播网络（Browser + n8n）

### 8.1 Browser Runtime 双轨取证系统
- **运行方式**：Playwright / 无头沙箱在隔离环境中运行外部信息获取与页面交互。
- **双轨证据持久化**：
  1. **磁盘审计轨 (Disk JSONL)**：按租户和日期持久化写入 `audit.jsonl`，记录所有网络请求截屏、状态码与控制台日志。
  2. **数据库快照轨 (DB TaskTrace)**：将操作证据注入 PostgreSQL `task_traces.artifacts` 字段，实现审计数据与商机实体强绑定。

### 8.2 n8n 出站广播分发中枢
- **端点**：`http://127.0.0.1:5678` 容器化运行。
- **已激活生产出站 Webhook**：
  - `site_built_notify`：站点/Landing Page 构建完毕，触发多平台上线通知与站长提交。
  - `content_publish_dispatch`：一篇母版内容自动变体，分发广播至海外与国内 40+ 媒体平台。

---

## 第九章：自进化引擎与企业长期记忆（Experience Engine TASK-041~050）

### 9.1 数据进化闭环（越用越聪明的底层逻辑）
系统绝非简单调用公共大模型，而是建立**企业私有经验沉淀中心**：
```text
业务交互完成 (询盘/成单/被拒)
       │
       ▼
[经验提炼器 Experience Extractor] 
       │ 抽取：沟通痛点、成交要素、反驳话术、报价敏感阈值
       ▼
[经验经验库 Experience Store] (PG evolution_experiences 表)
       │ 结构化入库与打标 (分类/有效度/权重)
       ▼
[金丝雀评测 Canary Evaluation] (A/B 测试新话术与旧方案)
       │
       ▼
[Prompt / SOP 自动版本升级] (无需重新训练基座模型，实现软件工程化自进化)
```

### 9.2 跨产业无感迁移能力
因为商品属性、买家画像和交易管道完全解耦参数化，当企业从品类 A 切换至品类 B 时，系统仅需灌入品类 B 的规格参数表，底层的拓客、履约、单证与进化引擎即可 100% 原样复用！

---

## 第十章：七轨商业变现模型与 Billing 计量账本（TASK-071~080）

### 10.1 七种商业模式支持矩阵
1. **SaaS Subscription（基础/专业/旗舰订阅年费）**
2. **Pay-per-use（按询盘单次计费 / 优质大额标书计费）**
3. **AI Token Metering（大模型推理 Token 事件溯源追加写账本）**
4. **Dedicated Egress Slots（静态住宅 IP / 浏览器指纹槽位租借）**
5. **Lead Generation Commission（促成交易后的佣金分成结算）**
6. **Freemium & Growth Viral（免费基础版 + 呼朋唤友裂变奖励）**
7. **API / Agent Marketplace（向生态开发者输出行业能力与 Agent 出口）**

### 10.2 Token Ledger 零行锁死锁保证
- 财务与用量事件采用 **Event Sourcing（追加写）** 模式写入 `meter_events`，彻底杜绝高并发扣费时的数据库行锁争抢。
- 采用 Celery 定时任务 `aggregate_meter_events` 执行批量对账与额度核减。

---

## 第十一章：DAG Governor 拓扑防爆与 19 项全景自检门禁法典

### 11.1 DAG Governor 双重安全防线
1. **单图规模硬上限**：`len(nodes) <= 100`，严格拦截大模型逻辑失控生成的无限节点图。
2. **DFS 环路死锁检测**：在建表派发前遍历有向依赖图，精准拦截任何循环依赖（如 `A -> B -> A`），拒绝入库并抛出清晰告警。

### 11.2 自动化 19 项全景门禁核验标准 (`orchestration_selfcheck.py`)
| 序号 | 检查项 | 验证内容 | 门禁标准 |
|---|---|---|:---:|
| 1 | 数据库连通 | PostgreSQL 15.8 @5433 连通性 | 229 表全部就绪 |
| 2 | Alembic 迁移 | 迁移链头状态 | 严格单 head `105_reconcile_model_backfill` |
| 3 | Celery 任务注册 | 分布式任务池 | 18 个核心任务全部注册 |
| 3b | Beat 定时匹配 | Celery Beat 调度器 | 12/12 调度项无断裂匹配 |
| 4 | 编排路由挂载 | 核心编排入口 | `/orchestration` 与 `/deepseek-harness` 挂载 |
| 5 | 统一任务面桥 | hermes_task_bridge | 支持场景全集注册 |
| 6 | n8n 内建工作流 | 出站 Webhook | `site_built_notify` 与 `content_publish` 激活 |
| 7 | DeerFlow intent | 研报与内容能力 | 9/9 意图分支全部覆盖 |
| 8 | DeerFlow 真执行 | 执行器源码 | 0 代码占位，100% 真实执行 |
| 9 | 外贸技能注册 | 外贸工具箱 | 7 大核心技能动态可用 |
| 10 | Browser 取证 | 证据链持久化 | Disk JSONL + DB TaskTrace 双轨均生效 |
| 11 | 技能包发现 | 业务技能库 | 76 个业务原子技能 frontmatter 全部解析 |
| 12 | 技能包入库 | PostgreSQL skills 表 | 76/76 active 正常入库 |
| 13 | 技能意图匹配 | 意图打分路由 | 核心意图 100% 准确命中技能 |
| 14 | Hermes 执行器契约 | P0 调度基座 | `advance_plan()` 实装，JsonPath 总线打通 |
| 15 | Trade AI Agent | 物理拓客中枢 | 源码完整，WhatsApp 路由与 Scraper 齐备 |
| 16 | GoodJob CRM | 履约与单证中枢 | Baileys 服务、PI 规约与单证工作室就绪 |
| 17 | 全域法典与硬锁 | 系统完整性 | `AEOS_GLOBAL_SYSTEM_REGISTRY.json` + `SYSTEM-LOCK-02` |
| 18 | 多核执行器调色盘 | 执行器矩阵 | `['accio', 'deerflow', 'goodjob_crm', 'trade_ai_agent']` |

---

## 结语：工业落地的终极承诺
**每个环节做正确的事。** 本设计不是概念演示，而是每一个节点都有代码实体、每一个数据流都有 JsonPath 校验、每一个子系统都有物理路径支撑的工业级 AI 操作系统。
此总纲为系统后续迭代与业务规模化扩张的唯一最高指南！
