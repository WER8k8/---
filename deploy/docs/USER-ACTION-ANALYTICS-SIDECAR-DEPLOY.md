# UserActionAnalyzePlatform 并入优丁系统

> 上游：https://github.com/oeljeklaus-you/UserActionAnalyzePlatform  
> **整项目落在 `deploy/vendor/`，不进入 `backend/`**；主站通过网关调 Spark + 读 MySQL。

## 合并架构

```
deploy/vendor/UserActionAnalyzePlatform/   ← git submodule / install 脚本克隆
        ↓ mvn package + java UserVisitAnalyze {task_id}
deploy/examples/user-action-analytics-sidecar/   ← FastAPI 网关（建 task、跑 Spark、读表）
        ↓ HTTP USER_ACTION_ANALYTICS_URL
backend/app/services/analytics/          ← 合规门禁 + 增长工具 API
        ↓
frontend 增长工具 → 查页面转化 / Session
```

## 一键安装上游源码

```powershell
powershell -File scripts/install-user-action-analytics-vendor.ps1
# 或
git submodule update --init deploy/vendor/UserActionAnalyzePlatform
```

## 启动完整栈（MySQL + 网关 + vendor 挂载）

```powershell
powershell -File scripts/install-user-action-analytics-vendor.ps1
docker compose -f deploy/examples/user-action-analytics-stack.compose.yml up -d --build
```

主站 `.env`：

```env
USER_ACTION_ANALYTICS_URL=http://127.0.0.1:8093
USER_ACTION_ANALYTICS_TOKEN=dev-sidecar-token
USER_ACTION_ANALYTICS_MYSQL_DSN=mysql://uaa:uaa_dev@127.0.0.1:3307/user_action_analytics
```

## 模块对照

| module_id | 来源 | 说明 |
|-----------|------|------|
| `session_analysis` | 上游 `UserVisitAnalyze.java` | Spark 写 session_aggr_stat 等 |
| `page_conversion` | Sidecar 聚合 session_detail | 单跳转化率（README 模块 2） |
| `hot_products` | 上游 top10_category 表 | 品类点击 Top10 |
| `ad_traffic_realtime` | README 仅文档 | master 无 Streaming 源码，返回明确未接入 |

## 合规

- 无 vendor / 无 MySQL / Spark 失败 → 不返回假成功
- `USER_ACTION_ANALYTICS_ALLOW_STUB=1` 仅 development
- Session 含用户行为 → `human_review_required`

## 验证

```powershell
curl http://127.0.0.1:8093/v1/vendor-info
curl -X POST http://127.0.0.1:8093/v1/run-module -H "Content-Type: application/json" -d "{\"module_id\":\"page_conversion\",\"params\":{}}"
curl -X POST http://127.0.0.1:8001/api/v1/growth-tools/ai-traffic/conversion-probe -H "Authorization: Bearer <token>" -d "{}"
```
