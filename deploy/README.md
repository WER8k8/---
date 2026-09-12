# 部署目录

本目录与 **本地开发源码** 分离，便于以后上服务器时不与 `Desktop/上线网站` 日常开发混淆。

| 子目录 | 用途 |
|--------|------|
| `production/` | 生产环境变量**模板**、上线清单、服务器侧说明 |

## 原则

- **开发**：只在仓库根用 `scripts/start-dev-admin.ps1`（SQLite、`ENVIRONMENT=development`）
- **生产**：真实 `.env` 只放在 **服务器** 或密码管理器，不提交 git
- **模板**：仓库内仅保留 `*.example` / `env.template`

详见 [`docs/WORKSPACE-ISOLATION.md`](../docs/WORKSPACE-ISOLATION.md)。
