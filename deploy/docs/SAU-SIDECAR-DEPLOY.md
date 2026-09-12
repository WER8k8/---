# SAU Sidecar 部署

## 角色

优丁 API（控制面）通过 `SAU_SIDECAR_URL` 调用本 Sidecar，在 Worker 机执行 `social-auto-upload` CLI。

## 快速启动（开发）

```powershell
# 终端 1 — Sidecar
python scripts/sau-sidecar-adapter.py --port 9910

# backend/.env
SAU_SIDECAR_URL=http://127.0.0.1:9910
SAU_ENABLED=true
```

## Docker

```bash
docker compose -f deploy/sidecar/sau-compose.yml up -d
```

生产须在镜像或宿主机 volume 中安装 `sau` CLI + Playwright Chromium，并挂载 `SAU_HOME` Cookie 目录。

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/youding/health` | 健康探测 |
| POST | `/api/youding/sau/check` | Cookie 检查 |
| POST | `/api/youding/sau/publish` | 提交发布任务 → `job_id` |
| GET | `/api/youding/sau/jobs/{id}` | 轮询结果 |

## 诚实门禁

- 即时发布：`platform_post_url` 必填才算 `success`
- 定时发布：可返回 `pending` + `publish_state=scheduled`，禁止假成功

## 验证

```powershell
python scripts/verify-sau-sidecar.py
```

契约：`.project/sau-youding-integration.json`
