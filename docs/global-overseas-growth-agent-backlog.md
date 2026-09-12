# 出海增长智能体 — 全量细节头脑风暴与任务登记

> **签发**：研究员 × PM-07 联合  
> **日期**：2026-06-02  
> **性质**：**出海比国内网站推广更难、细节更多** — 本文作为海外获客/内容/投放/销售的全量缺口清单与分配依据  
> **关联**：[`outreach-deliverability-brief.md`](./outreach-deliverability-brief.md) · [`pm-swarm-parallel-charter.md`](./pm-swarm-parallel-charter.md) · 任务 JSON：[`global-overseas-growth-task-register.json`](./global-overseas-growth-task-register.json)

---

## 0. 为什么比国内难

| 维度 | 国内网站推广 | 出海 B2B（建材/工厂） |
|------|-------------|----------------------|
| 语言与文化 | 单一中文语境 | 多语言 + 宗教/ imagery / 商务礼仪 |
| 时区 | 基本同一时区 | 发送/互动/客服需按买家本地时间 |
| 信任 | 电话/微信/实地 | 认证、检测视频、独立域、邮件可达性 |
| 线索质量 | 表单/电话即可 | 要规格、目的港、MOQ、Incoterms |
| 渠道 | 百度/抖音/微信生态 | Google/LinkedIn/Email/WhatsApp/YouTube/矩阵 |
| 合规 | 广告法、ICP | CAN-SPAM、GDPR、出口/认证表述、域名预热 |
| 归因 | 简单 UTM | 跨域、跨 IM、线下展会、多 touch |
| 内容 | 促销/品牌 | 规格书、项目案例、E-E-A-T、AI 引文（AEO） |

**结论**：不是「多几个 AI 名字」，而是 **每个渠道背后一堆运营常识要进系统（字段、规则、队列、清单）**。

---

## 1. 编排原则（蜂群）

| Lane | 范围 | Out-of-Scope |
|------|------|--------------|
| **GW-S** 社媒内容 | TikTok/IG/X/Reddit/YouTube/轮播 | 国内百家号运营细节 |
| **GW-G** 增长与 SEO | 增长实验、SEO、AEO、内容日历 | 付费 API 真投放（归 GW-P） |
| **GW-P** 付费媒体 | 审计、创意、PPC、归因 | 销售 CRM 字段（归 GW-L） |
| **GW-L** 销售 outbound | 开发信、ABM、Discovery、Pipeline | 社媒发帖 Worker |
| **GW-R** 研究员 | 词库、时区、spam、国标、竞品 | 写 Vue 页 |
| **GW-PM** 产品 | 验收 ID、角色库 JSON、前台入口 | 替 Lane 实现 |

**永久**：每条任务必须有 **In-Scope / Out-of-Scope / 验收证据**；`cert:gate` 不回归。

---

## 2. 社媒 & 视频（GW-S）

### 2.1 TikTok 策略师 · 病毒式内容 / 算法 · 出海短视频

**我们已有**：矩阵发布、抖音 Worker 谈单、视频矩阵 Hermes。  
**没想到的细节（须补）**：

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-S-TT-01 | B2B 钩子=工地/检测/装箱，不是娱乐爆款 | 脚本模板库 `b2b_hook` 分类 |
| GW-S-TT-02 | Bio 链独立域 + UTM `src=tiktok-{country}` | 发布任务强制 UTM |
| GW-S-TT-03 | 评论 RFQ → 询盘/社媒谈单表 | TikTok 评论 webhook 契约 |
| GW-S-TT-04 | 音乐/素材商用版权清单 | 上传前 metadata 校验 |
| GW-S-TT-05 | 完播率 vs 留资率分开报表 | analytics 事件 `tiktok_view` / `lead` |
| GW-S-TT-06 | 账号属地+语言分区（中东 EN/AR） | 租户 `locale_matrix` 配置 |
| GW-S-TT-07 | 前 3 秒字幕必含品类+认证关键词 | 视频出厂 checklist |

**不测**：C 端带货直播话术；国内纯娱乐涨粉。

---

### 2.2 Twitter/X 互动官 · 实时互动 / 思想领袖

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-S-X-01 | 行业日历发帖（广交会、Big5、当地建材展） | `marketing_calendar` 表 |
| GW-S-X-02 | Thread 结构：规格对比 / 认证清单 / 案例 | 内容模板 `thread_b2b` |
| GW-S-X-03 | 与 LinkedIn 同源不同语气（更短、更数据） | 一源多态变体 |
| GW-S-X-04 | 舆情/质量投诉 @ 应答 playbook | 危机模板 + 升级工单 |
| GW-S-X-05 | 实时互动窗口按欧美工作时间提醒 | 通知规则 |

---

### 2.3 Instagram 策展师 · 视觉叙事 / 社区

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-S-IG-01 | Carousel：规格→认证→应用→CTA 四页结构 | 轮播模板 ID |
| GW-S-IG-02 | 工地图/案例需客户授权与水印 | 素材 `license` 字段 |
| GW-S-IG-03 | Story：样品→检测→装箱→到港信任链 | storyboard 模板 |
| GW-S-IG-04 | DM → WhatsApp 分流（中东） | CTA 按 region 切换 |
| GW-S-IG-05 | 平台安全区（顶底遮挡）自动化裁剪 | 轮播引擎参数 |

---

### 2.4 Reddit 社区运营 · 社区文化 / 真实互动

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-S-RD-01 | subreddit 规则预检（r/Construction 等） | 发帖前规则 checklist |
| GW-S-RD-02 | 90 天答疑再带链接节奏 | Playbook 文档 + CRM 标签 |
| GW-S-RD-03 | 官方号 vs 员工个人号策略 | 账号角色 `reddit_official` / `personal` |
| GW-S-RD-04 | AMA 式出口认证 FAQ 长帖 | 内容类型 `reddit_ama` |
| GW-S-RD-05 | 禁止硬广话术扫描 | 同 spam 词库扩展 |

---

### 2.5 应用商店优化师 · ASO · App 出海

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-S-ASO-01 | 优先级：Web/独立域 > App（除非 App 成主入口） | PM 路线声明 |
| GW-S-ASO-02 | 关键词：HS、insulation supplier、MOQ calculator | ASO 词表（若上架） |
| GW-S-ASO-03 | 截图展示询盘/规格工具非纯 UI | 商店素材规范 |
| GW-S-ASO-04 | 出海计 App 与独立域 deep link 一致 | Universal link |

**Out**：无 App 主战略时不占 P0 研发。

---

### 2.6 视频优化专家 · YouTube / 留存 / 跨平台

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-S-YT-01 | 前 30 秒：规格+认证+MOQ | 脚本门禁 |
| GW-S-YT-02 | 章节 Specs/Certs/Shipping/Contact | 上传 metadata |
| GW-S-YT-03 | 母片切 9:16 / 1:1 / 16:9 | media_factory 导出预设 |
| GW-S-YT-04 | 多语言字幕 + 描述区独立域链接 | 发布包字段 |
| GW-S-YT-05 | 实拍 vs 渲染标注 | 视频 `source_type` |
| GW-S-YT-06 | 留存曲线与询盘相关性 | YouTube Analytics 导入（P2） |

---

## 3. 增长 / 内容 / SEO / AEO（GW-G）

### 3.1 增长黑客 · 获客 / 病毒循环 / 实验

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-G-GH-01 | 病毒循环=经销商转介绍非 C 端红包 | 推荐计划 B2B 字段 |
| GW-G-GH-02 | 独立域→开发信→询盘漏斗 A/B | 实验框架 + 事件 |
| GW-G-GH-03 | 「样品申请」低门槛转化 | 表单类型 `sample_request` |
| GW-G-GH-04 | 垃圾询盘/同行爬虫过滤 | inquiry_score 规则 |
| GW-G-GH-05 | 每实验必绑 north_star metric（有效 SQL） | 实验登记模板 |

---

### 3.2 内容创作者 · 多平台 / 编辑日历

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-G-CC-01 | 日历=展会季+目的国旺季+汇率窗口 | calendar 数据源 |
| GW-G-CC-02 | 1 长文→3 短帖→1 邮件→1 开发信 | content_master 复用链 |
| GW-G-CC-03 | 品牌/工厂/产品三线内容人格 | `content_line` 标签 |
| GW-G-CC-04 | 人审：数字/认证/MOQ 与 PI 一致 | 发布前 checklist |
| GW-G-CC-05 | 禁促销腔（同步 spam 词库） | 与 OUTREACH 共享 |

---

### 3.3 社交媒体策略师 · 跨平台整合

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-G-SM-01 | 平台优先级矩阵（建材 B2B） | 默认：LinkedIn>Email>YouTube>IG>TikTok>Reddit |
| GW-G-SM-02 | 同一 campaign ID 跨平台 | `campaign_id` 贯穿 |
| GW-G-SM-03 | 国内矩阵 vs 海外独立域分轨 | region=cn/global |
| GW-G-SM-04 | 账号健康度（登录/Cookie/限流） | platform_accounts 告警 |

---

### 3.4 SEO 专家 · 技术 SEO / Google

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-G-SEO-01 | hreflang + 独立域 CWV | 站点体检 job |
| GW-G-SEO-02 | 程序化 SEO 薄内容风险门禁 | 城市页数量/字数阈值 |
| GW-G-SEO-03 | Product/FAQ/Organization Schema | 与 GEO 统一 |
| GW-G-SEO-04 | 百度 vs Google 分轨策略文档 | 双轨 runbook |
| GW-G-SEO-05 | 长尾 HS + material + supplier 落地页 | 模板+人审 |

---

### 3.5 轮播图增长引擎 · 轮播 / 自动投放

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-G-CG-01 | 第 1 张问题 / 最后 CTA+域名 | 模板约束 |
| GW-G-CG-02 | IG/LinkedIn 安全区参数 | 导出规格 |
| GW-G-CG-03 | A/B：认证标 vs 应用场景 | 实验标签 |
| GW-G-CG-04 | 与 paid_ads_creative 素材同源 | 创意 ID 关联 |

---

### 3.6 LinkedIn 内容创作 · B2B 职场获客

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-G-LI-01 | Personal Profile > Company Page | Playbook |
| GW-G-LI-02 | Document post / PDF 规格摘要 | 导出 PDF 流水线 |
| GW-G-LI-03 | InMail 与开发信话术分轨 | 模板库分离 |
| GW-G-LI-04 | Sales Navigator 线索→CRM 字段 | 导入映射 |
| GW-G-LI-05 | 连接请求备注字数与禁忌 | 校验规则 |

---

### 3.7 图书联合作者 → 白皮书 / 出口指南

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-G-BK-01 | 行业白皮书替代实体书 | PDF lead magnet |
| GW-G-BK-02 | 章=目的国法规+案例+清单 | 目录模板 |
| GW-G-BK-03 | 与官网/GEO/AEO 互链 | 统一 canonical |

---

### 3.8 AI 引文策略师 · AEO/GEO · AI 平台可见性

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-G-AEO-01 | FAQ 与旺财/UBrain 事实一致审计 | 事实对齐 job |
| GW-G-AEO-02 | 品牌词在 ChatGPT/Perplexity 可见性抽检 | 季度审计表 |
| GW-G-AEO-03 | E-E-A-T 作者与 eeat.vue 数据同源 | 作者实体 |
| GW-G-AEO-04 | 结构化数据 + Citation 友好段落 | content 模板 |
| GW-G-AEO-05 | 竞品 AI 引文对比 | 研究员手工+记录 |

---

## 4. 付费媒体部（GW-P）

### 4.1 付费媒体审计师

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-P-AU-01 | CPL=有效询盘（规格+电话）非裸表单 | 转化定义文档 |
| GW-P-AU-02 | 品牌/竞品/品类词预算比例 | 审计 checklist |
| GW-P-AU-03 | 国内 vs 海外账户隔离 | 账户标签 |
| GW-P-AU-04 | 创意-落地页-承诺一致性 | 审计截图 |

---

### 4.2 广告创意策略师

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-P-CR-01 | 创意=认证+场景+Get spec sheet | paid_ads 模板扩展 |
| GW-P-CR-02 | 中东/宗教 imagery 扫描 | culture-adapt 规则 |
| GW-P-CR-03 | A/B 文案版本与询盘质量挂钩 | 实验记录 |
| GW-P-CR-04 | 落地页 MOQ/交期与广告一致 | 字段绑定 |

---

### 4.3 社交广告策略师 · Meta/TikTok/LinkedIn

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-P-SO-01 | Lead Form 字段=规格+目的港+数量 | 表单 schema |
| GW-P-SO-02 | LinkedIn 预填 vs 自定义问题 | B2B 筛选 |
| GW-P-SO-03 | 再营销 7/30/90 天分层 | audience 定义 |
| GW-P-SO-04 | CAPI / Pixel 与询盘 ID 回写 | P2 API |

---

### 4.4 PPC 竞价策略师 · Google/百度

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-P-PC-01 | 长尾 HS + material + supplier + country | 关键词包 |
| GW-P-PC-02 | 否定词 jobs/DIY/retail | 共享否词表 |
| GW-P-PC-03 | 一广告组一意图一落地页 | LP 路由规则 |
| GW-P-PC-04 | 国内百度与 Google 分账户 | 双轨 |

---

### 4.5 程序化广告采买 · DSP/RTB

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-P-DSP-01 | B2B 工厂默认 P2，品牌展会有数据再开 | 优先级声明 |
| GW-P-DSP-02 | 若做：品牌安全+行业 whitelist | 配置模板 |

---

### 4.6 搜索词分析师

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-P-SQ-01 | 搜索词→开发信关键词→SEO 选题三角 | 周报流水线 |
| GW-P-SQ-02 | 否词同步到 SEO（避免内耗） | 词库 sync |
| GW-P-SQ-03 | 高意图词单独 landing | 路由 |

---

### 4.7 追踪与归因专家

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-P-TR-01 | UTM 全链路：矩阵→独立域→询盘→CRM | **P0** |
| GW-P-TR-02 | GCLID + inquiry_id 回写 | CRM 字段 |
| GW-P-TR-03 | 展会线下线索 UTM | 活动码 |
| GW-P-TR-04 | WhatsApp 点击 vs 表单双转化 | 事件名 |
| GW-P-TR-05 | 邮件打开/回复 webhook | OUTREACH-D4 |
| GW-P-TR-06 | 多 touch 归因模型（末次/线性） | P2 分析 |

---

## 5. 销售部（GW-L）

### 5.1 客户拓展 / Outbound / ABM

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-L-OB-01 | 时区发送窗口 | ✅ `outreach_deliverability_service` |
| GW-L-OB-02 | 垃圾箱/质量分 | ✅ 同上 |
| GW-L-OB-03 | 同公司多联系人错开发送 | `company_id` 节流 |
| GW-L-OB-04 | 首封无附件，二封 spec PDF | 序列规则 |
| GW-L-OB-05 | ABM 50 家深度定制再规模化 | 标签 `abm_tier` |
| GW-L-OB-06 | SPF/DKIM/DMARC/预热清单 | ✅ checklist |
| GW-L-OB-07 | D+3/D+7 跟进节奏 | ✅ follow_up_schedule |
| GW-L-OB-08 | LinkedIn/InMail 与邮件不同文 | 模板分轨 |

---

### 5.2 Discovery 教练 / 赢单策略师 / 销售教练

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-L-DC-01 | MEDDPICC 字段进询盘 | inquiry 扩展字段 |
| GW-L-DC-02 | 建材必问：防火/标准/项目/incoterms | discovery 脚本 |
| GW-L-DC-03 | 压价触发 cost_floor 提示 | UI 与 negotiation 联动 |
| GW-L-DC-04 | 丢单原因编码 | 关闭原因 enum |
| GW-L-DC-05 | 销售录音/纪要结构化（P2） | 可选 |

---

### 5.3 售前工程师

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-L-SE-01 | Demo=独立域+样品+检测视频 | 演示包 checklist |
| GW-L-SE-02 | 技术 FAQ 与 UBrain 知识库同源 | knowledge 单一源 |
| GW-L-SE-03 | RFQ 附件 OCR 进询盘 | P2 文档解析 |

---

### 5.4 Pipeline 分析师

| ID | 细节 | 产品化 |
|----|------|--------|
| GW-L-PL-01 | 阶段：MQL→SQL→报价→PI→定金 | pipeline 定义 |
| GW-L-PL-02 | 预测含交期/认证风险 | 风险字段 |
| GW-L-PL-03 | 开发信→打开→回复→询盘漏斗 | 依赖 GW-P-TR-05 |
| GW-L-PL-04 | 周报自动汇总 | weekly_lead_report 扩展 |

---

## 6. B2B 外贸「AI 专家角色库」（产品包装 · GW-PM）

对标 Eva/Nora/Max，**6–8 个角色**映射现有能力（非 220 通用 agent）：

| 角色 ID | 对外名 | 干什么 | 后端能力 | 必显细节 |
|---------|--------|--------|----------|----------|
| `expert_eva` | 找客专员 | 画像/候选客户 | find_buyers | 待核实免责声明 |
| `expert_letter` | 开发信专员 | 草稿+质量分+发送窗 | outreach_letter_pack | 不进垃圾箱清单 |
| `expert_negotiate` | 谈单顾问 | RFQ/砍价 | negotiation_draft | cost_floor |
| `expert_site` | 建站助手 | 独立域 | auto_shopify | B2B 模板 |
| `expert_matrix` | 矩阵运营 | 多平台发文 | matrix_publish | 账号登录提醒 |
| `expert_ads` | 广告创意 | 素材 | paid_ads_creative | 人审导入 |
| `expert_research` | 市场参谋 | 蓝海/海关参考 | deerflow/trade_intel | 非实时报关 |
| `expert_crm` | 客户管家 | 询盘优先级 | inquiry_score | MEDDPICC P1 |

**交付物**：`backend/app/data/b2b_trade_experts.json` + Admin「AI 外贸团队」页（P1）。

---

## 7. 优先级总表

### P0 · 3 个月内（卖货直接相关）

| ID | 任务 | Lane |
|----|------|------|
| GW-P-TR-01 | UTM 全链路 | GW-P + 后端 |
| GW-L-OB-01~07 | 开发信可达性（部分✅） | GW-L |
| GW-G-CC-02 | 内容 1→多态复用链 | GW-G + content_master |
| GW-G-CC-04 | 发布人审清单 | GW-G |
| GW-L-DC-01 | 询盘 MEDDPICC 核心字段 | GW-L |
| GW-G-AEO-01 | 旺财 vs 官网事实审计 | GW-G |
| GW-G-SM-04 | 平台账号健康告警 | GW-S |
| GW-PM-01 | b2b_trade_experts 角色库 JSON | GW-PM | ✅ 已入库 |

### P1 · 增强专业感

| 范围 | 代表 ID |
|------|---------|
| YouTube/视频 | GW-S-YT-01~05 |
| LinkedIn | GW-G-LI-01~04 |
| 付费创意+落地页 | GW-P-CR-* , GW-P-SO-01 |
| Reddit/TikTok Playbook | GW-S-RD-* , GW-S-TT-* |
| Pipeline/丢单 | GW-L-PL-* , GW-L-DC-04 |
| 区域合规扫描 | GW-P-CR-02 , culture-adapt |

### P2 · 有预算/API 再做

| 范围 | 代表 |
|------|------|
| Google/Meta Ads API 真投放 | GW-P-SO-04 |
| 联系人数据库 | RocketReach 等 |
| DSP 程序化 | GW-P-DSP-* |
| ASO 主战略 | GW-S-ASO-* |
| 邮件打开追踪 | GW-P-TR-05 |
| RFQ OCR | GW-L-SE-03 |

---

## 8. 研究员 × PM 周节奏

### 研究员（每周）

1. **1 国 × 1 平台** 踩坑清单（礼仪、发送时间、禁忌词、案例链接）。  
2. 维护：`spam 词库`、`HS 长尾词`、`竞品广告/开发信截图`。  
3. 更新：`global-overseas-growth-task-register.json` 中 `research_notes`。  
4. 对外表述审核：**不承诺送达率/不承诺实名线索库**。

### PM（每周）

1. 从 P0/P1 拣 **≥2 条** 开验收 ID（格式 `GW-*`）。  
2. 写清：**进哪个 API / 哪张表 / 哪个 Vue 页**。  
3. 冲突仲裁：与 Sprint-R1 Lane A–H 抢文件时 PM 裁定。  
4. 同步：[`ecc-delivery-tracker.md`](./ecc-delivery-tracker.md) 增「出海 GW」小节。

### 开发

- 只实现 **本登记册中已 ID 化** 的条目；禁止「顺手」扩 scope。  
- 每条 PR 首段：任务 ID + 为何 + 验收脚本 + Out-of-Scope。

---

## 9. 与国内推广协同（勿混）

| 只做国内 | 只做出海 | 共用 |
|----------|----------|------|
| 百家号/抖音国内话术 | 开发信/LinkedIn/Google | content_master 母版 |
| 百度 SEO | hreflang 独立域 | 租户 RBAC |
| 企微/抖音私信 webhook | WhatsApp/Email 分轨 | 询盘统一表 |
| 国内广告法表述 | CAN-SPAM/GDPR 表述 | 素材库 |

---

## 10. 索引与变更

| 文件 | 用途 |
|------|------|
| 本文 | 全量细节与智能体头脑风暴 |
| [`outreach-deliverability-brief.md`](./outreach-deliverability-brief.md) | 开发信 P0 专项 |
| [`global-overseas-growth-task-register.json`](./global-overseas-growth-task-register.json) | 可机读任务登记 |
| `backend/app/services/ubrain/outreach_deliverability_service.py` | 开发信门禁实现 |

**变更**：新增 GW 任务只改 JSON + 本文 §7 优先级；周一 PM-07 刷新 pct。

---

*研究员 × PM-07 · 出海细节多于国内 — 先 P0 六条（UTM、开发信、内容复用、MEDDPICC、事实审计、角色库）再扩社媒爆款。*
