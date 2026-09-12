# 开发环境工具与产品代码隔离

> **原则：本文件夹（`上线网站`）= 产品源码。**  
> Cursor / ECC / CodeGraph / 蜂群 workflow 等**开发工具不得与产品代码混提交、混部署**。

## 三层分离

| 层 | 位置 | 是否进 git | 是否进送检/生产包 |
|----|------|------------|-------------------|
| 产品源码 | `backend/` `frontend/` `deploy/` `docs/` `scripts/` | ✅ 是 | ✅ 是 |
| 项目策略（轻量） | `.project/` | ✅ 是 | ✅ 可（仅 JSON/规则说明） |
| 开发工具栈 | `%USERPROFILE%\.devstack\shangxian-website\` | ❌ 否 | ❌ 否 |
| CodeGraph 索引 | `上线网站/.codegraph/`（本地） | ❌ 否（gitignore） | ❌ 否 |
| Cursor 联接 | `上线网站/.cursor` → 外部 | ❌ 否（gitignore） | ❌ 否 |

## 外部开发工具栈

默认根目录：

```text
C:\Users\97907\.devstack\shangxian-website\
  .cursor\              # ECC 38 + 项目规则（完整）
  workflows\            # agency-ecc-full.yaml 等
  ecc-install.json      # 安装 manifest
```

仓库内通过 **目录联接（Junction）** 挂载 `.cursor`，Cursor IDE 可正常使用，但 git 不会跟踪。

## 一键安装（推荐）

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-dev-stack-external.ps1
```

会完成：

1. 创建外部 dev-stack 目录
2. 将现有 `上线网站/.cursor` 迁到外部（若存在）
3. 建立 `.cursor` Junction
4. 同步 `.project/rules/` → 外部 `.cursor/rules/`
5. 初始化 `.codegraph/`（仅本地，已 gitignore）

## CodeGraph

- 索引目录必须在仓库旁（`codegraph` CLI 限制）：`上线网站/.codegraph/`
- **仅本地开发使用**，已通过 `.gitignore` 排除
- MCP 使用用户级 `~/.cursor/mcp.json`，不写入产品代码

## 产品硬锁（跨 IDE，入库）

`.project/*.json` 中的契约 **随产品源码入库**，Qoder / Cursor / CodeBuddy 等打开仓库即可读到，不依赖外部 `.cursor/`：

| 契约 | 说明 |
|------|------|
| `.project/login-entry-lock.json` | 管理端仅 `/login` 超管入口（LOGIN-LOCK-01） |
| `AGENTS.md` | 全 IDE AI 协作入口（优先读硬锁） |
| `docs/product/LOGIN-SINGLE-ENTRY-CHARTER.md` | 登录硬锁人类可读说明 |

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-login-entry-lock.ps1
```

## 验证隔离

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-dev-isolation.ps1
```

检查项包括：生产 env 误用、开发工具是否被 git 跟踪、Junction 是否指向外部、送检路径是否含 `.cursor`。

## 与生产隔离的关系

- 生产隔离：见 `docs/WORKSPACE-ISOLATION.md`（env、数据库、部署）
- 工具隔离：本文（AI 栈、IDE、索引不进产品树）

两者同时生效；**工具隔离优先级不低于生产隔离**。
