# 超管 L0 司令部 · 六屏说明（ARCH-02）

> **路径**：`/admin/system/command-center`  
> **API**：`GET /api/v1/hermes/ops/command-center`  
> **受众**：`super_admin` / `admin`（ops 门控）

## 六屏区块

| # | 区块 | 数据来源 | 租户可见 |
|---|------|----------|----------|
| 1 | **作战态势** | 巡站 overall + ops 快照 | 否 |
| 2 | **Hermes 巡站** | `site_patrol` probes | 否 |
| 3 | **DeerFlow 队列 + SLO** | `deerflow_jobs` + SLO 聚合 | 否 |
| 4 | **SEO 雷达** | 收录 / Rank Guard / rank_scheduler | 否 |
| 5 | **AI 机库 + ECC** | ai-config + `/admin/system/ecc-hangar` | 否 |
| 6 | **飞轮 / 集成 / 发布** | commercial-os + n8n/Mem0 + 统一发布历史 | 否 |

## 关联子页

| 路径 | 说明 |
|------|------|
| `/admin/system/ecc-hangar` | ECC 专家编制与评审 |
| `/admin/system/deerflow-monitor` | DeerFlow 分页队列 + 7 天 SLO |
| `/admin/system/publish-history` | SEO 图文 + 视频统一发布历史 |

## L0 vs L1

- **L0（本页）**：7×24 运维、队列、收录、Worker、集成 — Hermes 内核  
- **L1（租户）**：`/client/copilot` 仅触发任务、看进度 — 不暴露 Hermes ops 路由

## 一键动作

司令部 actions 区：Hermes 运维循环 · DeerFlow 研究 · Rank Guard · 收录复检 · ECC 机库 · 队列明细 · 发布历史
