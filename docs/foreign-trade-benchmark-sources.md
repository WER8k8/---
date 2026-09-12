# 外贸生态取长补短 · 标杆来源

> 随源码部署索引：`backend/app/data/foreign_trade_ecosystem_catalog.json` → `benchmark_sources`  
> API：`GET /api/v1/foreign-trade/ecosystem/benchmarks`

## 总原则

| 我们（SaaS） | 外部开源/导航 | 策略 |
|--------------|---------------|------|
| 多租户 + Admin + 合规边界 | 单机/全链路/真 SMTP | **取 playbook 与字段模型，不 fork 整仓** |
| 草稿 + deliverability + human_verify | 自动群发/爬虫账号池 | ** deliberately 不做** |
| Hermes/DeerFlow/Accio 编排 | LangGraph/Hermes 单机 | **sidecar 或 skill 登记** |

---

## 1. [EricHong123/Eric_Frank](https://github.com/EricHong123/Eric_Frank)（Trade AI Agent）

**定位**：外贸 B 端全链路 Agent — 社媒挖掘 → 清洗 → 邮件/WhatsApp 触达 → 询盘 AI 回复 → 老板接管。

| 取长 | 补短（我们不跟） |
|------|------------------|
| Skill 插件 + 可视化工作流（LangGraph） | 真 SMTP/WhatsApp 全自动群发 |
| RAG 知识库答专业问题 | TikTok/IG 反爬 + IP 池（合规风险） |
| 老板端监控 / 一键接管对话 | README 含未合并冲突，工程成熟度待验 |

**落地到我们**：

- 工作流 → `hermes_plugin_catalog` + n8n examples  
- 接管 → `inquiry` assign + 飞书告警（已有）  
- RAG → DeerFlow ResearchBrief + 桌面知识库  
- 社媒挖掘字段清单 → `ResearchBrief` 主题 `social_lead_fields`

---

## 2. [tshwangq/awesome-foreign-trade](https://github.com/tshwangq/awesome-foreign-trade)

**定位**：外贸 Awesome 清单（B2B 平台、沟通工具、关务/HS、背景调查）。

| 取长 | 补短 |
|------|------|
|  curated 外链（阿里国际站、TradeKey、HS 编码站等） | 非可执行代码 |
| 研究员速查 | 需人工维护时效 |

**落地**：Hermes 研究员 Brief 轮换外链；`nav8.top` 互补（见下）。

---

## 3. [frank-young/nana-crm](https://github.com/frank-young/nana-crm)（忽略许可证警告）

**定位**：传统外贸 CRM + EDM（2016，JS，停更但字段模型仍有参考价值）。

| 取长 | 补短 |
|------|------|
| 客户 / 产品 / 询盘 / 邮件营销表关系 | 无 AI、无多租户、无现代鉴权 |
| EDM 序列与询盘状态机思路 | 代码不可直接并入 |

**落地**：`inquiry` + MEDDPICC + `source_utm` 对标其 CRM 深度；**不 fork**；PI/报价阶段见 open-erp。

---

## 4. [QuantumCanvaX/open-erp](https://github.com/QuantumCanvaX/open-erp)

**定位**：开源外贸 ERP 供应链（~72★，JS，Apache-2.0，2024 后少更新）。

| 取长 | 补短 |
|------|------|
| 订单 / 采购 / 库存 / 出货单 B2B 流程 | 技术栈老，与 Vue Admin 不统一 |
| PI → 定金 → 生产 → 报关链路 | 全量 ERP 超 SaaS 边界 |

**落地**：GW-L-PL-01 管道阶段（MQL→SQL→报价→PI→定金）字段参考；询盘 webhook 同步 **P2**（与 ERPNext 二选一运维自建）。

---

## 5. [nav8.top 外贸驿站](https://nav8.top/)

**定位**：外贸导航 — B2B 平台、关务、收款、SEO、黄页、工具箱。

| 取长 | 补短 |
|------|------|
| 分类全（阿里/DHgate/WorldFirst/HS/背调） | 非 API，需人工策展 |
| 新人 onboarding 书签 | 链接时效需巡检 |

**落地**：`external_nav.curated_categories`；ResearchBrief 每周抽 1 类工具做「礼仪/禁忌/发送窗口」笔记（GW-R 研究员模板）。

---

## 6. [xiongQvQ/AI_Find_Customer](https://github.com/xiongQvQ/AI_Find_Customer)（AI Hunter）

**定位**：LangGraph 找客 — Insight→Search→LeadExtract→Evaluate；邮件 **人工批准** 后可 campaign。

| 取长 | 补短 |
|------|------|
| 证据链评分 + Pilot 小规模验证 | 开源版含 SMTP scheduler（我们仅草稿） |
| 多通道搜索（Google/B2B/Maps） | 需独立部署 + API token |
| b2b-lead-hunter Skill（Hermes 定制版） | 与 Accio human_verify 重复部分 |

**落地**：**P1 sidecar/MCP** → `prospect_enrichment`；批准流对齐 `outreach_deliverability`；禁止自动发信进主镜像。

---

## 7. [chefroger/smart-trade-ai](https://github.com/chefroger/smart-trade-ai)

**定位**：外贸员本地 AI 助手 — **15 项 Skill**（背调 6 层、开发信、LinkedIn 日历、PI/合同 DOCX）。

| 取长 | 补短 |
|------|------|
| 6 层 OSINT 背调清单 | 单机 SQLite，非 SaaS |
| 报价单/PI/合同模板生成 | 依赖 Hermes Agent 本地 |
| 阿里国际站/中国制造网「平台诊断」 | B2B 平台登录态不可共享 |

**落地**：背调 checklist → `accio_skill_catalog` / 找客 disclaimer；商务文档 → GW-L P1「报价 PI 导出」；**不 vendoring** `~/.trade/` 架构。

---

## 8. [qingchuh/sale_agent_factory](https://github.com/qingchuh/sale_agent_factory)（AIBD-FactoryLink）

**定位**：工厂外贸 BD Agent — 官网 onboarding → ICP → 全球找客 → 多渠道执行。

| 取长 | 补短 |
|------|------|
| 官网一键抽产品/认证/优势 | Web UI 仍在 roadmap |
| ICP + 漏斗 + 交接摘要 | Celery 邮件序列（合规同 Eric_Frank） |

**落地**：`tenant_onboarding` + `site-editor` 抽 manifest；ICP → `customer_finder`；交接 → `inquiry_intel` + MEDDPICC。

---

## 9. GitHub 搜索「外贸」第 7 页及以后

**链接**：[search p=7](https://github.com/search?q=%E5%A4%96%E8%B4%B8&type=repositories&p=7)

| 取长 | 补短 |
|------|------|
| 持续发现小众工具（spam 过滤后） | VPN/电子书噪声大 |
| 桌面库 `出海计/github-trade-filtered.json` | 需 `GITHUB_TOKEN` 补全 591 条 |

**落地**：仅更新 `github_curated` + 研究员 memo，**不批量 fork**。

---

## 能力对照矩阵（我们 vs 标杆）

| 能力 | 我们现状 | 最佳外部参考 | 下一步 |
|------|----------|--------------|--------|
| 找客/enrichment | Accio + human_verify | AI_Find_Customer, Eric_Frank Skill1 | MCP sidecar P1 |
| 开发信 | deliverability 包 | smart-trade-ai, Eric_Frank | OB 前台 P1 |
| 背调 OSINT | 部分 intel | smart-trade-ai 6 层 | checklist JSON P1 |
| 询盘/CRM | inquiry + MEDDPICC | nana-crm 字段 | Pipeline 阶段 P1 |
| ERP/PI | 无 | open-erp, ERPNext | webhook P2 |
| 工作流 | Hermes + n8n | Eric_Frank LangGraph | 已有，补 UI |
| 知识/导航 | catalog + 出海计 | awesome-FT, nav8 | Brief 外链轮换 |
| 真 EDM 群发 | **不做** | nana-crm, UZonMail | 仅草稿 |

---

## 部署说明

- 以上内容 **仅 JSON + 文档进镜像**；sidecar 见 `deploy/docs/FOREIGN-TRADE-ECOSYSTEM-DEPLOY.md`  
- 运维拉取 AI_Find_Customer：clone 上游 + `AI_FIND_CUSTOMER_URL` + `--profile sidecars`（主仓已接线 `ai_find_customer_sidecar.py`）

---

## 10. B2B 主动拓客开源清单（用户策展 · 2026-06-20）

> 索引：`foreign_trade_ecosystem_catalog.json` → `github_curated` / `benchmark_sources`  
> API：`GET /api/v1/foreign-trade/ecosystem/catalog?section=benchmarks`

### 适配结论（优丁 SaaS 边界）

| # | 项目 |  verdict | 优先级 | 落地方式 |
|---|------|----------|--------|----------|
| 1 | [AI_Find_Customer](https://github.com/xiongQvQ/AI_Find_Customer) | **✅ 最合适** | **P1** | 已接线 Sidecar；运维部署上游 + `8092` 适配器 |
| 2 | OpenClaw（浏览器自动化） | ⚠️  playbook | P2 | 对照 `headless_probe_sidecar`；不 fork；Maps/LinkedIn 流程抄作业 |
| 3 | [linkedin-scraper](https://github.com/tufayellus/linkedin-scraper) | ⚠️ 受限 | P3 | `restricted` + `tenant_consent`；仅 enrichment，禁止无 evidence 触达 |
| 4 | EmailExtractor（域名递归邮箱） | ✅ 互补 | P2 | AI Hunter 后处理 Sidecar；每条邮箱须 `source_url` |
| 5 | B2B-Lead-Generator（Apify） | ⚠️ 重复 | 暂缓 | 与 #1 同泳道；**AI Hunter 跑通后再二选一** |
| 6 | mymailclaw | ❌ 自动发信 | 不接入群发 | 仅借鉴 **只读 IMAP 询盘收取**（P3）；禁止 SMTP 序列进主仓 |
| 7 | [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) | ⚠️ 社媒泳道 | P2 | `social_restricted` Sidecar；服务矩阵/背调，非 CustomerFinder 默认 |
| 8 | CustomsDataSpider | ⚠️ 情报 | P2 | DeerFlow / `export_feasibility` brief；**不得** `included:true` 无来源落库 |

### 配套栈（第二节）对照

| 工具 | verdict | 说明 |
|------|---------|------|
| MailHog | ✅ dev | `docker compose --profile dev-mail`；SMTP 1025 / UI 8025 |
| email-validator | ✅ 已用 | `outreach_deliverability_service.check_recipient_email` |
| SuiteCRM / Odoo | 📋 字段参考 | 已有 `inquiry + MEDDPICC`；不 fork 整仓 |
| LibreTranslate | ⚠️ P2 | 询盘语言桥 LLM 优先；离线翻译可选自建 |
| WordPress + RankMath | ❌ 不替换 | 租户站走 **Nuxt L-Pro** + 自有 SEO/GEO |
| Openpyxl / Pandas | ✅ 部分 | `trade_document_service` 报价 PI；装柜计算器 playbook |

### 四类自动化技能 → 我们已有能力

| 技能类 | 外部工具 | 我们现状 |
|--------|----------|----------|
| Google 高阶指令 / Maps | AI_Find_Customer, OpenClaw | Sidecar + `CustomerFinder` + human_verify |
| AI 开发信 / 跟进 | smart-trade-ai, mymailclaw | `outreach_deliverability` 草稿 + Day3/7 建议节奏 |
| CRM / 报价 | SuiteCRM, open-erp | `inquiry` + MEDDPICC + Proforma PDF 部分 |
| 独立站 SEO | RankMath | `seo_optimization` + 租户 Nuxt + AEO 审计 |

### 合规（与 `01-no-fake-delivery` 一致）

1. 采集联系方式仅用于正常 B2B 开发；欧盟 GDPR 须可说明 lawful basis；**禁止**垃圾邮件轰炸。  
2. Google / LinkedIn 限速 + 代理；Sidecar 失败须 503/`skipped`，不得随机邮箱冒充找到。  
3. 客户数据优先本地 Sidecar + 租户库；LLM Key 不上传未授权第三方。

### 建议执行顺序

1. **P1** 部署 AI_Find_Customer → `scripts/verify-ai-find-customer-sidecar.py --smoke-find`  
2. **P1** Admin 找客页走通：`/sales/customer-finder` → 证据链 + 人工复核  
3. **P2** EmailExtractor Sidecar 接 enrichment 后处理  
4. **P2** MediaCrawler 登记 `social_restricted`（矩阵/背调 Lane）  
5. **P3** linkedin-scraper / IMAP 只读收取 — 租户书面授权后再开
