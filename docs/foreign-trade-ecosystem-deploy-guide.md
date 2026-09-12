# 外贸生态部署指南（产品 + 运维）

> 机器可读目录：`backend/app/data/foreign_trade_ecosystem_catalog.json`  
> 运维清单：`deploy/docs/FOREIGN-TRADE-ECOSYSTEM-DEPLOY.md`

## 我们 vs GitHub「外贸」生态

| 维度 | Eva/迈富时类 | GitHub 常见开源 | **本仓库（随源码部署）** |
|------|--------------|---------------|-------------------------|
| 开发信质量 | 强 | b2b-sdr 模板 | ✅ deliverability + 时区 + 跟进 |
| 找客数据 | 实名库 | AI_Find_Customer | ✅ 画像 + **human_verify** |
| 独立站 | 模板 | cf_b2b / web_b2b | ✅ site-editor + gap 向导 |
| 研究 | 7×24 | awesome-FT | ✅ DeerFlow + ResearchBrief |
| UTM/CRM | 强 | nana-crm | ⚠️ P0 gap GW-P-TR-01 |
| 真 SMTP 群发 | 有 | UZonMail | ❌ 故意不做（合规） |

## 报关合规（9710 / 9810）

- **9710**：B2B 直接出口，三单一致，单一窗口传输  
- **9810**：先出口海外仓再零售  
- 官方 PDF：[上合示范区手册](http://kjm.eportyun.com/doc/5.pdf)  
- 实操文：[9710 指引](https://www.key.date/325.html)

## API 一览

| 路径 | 说明 |
|------|------|
| `GET /api/v1/foreign-trade/ecosystem/overview` | 统计概览 |
| `GET /api/v1/foreign-trade/ecosystem/catalog` | 全量或分片 |
| `GET /api/v1/foreign-trade/ecosystem/skills` | 技能+状态 |
| `GET /api/v1/foreign-trade/ecosystem/gaps` | P0 短板+推荐集成 |
| `GET /api/v1/foreign-trade/ecosystem/deploy-manifest` | 运维清单（平台 admin） |
| `GET /api/v1/super-agent/skills?include_gaps=true` | Super Agent 合并视图 |

## 推荐外部集成（不 fork，MCP/运维自建）

完整 **取长补短** 矩阵见 [`foreign-trade-benchmark-sources.md`](./foreign-trade-benchmark-sources.md) · API `GET /foreign-trade/ecosystem/benchmarks`

1. **xiongQvQ/AI_Find_Customer** — enrichment 侧car，P1（人工批准发信，不对齐自动 SMTP）
2. **chefroger/smart-trade-ai** — 6 层背调 + PI/合同 playbook → accio_skill P1
3. **EricHong123/Eric_Frank** — 全链路 Skill 清单 → Hermes workflow 对照
4. **qingchuh/sale_agent_factory** — 官网 ICP onboarding → site-editor
5. **QuantumCanvaX/open-erp** / **nana-crm** — 字段/管道参考（不 fork）
6. **nav8.top** + **tshwangq/awesome-foreign-trade** — 研究员外链库
7. **n8n + autonomous-sales-swarm** — 已有 examples/n8n

## 扩展知识库（不同步进镜像，可选）

桌面库：`Desktop/出海计/docs/外贸知识库/` — 可用 `scripts/sync-foreign-trade-kb-to-repo.ps1` 同步摘要到本 `docs/`（运维文档不强制）。
