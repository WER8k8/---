# 工作区与生产环境隔离

**本仓库（`Desktop/上线网站`）= 本地开发源码。** 生产部署使用独立配置与服务器，避免与日常开发混淆。

## 路径矩阵

| 角色 | 路径 | 做什么 |
|------|------|--------|
| 开发源码 | `C:\Users\97907\Desktop\上线网站` | 改代码、跑 Vite/uvicorn、单测 |
| **开发工具栈（外部）** | `%USERPROFILE%\.devstack\shangxian-website\` | Cursor/ECC、workflows；**不进 git** |
| CodeGraph 索引 | `上线网站\.codegraph\` | 仅本地；**gitignore** |
| 生产模板 | `deploy/production/` | 服务器 `.env` 的示例与清单 |
| 知识库 | `C:\Users\97907\Desktop\出海计` | 文档、交接、Obsidian（见 `SYNC.md`） |
| 历史总仓（归档） | `C:\Users\97907\Desktop\UJ\website CodeBuddy` | 过大；仅对照 / ECC 包；见 `docs/SOURCE-REPO.md` |
| ECC 包 | `...\website CodeBuddy\v1.10.0\ECC-1.10.0` | AI 技能安装源（装到**外部** dev-stack） |
| 生产机 | 远程 VPS | 真实密钥与 PostgreSQL |

## 本地开发（唯一推荐入口）

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-dev-admin.ps1
```

- API：`http://127.0.0.1:8001`
- Admin：`http://127.0.0.1:5173`
- DB：`backend/youding_dev.db`（SQLite）
- 账号：`admin` / `admin123`

`start-dev-admin.ps1` 会覆盖 `DATABASE_URL` 与 `JWT_SECRET_KEY`，避免误连生产库。

## 生产环境

1. 模板：`deploy/production/env.template`
2. 服务器上单独维护 `.env`（不进 git）
3. 部署前在目标环境跑：`python scripts/run_production_preflight.py`
4. 清单参考：`出海计/docs/出海计/主站商用MVP-上线清单.md`

## 禁止事项

- 在根目录 `.env` 使用 `ENVIRONMENT=production` 做日常开发
- 把 `backend/.env.production` 当作本地默认配置
- 从 CodeBuddy **全量覆盖** 本仓库而不合并 landing/hierarchy 等差异
- 将 `.env`、API Key 复制到 `出海计/`
- **将 `.cursor/`、`ecc-install.json`、CodeGraph 索引提交进 git 或打进送检包**

## 开发工具隔离（强制）

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-dev-stack-external.ps1
powershell -ExecutionPolicy Bypass -File scripts/install-dev-stack-external.ps1 -InstallEcc
```

详见 **`docs/DEV-TOOLS-ISOLATION.md`** · 配置 **`.project/dev-stack.config.json`**

## 验证

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-dev-isolation.ps1
```

## AI 栈安装

```powershell
# 开发工具 → 仓库外（推荐，与产品代码隔离）
powershell -ExecutionPolicy Bypass -File scripts/install-dev-stack-external.ps1 -InstallEcc

# CodeGraph + 用户级 MCP（可选）
powershell -ExecutionPolicy Bypass -File scripts/install-ai-stack-global.ps1
```

项目策略（可入库）：`.project/rules/00-workspace-isolation.mdc`  
Cursor 实际规则：外部 dev-stack `.cursor/rules/`（通过 Junction 挂载）
