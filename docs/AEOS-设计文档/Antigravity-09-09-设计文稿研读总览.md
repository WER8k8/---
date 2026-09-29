# 研读总览 · Antigravity 于 2026-09-09「点开发」的全部设计文稿

> **研读日期**：2026-09-09 晚 → 续读补全
> **研读目的**：把 Antigravity 当天产出的架构法典、代码字典、注册表、组装方案、裁定书、对接方案、网关/MCP 清单一锅端读懂，并**标出其被广泛证实的错误**，供「系统组装」阶段安全取用。
> **一句话**：Antigravity 把「零件极丰富但没总装」的项目写成了一套宏大的 AEOS 法典（取数扎实、汇总注水、状态超前）。**可直接取其架构骨架与取数明细，但凡涉及端口/库/配色/数量/状态的事实，一律以《多模型设计统一裁定书》+ 实测为准。**

---

## 0. 当天产出清单（11 份文档 + 2 份数据目录）

| # | 文件 | 性质 | 可靠性 |
|---|---|---|---|
| 1 | `docs/AEOS_MASTER_ARCHITECTURE_SPEC.md` | 11 章架构法典（总纲） | 骨架可用，数字/状态多注水 |
| 2 | `docs/AEOS_MASTER_CODEBASE_INDEX.md` | 大字典（8 子系统、模型/路由/服务/技能） | 取数可靠，部分计数错 |
| 3 | `AEOS_GLOBAL_SYSTEM_REGISTRY.json` | 机读注册表（顶栏 keys + subsystems + guardrails） | 状态字段被错读为 active |
| 4 | `docs/系统组装总方案-2026-09-09.md` | 阶段 0–7 装配计划（造车比喻） | 本次最可落地的一份 |
| 5 | `docs/多模型设计统一裁定书-2026-09-09.md` | T0/T1/T2 三级判定链 + 判例表 | **仲裁真值，必读** |
| 6 | `docs/开发记录串联报告-2026-09-09.md` | 六方记录对齐（Antigravity/Trae/WB/Qoder/OpenSquilla/Claude） | 纠错证据集中在此 |
| 7 | `docs/TradeAI-GoodJob-Hermes总线对接方案-2026-09-09.md` | TradeAI×GoodJob 真桥方案 | 现状判据可靠 |
| 8 | `docs/开发交接记录-2026-09-09-AEOS判定与对接现状断点.md` | 断点交接（含路径漂移修正） | 实测可靠 |
| 9 | `docs/bankofai网关接入指南-2026-09-09.md` | AI 网关接入（已实测 48 模型） | 实测可用 |
| 10 | `docs/MCP与技能接入清单-2026-09-09.md` | PostgreSQL + Playwright MCP 接入建议 | 待你授权安装 |
| 11 | `docs/AEOS_全域代码扫描与架构设计总览-2026-09-09.html` | Trae 生成的扫描总览页 | 基线已过时 |
| — | `scratch/meticulous_scan_catalog.json` (2.18MB) | AST 扫描明细（Antigravity 取数证据） | 原始数据 |
| — | `scratch/meticulous_frontend_assets_catalog.json` (627KB) | 前端资产扫描明细 | 原始数据 |

---

## 1. AEOS 架构法典（文档 1/2/3 的核心立意）

**定位**：把优丁从「建材 SaaS」抽象成「去行业化的通用 B2B AI 操作系统」——四维数学模型（Catalog Item / Counterparty / Deal Pipeline / Commercial Instrument）。

**八大子系统（SYSTEM-LOCK-02，不可裁减）**：
1. Core Backend（FastAPI + PG229表 + Hermes + Celery）
2. DeepSeek Harness（外层认知沙箱，Cordis JSON-RPC）
3. Hermes（内层受控 DAG 编排内核，Governor 防爆 + JsonPath 数据总线 + Saga 补偿）
4. DeerFlow（深研/内容工厂，9 intent）
5. Trade AI Agent（全域 Outbound 拓客 + WhatsApp）
6. GoodJob CRM（7 步履约 + WhatsApp 翻译 + PI/CI/PL 单证）
7. 350+ 资产（76 skills + 276/309 AgencyZH + 286 ECC）
8. Browser Runtime + n8n（取证 + 40+ 出站）

**三层 Agent 拓扑**：DeepSeek Harness（意图→TaskGraphSpec）↔ Hermes（派发 `hermes_node:<executor>`）。

**七轨变现 + Event Sourcing Token Ledger + DAG Governor（max_nodes≤100 + DFS 环路检测）**——这些是设计层共识，未被反驳。

> ⚠️ 法典的「每个节点都有代码实体、零假交付」是**自我宣称**，与实测（executor 是桩、22 参数核价不存在、PSSP 不存在）冲突。详见 §3。

---

## 2. 代码大字典（文档 2）可取用的真实明细

- 后端 `backend/app/`：**93 模型 / 150 路由 / 42 服务 / 12 Celery 任务**；1207+ 端点（注意：有 4268/2135/1616/1207/4269 五种口径混用）。
- 服务重点：`hermes/`(66)、`ubrain/`(81)、`root_services/`(255)、`foreign_trade/`(28)、`cross_border/`(29)、`deerflow/`(5)、`browser_runtime/`(6)、`n8n/`(3)。
- Trade AI Agent（`_external/trade-ai-agent`）：FastAPI，13 个 router，自带 PG `trade_ai`@5432/Redis/Celery，**自身占 8000 端口**（与主后端冲突，接入须错端口）。
- GoodJob CRM（`_external/goodjob-crm`）：Node/TS，含 `uj-bridge-routes.ts` + `agent-api-contracts.ts` 官方桥、`whatsapp-service.ts`（whatsapp-web.js + Twilio）、`customs-export.ts`、单证工作室；依赖 MySQL + BullMQ(Redis)。
- 资产：skills 76（active 入库）✅；AgencyZH 磁盘实测 **323** 个 .md（非 276/309）；ECC 实测 **286** SOP / 2444 文件。

---

## 3. ★ 已被实测推翻的 Antigravity 错误（读它的文稿时必须清零再信）

来源：`多模型设计统一裁定书` 判例表 + `开发记录串联报告` §5「说错了的」。

| # | Antigravity 说法 | 实测真值 | 性质 |
|---|---|---|---|
| 1 | 3000 官网 = 薄荷绿 `#4a9b8c` | 砖橙 `rgb(154,52,18)`（Vite 运行源） | ❌ T0 事实错 |
| 2 | 数据库 = SQLite | 原生 PG 15.8 @5433（229 表，head=105） | ❌ T0 事实错 |
| 3 | 239 张表 | ORM 实测 **225**；PG 实跑 **229** | 计数错 |
| 4 | 1,499 路由端点 | 自算明细 **1,397** | 计数错 |
| 5 | AgencyZH 276 / 309 | 磁盘 **323** .md | 计数错 |
| 6 | GoodJob CRM 扫描 0 / 590 文件 | 实际 **598** 文件（扫描有洞） | 计数错 |
| 7 | 19 项自检门禁 | 实测 **18**（另有 14 口径）→ 以 `orchestration_selfcheck.py` 实跑为唯一真值 | 口径漂移 |
| 8 | Trade AI / GoodJob「已实装 active」 | registry `ready_for_adapter` 被错读；**executor 是纯 mock 桩**（假线索/假 PI/假翻译） | ❌ 状态超前 |
| 9 | DeerFlow「内容工厂已实现」 | 6 文件 / 2,420 行；「9 intent 真执行」待证 → 标 🟡 已规划 | 状态超前 |
| 10 | 前端 API 由 Orval 生成 | 手写 axios / 原生 fetch | 描述错 |
| 11 | orchestration 含 Temporal 工作流 | 全库无 temporalio | 描述错 |
| 12 | 生效配置 = `config/dev/.env` | 实为 `backend/.env` 覆盖前者（本轮初版也写错过） | 事实错 |
| 13 | 22 参数 BOQ 核价 / PSSP 资产组装 | 代码**根本不存在** | ⚫ 虚构 |

> **规律**：数字多半能对上，**结论普遍超前或过时**；越往汇总层走越容易注水。裁定书铁律：**争论只在 T0/T1 用事实裁定，T2 愿景只要求三态标注（🟢已实现 / 🟡已规划 / 🔴待接入）。**

---

## 4. 系统组装总方案（文档 4）—— 这才是「继续推进」的施工蓝图

**诊断比喻**：发动机（AI Key 空/gateway 是桩）、传动（Hermes 两执行器空转）、车轮（BOQ 核价没装）、刹车（租户隔离 no-op、RLS 关）、油箱（Redis 被脚本强关）、仪表盘（自检项三口径）、底盘（官网双形态分叉 + worktree git 断链）。

**四条规程（必须先立）**：
- 规程一：配置单一真源（`backend/.env` 覆盖 `config/dev/.env`；归档孤儿 `config/.env.dev`；**Redis 值在 env 里其实是对的**，风险在「用错启动脚本强制关 Redis」）。
- 规程二：防伪标记（mock 必须带 `simulated:true` + 单测）。
- 规程三：每个接点一个端到端验收脚本（可证副作用）。
- 规程四：单一真相源 + 变更留痕。

**依赖拓扑与关键路径**：
```
阶段0 地基(env/Redis/PG/n8n/git/门禁)
  → 阶段1 底盘(登录·四壳·RBAC·租户隔离·RLS + Hermes 内核)
      → 阶段3 入站/出站(Site/BOQ/发布/Browser)
          → 阶段4 获客履约(TradeAI + GoodJob)   ← 最大认知差
              → 阶段6 计费/支付/财务
阶段2(Harness+DeerFlow)、阶段5(资产) 可并行插入，不阻塞主链
阶段7(双后端合一/官网收敛) 必须最后做
```
**关键路径 = 0→1→3→4→6**。

**立即可开始的三件事（低风险、独立回滚、等你点头）**：
1. **规程一**（半天）：归档 `config/.env.dev` + 修正 `config.py:27` 错误注释 + 给会关 Redis 的脚本加警告（**别再改 env 里的 Redis 两行**）。
2. **接点 10**（半天）：修 `start.bat` 自检块，让「启动成功」重新可信。
3. **规程二**（1–2 天）：给 Trade AI / GoodJob 两 mock 执行器加 `simulated` 标记 + 单测，先堵「假交付」口子。

---

## 5. TradeAI × GoodJob 真桥方案（文档 7）—— 阶段 4 的细化

- **选型 A（推荐）**：异步 HTTP Bridge，Hermes adapter 经 HTTP 调 `_external` 的现成 API（trade-ai `/api/v1/*`；goodjob `uj-bridge`/`agent-api-contracts`），返回 JSON 回写 `ai_tasks.output_json`。
- **能力映射已列全**：`prospect.scrape`→`POST /customer/search`、`outreach.whatsapp`→`POST /whatsapp/send`、`document.generate_pi`→goodjob 单证工作室（返回 docId/PDF）、`im.translate`→真翻译（非 `[Translated]` 桩）。
- **六件套 P0–P2**：新增 `clients/trade_ai_client.py` + `goodjob_client.py` → 改造两 executor 由桩→真调 → 启动编排（trade-ai 错端口 8010）→ Saga 真补偿 + 真 Token 计量 + WhatsApp `wa_message_id` 回写 → 升级自检 Check14/15/16 为真实端口冒烟。
- **验收判据**：桩给 `buyer{i}@…-intl.com` / `status:"sent"` / 硬编码 PI；真桥给真实线索 + `wa_message_id` + 真 docId/PDF。

---

## 6. bankofai 网关（文档 9）+ MCP（文档 10）

- **bankofai**（已实测）：`https://api.bankofai.io/v1`，key 已给。**免费可用**：`qwen3.8-flash`（默认）/ `glm-5.3-flash` / `hy3`；`gpt-5.x`/`claude`/`gemini`/`kimi`/`minimax`/`deepseek-v4-flash` 需充值。**注意系统代理 7897 直连 `api.bankofai.io`**。上一个 `kktoken.cc` 网关已弃用。
- **MCP 清单（待你授权安装）**：P0 = PostgreSQL MCP（建专用只读角色 `mcp_reader`，**勿用应用凭证**）+ Playwright MCP（验官网渲染/四壳/破锁）。P1 = redis-mcp / docker-mcp / fetch。明确**不要用** Anthropic 归档的 `server-postgres`（有注入漏洞）。

---

## 7. 研读取信结论（fulfillment state）

- **已完成**：11 份文档 + 2 份数据目录已全部读毕并交叉核对；Antigravity 的架构骨架、可取用明细、错误清单均已厘清。
- **未满足/需你裁决**：官网收敛路径 A/B/C（P0-14）、计费三轨 vs 七轨、BOQ 实现或下架、TradeAI MIT LICENSE——四项仍悬置。
- **验证结果**：错误清单来自裁定书 + 串联报告 + 源码实测，可信；bankofai 为实测通过。
- **不能证明**：法典自称「零假交付/每节点有实体」——已被实测推翻，不能当作现状。

---

## 8. 下一步建议（对应「继续推进昨天到了这里」）

最稳妥的起步 = 文档 4 的「立即三件事」（规程一 + 接点10 + 规程二），均不动业务逻辑、可独立回滚。做完再进阶段 1 的租户隔离修复。**需你明确「继续」即开始执行这三件；MCP 安装需你授权配置目录。**

*EOF · 研读总览 · 基于 2026-09-09 工作区实测*
