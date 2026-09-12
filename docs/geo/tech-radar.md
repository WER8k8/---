# GEO 技术雷达 · 正式口径（RADAR-06）

**状态**：已上线（2026-06-02） · 取代旧 MVP「仅计划」描述

## 流水线

```text
公开源抓取 → Hermes 只读验证 → ECC 专家只读评审 → 高影响/否决 → 飞书通知
     ↓
Markdown 日报写入 docs/geo/tech-radar/YYYY-MM-DD.md
```

| 阶段 | 模块 | 说明 |
|------|------|------|
| 抓取 | `tech_radar_fetch.py` | RSS / GitHub Releases / Schema.org / **Tavily**（可选） |
| 验证 | `tech_validation.py` | HTTP 可达、影响分级 |
| 专家 | `ecc_expert_panel.py` | 只读 LLM 评审（**lane=ops**, scenario=`hermes_tech_radar`→`logic`） |
| 编排 | `ops_autopilot.run_tech_radar_cycle` | mode=`fetch_validate_ecc_expert` |
| 调度 | Celery `geo_tech_radar_daily` | 每日 08:00 |
| 导出 | `tech_radar_markdown_export.py` | 自动写入 `docs/geo/tech-radar/` |
| 人工 | `/hermes/ops/instruct` | `rerun_tech_radar` · `export_tech_radar_md` |

## 数据源

| 源 | 类型 | 需密钥 |
|----|------|--------|
| Vue Blog Atom | RSS | 否 |
| web.dev Atom | RSS | 否 |
| FastAPI GitHub Releases | API | 否 |
| Schema.org releases | HTML 标题 | 否 |
| Tavily 外网搜索 | REST | `TAVILY_API_KEY` |

未配置 Tavily 时流水线仍运行，响应 `fetch_errors` 含 `tavily:not_configured`。

## API

| 方法 | 路径 | 角色 |
|------|------|------|
| POST | `/hermes/ops/run` | 超管 · 含雷达一轮 |
| POST | `/hermes/ops/instruct` body `{command:"rerun_tech_radar"}` | 超管 |
| GET | `/hermes/ops/tech-radar/reports` | 超管 · 最近 Markdown 日报 |
| GET | `/api/v1/super-admin/geo-engine/tech-radar/run` | 超管 · 触发 Celery 同源 pipeline |

**不再返回** `mode: mvp_plan_only`。手动触发与 Celery 均走 `fetch_validate_ecc_expert`。

## 硬规则（维护宪法）

1. 仅公开源；禁止自动升级生产依赖  
2. Hermes 不执行热更新 / 删库 / 外发邮件  
3. 高影响项仅通知人工，由 ECC 机库或运维指令跟进  
4. 报告落盘供审计，不对外租户展示 DeerFlow/Hermes 商标

## 验收

- Celery 或 `POST /hermes/ops/instruct` 后 Redis `geo:tech_radar:YYYYMMDD` 为 `completed`  
- `docs/geo/tech-radar/` 生成当日 `.md`  
- 司令部 / ECC 机库可见 `high_impact_count` 与候选列表  

## 相关

- 旧 MVP 说明（已归档）：`docs/geo/tech-radar-MVP.md`  
- 运维 cron：`docs/运维-cron.md`  
- Tavily / SEO 矩阵：`deploy/docs/SEO-MATRIX-DATABASE-DEPLOY.md`
