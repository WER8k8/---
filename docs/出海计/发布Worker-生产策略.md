# 发布 Worker · 生产策略（T5）

> **目标**：矩阵发布任务可预期消费，失败可重试，与副驾「经营快照」中的 `publish_failures` 对齐。

## 1. 队列模型

- 表：`publish_tasks`（`pending` → `processing` → `success` / `failed`）
- 消费：`app.workers.publish_worker.process_pending_tasks`
- 运维 API（需超管）：
  - `GET /api/v1/ops/publish-worker/status` — 队列深度
  - `POST /api/v1/ops/publish-worker/run?limit=10` — 手动/ cron 消费
  - `POST /api/v1/ops/publish-worker/retry-failed?limit=50` — 失败重入队

## 2. 推荐 cron（Linux）

```cron
# 每 5 分钟消费一批 pending（按流量调 limit）
*/5 * * * * curl -sS -X POST "https://<API_HOST>/api/v1/ops/publish-worker/run?limit=20" \
  -H "Authorization: Bearer <OPS_CRON_TOKEN>"

# 每小时重试可恢复失败
15 * * * * curl -sS -X POST "https://<API_HOST>/api/v1/ops/publish-worker/retry-failed?limit=50" \
  -H "Authorization: Bearer <OPS_CRON_TOKEN>"
```

## 3. Windows / 任务计划程序

使用 `scripts/ops-publish-worker-cron.ps1`（见仓库）：

```powershell
$env:OPS_CRON_TOKEN = "<超管 JWT 或专用服务账号>"
powershell -ExecutionPolicy Bypass -File scripts/ops-publish-worker-cron.ps1 -BaseUrl https://api.example.com
```

## 4. 环境变量

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | Worker 与 API 共用库 |
| `OPS_CRON_TOKEN` | 调用 ops 接口的 Bearer（勿提交 Git） |

## 5. 告警与副驾

- 失败数：`GET /api/v1/ubrain/ops-snapshot` → `publish_failures`
- 人工：副驾「经营快照」hints 会提示失败条数
- **不自动外发**：矩阵计划仍须人审（Accio `matrix_publish`）

## 6. 验收

1. 创建 1 条 `pending` 任务 → `run` → 状态变为 `success` 或可见 `failed`
2. `retry-failed` 后 pending 增加
3. 副驾经营快照中 `publish_failures` 与库内 `failed` 计数一致
