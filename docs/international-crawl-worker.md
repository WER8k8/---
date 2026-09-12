# 国际询盘爬虫 Worker（OPS-02）

后端**只接收** Webhook，不内置定时爬虫。

## 配置

```env
CRAWL_WEBHOOK_SECRET=<随机长密钥>
```

## 外置 Worker 职责

1. 读租户 `crawl_interval`（分钟）
2. 抓取目标站点 / RSS
3. `POST /api/v1/international/webhook`，签名与 `CRAWL_WEBHOOK_SECRET` 一致

## 验收

- `GET /api/v1/international/stats` 有新增记录
- preflight / 日志无 401/500 验签错误
