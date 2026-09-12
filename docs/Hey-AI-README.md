# Hey AI README — 全局 AI 对话栈

> 给 Cursor / Claude / Codex 等 AI 助手：进入本仓库后**默认全开**，无需用户每次说明。  
> **开发进度与配置（多 IDE）**：[`docs/多IDE开发进度与配置索引.md`](多IDE开发进度与配置索引.md) · 同步 `scripts/sync-dev-docs-to-ides.ps1`

## 四层栈（每条对话自动启用）

```
用户消息
  → Agency 184 + ECC 38（222 人七阶段编排）
  → CodeGraph MCP（本地代码知识图谱）
  → Hey AI README（本文件 + 规则 .cursor/rules/hey-ai-readme.mdc）
  → ECC 工程门控（TDD / Review / Security / E2E）
```

## 1. Agency 184 + ECC 38

| 项 | 路径 |
|----|------|
| 启动 | `python scripts/agency-launch.py` |
| 工作流 | `workflows/agency-ecc-full.yaml` |
| Agency | `C:/Users/97907/.claude/agents/`（184 位） |
| ECC | `.cursor/agents/`（38 位） |
| 项目规则 | `.cursor/rules/00-agency-ecc-global-autoload.mdc` |
| 用户级规则 | `C:/Users/97907/.cursor/rules/00-ai-stack-global.mdc` |

**轻量例外**：纯寒暄、名单查询、无实现意图的文档解释 → 只跑 `agency-launch.py` 摘要，不跑完整 7 阶段。

## 2. CodeGraph

[CodeGraph](https://github.com/colbymchenry/codegraph) 在本机预索引符号、调用链、FastAPI 路由；100% 本地 SQLite，无 API key。

| MCP 工具 | 用途 |
|----------|------|
| `codegraph_search` | 按名搜符号 |
| `codegraph_explore` | 一次拿多文件相关源码（Explore 子代理主用） |
| `codegraph_context` | 按任务拼上下文 |
| `codegraph_callers` / `codegraph_callees` | 调用链 |
| `codegraph_impact` | 改动影响面 |
| `codegraph_affected` | 变更影响的测试文件 |

索引目录：`.codegraph/`（已 gitignore）。

**与 CI 互补**：`scripts/check_mounted_routes.py` 做运行时 FastAPI 挂载门禁；CodeGraph 做静态路由 → handler 映射。

## 3. 一键全局安装

```powershell
cd "c:\Users\97907\Desktop\UJ\website CodeBuddy"
powershell -ExecutionPolicy Bypass -File scripts/install-ai-stack-global.ps1
```

安装后**重启 Cursor**，使 MCP 与规则生效。

## 4. 手动分步（排错用）

```powershell
# CodeGraph CLI
npm i -g @colbymchenry/codegraph@latest
codegraph install --target=cursor --location=global --yes
cd "c:\Users\97907\Desktop\UJ\website CodeBuddy"
codegraph init -i

# 验证
codegraph status
python scripts/agency-launch.py
```

## 5. 工程向 vs 业务向

| 受益 | 无感 |
|------|------|
| architect、planner、code-reviewer、tdd-guide、explore 子代理 | 营销、文案、财务、客服等 Agency 角色 |

CodeGraph 是**工程基础设施**，不替代 222 人分工与 ECC 质量门。
