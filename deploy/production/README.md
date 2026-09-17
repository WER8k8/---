# 生产环境配置（仅模板）

> **勿在本机 `上线网站` 目录填写真实生产密钥。**  
> 服务器部署时：在 VPS 上复制 `env.template` 为 `.env`，由运维填写。

## 服务器部署步骤（摘要）

1. 从 git 拉取 **`上线网站`** 指定 tag/分支（主开发仓）
2. 构建前端：`frontend/admin` → `npm ci && npm run build`
3. 后端：Python 3.11+、PostgreSQL、Redis（见 `backend/config/prod/.env.example`）
4. 复制本目录 `env.template` → 服务器 `/opt/youding/.env`（路径自定）
5. 运行迁移：`alembic upgrade head`
6. 预检：`python scripts/run_production_preflight.py`
7. 进程：systemd / Docker（见 `出海计/docs/Sprint-I-上线运维.md`）

## 本地禁止

| 文件 | 说明 |
|------|------|
| 仓库根 `.env` | 仅开发；勿设 `ENVIRONMENT=production` |
| `backend/.env.production` | 若存在，仅为历史备份；**不要**被 uvicorn 自动加载 |
| `backend/youding_dev.db` | 开发 SQLite，**禁止**用于生产 |

## 相关模板

- `env.template` — 本目录合并清单（入口）
- `../backend/config/prod/.env.example` — 后端分项模板
- `../backend/.env.prod.example` — 商用飞轮/创始人字段
- `../.env.prod.example` — 根目录历史模板

## 域名与 CORS

生产域名在服务器 `.env` 配置 `SITE_URL`、`FRONTEND_URL`、`CORS_ORIGINS`。  
本地开发只用 `localhost:5173` / `127.0.0.1:8001`。
