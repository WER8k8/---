# 轻集料混凝土官网 — 企业级全栈 AI SEO 系统

> **有能力的大神请帮我优化补充一下，谢谢**

## 项目定位

企业级轻集料混凝土官方网站，采用 **Nuxt.js 3 + FastAPI** 全栈架构，融合 **AI SEO 智能运营系统**，实现百度权重10目标。

### 核心特性
- **SSR 服务端渲染** — 面向百度爬虫和AI搜索引擎优化
- **AI 驱动内容优化** — LLMs.txt生成、Meta智能优化、网站自动审计
- **混合开发模式** — InsCode生成 + 手写核心 + 开源集成
- **DevOps 自动化** — Docker容器化 + GitHub Actions CI/CD
- **企业级安全** — OWASP TOP 10零容忍 + RBAC权限

## 技术栈概览

| 层 | 技术 | 用途 |
|----|------|------|
| 前端 | Nuxt.js 3 + Vue 3 + TypeScript | SSR官网 |
| 后台 | vue-vben-admin + Ant Design Vue | SEO管理面板 |
| 后端 | FastAPI + Python 3.11 | API服务 |
| 数据库 | PostgreSQL 15.6 + Redis 7.2.4 | 数据存储/缓存 |
| AI | LangChain + OpenAI/Claude/Gemini | 智能内容优化 |
| DevOps | Docker + GitHub Actions | 自动化部署 |

## 项目结构

```
├── frontend/        # Nuxt.js 3 前端
├── backend/         # FastAPI 后端
├── ai-engine/       # AI 引擎
├── docker/          # Docker 配置
├── docs/            # 技术文档
└── docker-compose.yml
```

## 文档索引

| 文档 | 说明 |
|------|------|
| [项目概述与架构](docs/0-项目概述与架构.md) | 整体架构、模块划分 |
| [技术栈清单](docs/1-技术栈清单.md) | 完整技术栈版本表 |
| [系统架构设计](docs/2-系统架构设计.md) | 前后端架构、目录结构 |
| [数据库Schema设计](docs/3-数据库Schema设计.md) | 11张表结构、索引设计 |
| [API接口定义](docs/4-API接口定义.md) | 5大模块API规范 |
| [项目目录结构](docs/5-项目目录结构.md) | 完整文件树 |
| [Docker与CI_CD配置](docs/6-Docker与CI_CD配置.md) | 容器化 + 自动部署 |
| [SEO核心功能设计](docs/7-SEO核心功能设计.md) | LLMs/优化器/审计引擎 |
| [阶段验收标准](docs/8-阶段验收标准.md) | 4阶段验收标准 |
| [开发路线图与资源规划](docs/9-开发路线图与资源规划.md) | 12周路线图 |
| [AI智能体系统配置](docs/10-AI智能体系统配置.md) | 46智能体分配 |
| [**Hey AI README**](docs/Hey-AI-README.md) | **全局对话栈**：CodeGraph + Agency 184 + ECC 38 |
| [**产品经理-开发文档**](docs/产品经理-开发文档.md) | **研发下发总册 v2.0+**：七步闭环 + 四壳/UBrain/出海参谋/**优丁 App** |
| [**出海计-App产品规格**](docs/出海计-App产品规格.md) | **出海计** 商家 App（必做）、豆包式、Push/BFF |
| [**战略总纲 2026（融资·政府·方向）**](docs/战略总纲-2026-面向融资与政府.md) | **创始人/投资人必读**：不整库迁移、四壳、路线图、盈利与验收标准 |
| [四壳信息架构与菜单治理](docs/四壳信息架构与菜单治理.md) | Client/Platform/Agent 分壳、菜单删留、每月验收 |
| [UBrain 统一调度大脑规格](docs/UBrain-统一调度大脑-产品规格.md) | AI 副驾：越用越聪明、分阶段落地、与现 API 对接 |
| [产品俯视-租户旅程与三轨计费](docs/产品俯视-租户旅程与三轨计费.md) | 卖货闭环、三轨收费、40平台、呼朋唤友、总站权重枢纽 |
| [产品对话总览-定稿](docs/产品对话总览-定稿.md) | 对话结论一页纸、优先级摘要 |
| [未开发任务清单](docs/未开发任务清单.md) | **全仓扫描**：未实现/未挂载/前后端不一致任务 backlog |
| [开发任务下发清单](docs/开发任务下发清单.md) | **团队下发版**：Sprint A～D、角色、DoD、依赖图 |
| [dev-backlog-sprint.json](docs/dev-backlog-sprint.json) | 机器可读任务板（领取人、状态、验收命令） |
| [呼朋唤友-客户裂变营销方案](docs/呼朋唤友-客户裂变营销方案.md) | 租户裂变 L1/L3/L5 小计划与排行榜 |

## 给 AI 助手（Hey AI README）

本仓库在 **Agency 184 + ECC 38（222 人）** 编排之外，推荐启用 **[CodeGraph](https://github.com/colbymchenry/codegraph)**：本地预索引代码知识图谱（MCP），减少 grep/Read 探索，对工程向智能体（架构、review、TDD、影响分析）有明显加成；营销/文案类角色无感。

| 能力 | 说明 |
|------|------|
| 符号搜索 / 调用链 | `codegraph_search`、`codegraph_callers`、`codegraph_callees` |
| 探索与上下文 | `codegraph_explore`、`codegraph_context`（大段源码，宜在 Explore 子代理中用） |
| 改动影响面 | `codegraph_impact`；CI 可配合 `codegraph affected` 缩小测试范围 |
| FastAPI 路由 | 静态识别 `@app.get` 等 → handler；与 `scripts/check_mounted_routes.py`（运行时挂载门禁）互补 |
| 索引目录 | `.codegraph/`（已 gitignore，勿提交） |

**一键全局安装（CodeGraph + Hey AI README + Agency + ECC）：**

```powershell
cd "c:\Users\97907\Desktop\UJ\website CodeBuddy"
powershell -ExecutionPolicy Bypass -File scripts/install-ai-stack-global.ps1
```

安装后**重启 Cursor**。详细说明见 [docs/Hey-AI-README.md](docs/Hey-AI-README.md)。

**222 人编排（与本节并行）：** `python scripts/agency-launch.py` · 工作流 `workflows/agency-ecc-full.yaml` · 规则 `.cursor/rules/00-agency-ecc-global-autoload.mdc` · 用户级 `~/.cursor/rules/00-ai-stack-global.mdc`

## 开发阶段

| 阶段 | 时间 | 内容 |
|------|------|------|
| Phase 1 | 第1-2周 | 基础架构搭建 + DevOps |
| Phase 2 | 第3-5周 | 核心SEO功能开发 |
| Phase 3 | 第6-9周 | 高级功能（Schema/EEAT/合规/权限） |
| Phase 4 | 第10-12周 | 优化上线 + 验收交付 |

## 快速启动

```bash
# 1. 克隆仓库
git clone https://github.com/WER8k8/企业官方开发日志-小学文化的小白.git
cd wang-zhan

# 2. 启动所有服务（需要 Docker）
docker compose up -d

# 3. 访问服务
# 前端: http://localhost:3000
# 后端API: http://localhost:8000/docs
# MinIO控制台: http://localhost:9001
```

## 核心承诺

1. **技术可行性** — 基于真实开源仓库重构，100%功能可实现
2. **百度权重增长** — 系统化SEO策略，月均权重增长≥1
3. **AI搜索优化** — LLMs.txt + EEAT + Schema 三重覆盖主流AI搜索引擎
4. **合规安全** — 广告法合规 + OWASP TOP 10零漏洞
5. **持续迭代** — 交付后6个月免费技术支持

---

**仓库**: https://github.com/WER8k8/企业官方开发日志-小学文化的小白
**作者**: 优丁公司技术团队
