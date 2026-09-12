# 多 IDE 开发进度与配置索引

> **同步时间**：2026-05-25  
> **用途**：Cursor、通义灵码、Trae、CodeBuddy/Codex、Obsidian 共用同一套进度与配置文档。  
> **刷新**：改 `docs/` 后执行 `scripts/sync-dev-docs-to-ides.ps1`。

---

## 1. 进度权威源（只改一处）

| 文件 | 内容 |
|------|------|
| [`module-progress.json`](module-progress.json) | 20 模块权重、PM 阻塞、代码任务 ID 摘要 |
| [`未完成开发任务表.md`](未完成开发任务表.md) | P0～P2、UX/AI、出海计 App 逐条状态 |
| [`IDE-开发交接记录.md`](IDE-开发交接记录.md) | 批次交付、环境变量、下一优先 |
| [`进度看板.md`](进度看板.md) | 看板说明 + 快照路径 |
| [`module-progress-latest.txt`](module-progress-latest.txt) | 终端条形色块（脚本生成） |

```powershell
python scripts/module_progress.py
```

---

## 2. 各 IDE 读取路径

| IDE / 工具 | 仓库内入口 | 说明 |
|------------|------------|------|
| **Cursor** | `.cursor/rules/`、`AGENTS.md`、`CLAUDE.md` | ECC + Agency 编排 |
| **通义灵码** | `.lingma/rules/开发进度与配置同步.md` | 由同步脚本镜像 |
| **Trae** | `.trae/DEV_PROGRESS_SYNC.md` | 由同步脚本镜像 |
| **CodeBuddy** | `.codebuddy/DEV_PROGRESS_SYNC.md` | 由同步脚本镜像 |
| **Codex** | `.codebuddy/.codex/AGENTS.md` | 与 CodeBuddy 同仓 |
| **Obsidian / 桌面库** | `C:\Users\97907\Desktop\出海计\docs\` | `sync-to-chuhaiji-kb.ps1` 镜像 |

---

## 3. 功能与配置文档清单（全 IDE 必读）

### 3.1 产品 / PM

| 文档 | 用途 |
|------|------|
| [`产品经理-开发文档.md`](产品经理-开发文档.md) | 研发总册 v2.3 |
| [`战略总纲-2026-面向融资与政府.md`](战略总纲-2026-面向融资与政府.md) | 融资叙事 |
| [`四壳信息架构与菜单治理.md`](四壳信息架构与菜单治理.md) | Client/Admin/Agent |
| [`产品俯视-租户旅程与三轨计费.md`](产品俯视-租户旅程与三轨计费.md) | 七步闭环 |

### 3.2 智能与 App

| 文档 | 用途 |
|------|------|
| [`UBrain-统一调度大脑-产品规格.md`](UBrain-统一调度大脑-产品规格.md) | 助手意图 |
| [`出海参谋-贸易情报与UBrain.md`](出海参谋-贸易情报与UBrain.md) | 贸易情报 |
| [`出海计-App产品规格.md`](出海计-App产品规格.md) | App 四 Tab |
| [`出海计-Capacitor构建说明.md`](出海计-Capacitor构建说明.md) | 原生壳构建 |
| [`桌面知识库-出海计.md`](桌面知识库-出海计.md) | 桌面库同步 |
| [`出海计/UBrain-X-全员实施任务书.md`](出海计/UBrain-X-全员实施任务书.md) | UBrain-X 全员分工与验收 |
| [`出海计/UBrain-X-AccioWork全维度能力蓝图.md`](出海计/UBrain-X-AccioWork全维度能力蓝图.md) | Accio 全能力→分期 |

### 3.3 技术 / API / 运维

| 文档 | 用途 |
|------|------|
| [`0-项目概述与架构.md`](0-项目概述与架构.md) | 架构 |
| [`4-API接口定义.md`](4-API接口定义.md) | API 契约 |
| [`管理端路由与功能映射表.md`](管理端路由与功能映射表.md) | 路由 JSON |
| [`管理端统一登录与OAuth对接.md`](管理端统一登录与OAuth对接.md) | 登录 |
| [`演示验收清单.md`](演示验收清单.md) | 七步彩排 |
| [`Hey-AI-README.md`](Hey-AI-README.md) | AI 栈四层 |
| [`换机与本地调试清单.md`](换机与本地调试清单.md) | **换电脑 / 任意 IDE + 内置浏览器调试** |
| [`出海计/问题汇总与任务表.md`](出海计/问题汇总与任务表.md) | **问题总表 · 按 P0→P1 挨个解决** |
| [`本地IDE与网站系统能力对照表.md`](本地IDE与网站系统能力对照表.md) | **ECC 本地 vs 网站服务器** |
| [`技术栈-智能体-MCP-调度表.md`](技术栈-智能体-MCP-调度表.md) | 智能体分工 |
| [`运维-cron.md`](运维-cron.md) | cron |
| [`saas/ssl-automation.md`](saas/ssl-automation.md) | SSL |
| [`Sprint-O-商用收尾.md`](Sprint-O-商用收尾.md) | 商用 env |

### 3.4 代码内配置（改功能时对照）

| 路径 | 用途 |
|------|------|
| `backend/app/core/config.py` | 后端 Settings |
| `backend/.env.example` | 环境变量模板 |
| `frontend/admin/capacitor.config.ts` | 出海计包名 |
| `frontend/admin/public/manifest.webmanifest` | PWA |
| `.lingma/agents-config.md` | 灵码智能体绑定 |
| `workflows/agency-ecc-full.yaml` | 七阶段工作流 |

---

## 4. 当前进度摘要（2026-05-25）

| 维度 | 数值 |
|------|------|
| 排期 Sprint | **100%**（84/84） |
| 产品模块权重 | **约 78%**（156/200） |
| 商用 P0 未完成 | 约 **5** 条（SSL、演示域、cron、验签等） |
| 商用 P1 未完成 | 约 **7** 条 |
| UX/AI 未完成 | **UX-2c**、**AI-M1** |
| 出海计 App | PWA 已上线；商店包与 APP-2 待做 |
| **UBrain-X P0** | 后端 5 工具 **已落地**；`/client/copilot`、手机必填 **进行中** |

---

## 5. 同步命令（一条搞定）

```powershell
cd "C:\Users\97907\Desktop\UJ\website CodeBuddy"
powershell -ExecutionPolicy Bypass -File scripts/sync-dev-docs-to-ides.ps1
```

脚本会：刷新 `module-progress-latest.txt` → 镜像到灵码/Trae/CodeBuddy → 同步桌面「出海计」知识库。
