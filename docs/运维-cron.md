# 运维定时任务（收尾）

## 脚本（服务器 cron）

```bash
cd backend
export JWT_SECRET_KEY="your-production-secret-32chars-min"
python scripts/run_ops_jobs.py --job all
```

可选参数：

| 参数 | 说明 |
|------|------|
| `--job tenant-expiry` | 到期租户冻结 |
| `--job ai-costs` | AI 用量写入成本台账 |
| `--job publish-worker` | 消费 pending 发布任务 |
| `--dry-run` | 只打印不写入 |
| `--publish-limit 50` | 单次最多处理发布任务数 |

## HTTP（超管 token）

| 接口 | 说明 |
|------|------|
| `POST /api/v1/ops/jobs/run-all` | 一键：冻结 + 成本 + 发布队列 |
| `POST /api/v1/ops/publish-worker/run?limit=20` | 仅发布队列 |
| `POST /api/v1/ops/tenants/enforce-expiry` | 仅到期冻结 |
| `POST /api/v1/ops/finance/sync-ai-costs` | 仅 AI 成本 |

| `POST /api/v1/ops/nvidia-customer-probe/run` | 英伟达客户可用模型探测 |
| `GET /api/v1/ops/nvidia-customer-probe/status` | 探测调度状态 |

管理端：**系统 → 运维批处理**（`/admin/system/ops-wrap`）

## 英伟达免费通道定时探测（生产）

**默认已自动开启**：`ENVIRONMENT=production` 时后端进程内调度器随部署启动，每日 **1:00 / 12:00 / 20:00（北京时间）** 探测；部署后约 **20 秒** 会额外跑一次首探。只需配置 `AI_NVIDIA_API_KEY`，**不必**再记 `NVIDIA_CUSTOMER_PROBE_SCHEDULER_ENABLED=1`。

可选覆盖：

```bash
# 改时段（默认 1:00,12:00,20:00）
NVIDIA_CUSTOMER_PROBE_SLOTS=1:00,12:00,20:00
NVIDIA_CUSTOMER_PROBE_TZ=Asia/Shanghai
# 显式关闭（极少用）
NVIDIA_CUSTOMER_PROBE_SCHEDULER_ENABLED=false
```

无进程内调度时，可用 crontab 调用 CLI / HTTP：

```cron
0 1,12,20 * * * cd /app/backend && .venv/bin/python scripts/run_ops_jobs.py --job nvidia-probe >> /var/log/uj-nvidia-probe.log 2>&1
```

## Celery（OPS-04 · SEO + GEO 定时）

需 **Redis** + 两个进程（或 K8s 两个 Deployment）：

```bash
cd backend
export PYTHONPATH=$(pwd)
celery -A app.tasks.celery_app worker -l info
celery -A app.tasks.celery_app beat -l info
```

本地说明：`scripts/start-celery-local.ps1`

Beat 已含：`check-keyword-rankings`、`run-periodic-site-audit`、`geo_tech_radar_daily`、`geo_rank_guard_check`、`geo_competitor_monitor`、`deerflow_scheduled_daily`、`deerflow_run_pending`（3min）、`seo-inclusion-recheck-daily`（05:30）、`flywheel_feedback_sync_daily`（06:00）、`trade_intel_refresh_weekly`（周一 03:30）。

## 出海参谋 · UN Comtrade 海关数据

- **数据源**：UN Comtrade 公开 API（中国出口 × HS 章别 × 目的国）
- **进程内调度**：生产环境默认开启，每周一 03:30（`TRADE_INTEL_SCHEDULER_ENABLED`）
- **手动 / cron**：`POST /api/v1/ops/trade-intel/refresh` 或 `python scripts/run_ops_jobs.py --job trade-intel-refresh`
- **可选 Key**：`UN_COMTRADE_SUBSCRIPTION_KEY`（未配置则用 public preview 端点）
- **旺财 / 出海参谋**：刷新后自动更新 `trade_intel_customs_public.json`，旺财 Trade Q&A 即时生效

## Hermes / DeerFlow / SEO 定时一览（OPS-05）

| 时间 | 任务 | 说明 |
|------|------|------|
| 每 15min | Hermes 巡站 scheduler | `site_patrol_scheduler` |
| 每 3min | DeerFlow tenant worker | Celery `deerflow_run_pending` |
| 07:30 | DeerFlow 日批 | `deerflow_scheduled_daily` |
| 08:00 | GEO 技术雷达 | `geo_tech_radar_daily` |
| 每 6h | Rank Guard | `geo_rank_guard_check` |
| 05:30 | 收录日检 | `recheck_inclusion_daily` |
| 06:00 | 飞轮反馈同步 | `flywheel_feedback_sync_daily` |
| 04:00 | SEO 词反哺 hints | `seo_research_hints_sync` |
| 周一 03:30 | 海关 Comtrade 刷新 | `trade_intel_refresh_weekly` |
| 86400s | 关键词排名 | `check_all_keyword_rankings` |

生产验收：`powershell -File scripts/ops-02-verify.ps1`

## 国际爬虫（OPS-02）

外置 Worker 按租户 `crawl_interval` POST 到 `/api/v1/international/webhook`，Header 携带 `CRAWL_WEBHOOK_SECRET`。后端不内置爬虫进程。

## 建议 crontab（示例）

```cron
0 2 * * *  cd /app/backend && python scripts/run_ops_jobs.py --job all >> /var/log/uj-ops.log 2>&1
*/5 * * * * cd /app/backend && python scripts/run_ops_jobs.py --job publish-worker --publish-limit 30
```

## 支付生产验签

```bash
export PAYMENT_STRICT_VERIFY=1
export PAYMENT_WEBHOOK_SECRET=your-shared-secret
```

回调 JSON 需带 `signature` = HMAC-SHA256(`out_trade_no:amount`, secret)。
