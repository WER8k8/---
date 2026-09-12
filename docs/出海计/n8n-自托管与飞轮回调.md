# n8n 自托管 · 商业飞轮回调

## 1. 回调端点

| 项 | 值 |
|----|-----|
| URL | `POST {API}/api/v1/ubrain/commercial-os/webhook` |
| 鉴权 | Header `X-N8N-Webhook-Secret` = 环境变量 `N8N_WEBHOOK_SECRET` |
| 示例 Body | `docs/出海计/examples/n8n-deerflow-done.json` |

## 2. 支持 event

| event | 行为 |
|-------|------|
| `deerflow_done` | 沉淀洞察 + 可选自动编排（`UBRAIN_AUTO_PIPELINE`） |
| `manual_pipeline` | 仅编排入队 |
| `feedback` | 等价 `feedback/sync` |

## 3. n8n 工作流建议

1. **HTTP Request** 节点：官方 DeerFlow / 自建研究服务完成后 POST 本 webhook  
2. 将 `tenant_id`、`job_id`、`result` 替换为真实 UUID  
3. `auto_enqueue: true` 时自动创建 Accio 子任务（找客/开发信等）

## 4. 自托管部署要点

- n8n 与 API 同 VPC 或 HTTPS 出网白名单  
- 密钥仅存 n8n Credentials + 后端 `.env`，勿写入 Git  
- 失败重试：n8n 侧 Exponential Backoff；后端幂等靠 `job_id` + 洞察去重  

## 5. 验收

```powershell
# 未配置密钥时（开发）
curl -X POST http://127.0.0.1:8000/api/v1/ubrain/commercial-os/webhook `
  -H "Content-Type: application/json" `
  -d "@docs/出海计/examples/n8n-deerflow-done.json"

# 生产务必设置 N8N_WEBHOOK_SECRET
```

pytest：`tests/unit/test_commercial_os_webhook.py`
