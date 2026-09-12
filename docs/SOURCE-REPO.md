# 源码仓说明 — 为何有「上线网站」与 CodeBuddy 两个文件夹

## 结论（先看这个）

| 文件夹 | 角色 | 是否日常开发 |
|--------|------|--------------|
| **`Desktop/上线网站`** | 从 CodeBuddy **完整复制**出的可运行源码 | ✅ **唯一开发仓** |
| **`UJ/website CodeBuddy`** | 历史总仓（含大量 IDE 缓存、审计、备份、实验目录） | ❌ 仅归档/对照，**AI 与 IDE 不宜整仓打开** |
| **`Desktop/出海计`** | Obsidian 知识库；`docs/` 从 **上线网站** 同步 | 📖 文档镜像 |

**产品代码、pytest、cert:gate、送检** — 一律以 **`上线网站`** 为准。

---

## 为什么单独复制一份

`website CodeBuddy` 体积过大（多 IDE 配置、`.codebuddy`、备份、历史报告、重复实验目录等），导致：

- Cursor / Agent **索引与上下文跑不动**
- 文档与代码 **混在同一巨仓**，难以隔离开发工具与产品源码
- 日常调试路径混乱（脚本里仍写 CodeBuddy 绝对路径）

因此将 **已开发好的可运行部分** 完整复制到：

```text
C:\Users\97907\Desktop\上线网站
```

**实测对比（2026-05-31）**：CodeBuddy ~477,791 文件 / ~6.9 GB → 上线网站 ~80,577 文件 / ~1.1 GB（约 **1/6 体积**）。

复制范围包含：`backend/`、`frontend/`、`docs/`、`scripts/`、`deploy/`、`docker*`、测试与构建脚本等**产品相关目录**；  
**不追求**与 CodeBuddy 字节级一致，但 **功能上为同一套系统的可运行快照**。

CodeBuddy 保留作：

- 历史 PRD / 旧 Sprint 文档对照
- ECC 安装包路径（`v1.10.0/ECC-1.10.0`）
- 需要时 cherry-pick 单文件

---

## 与出海计文档的关系

```
上线网站/docs  ──sync──►  出海计/docs   （Obsidian 阅读）
上线网站/backend、frontend  ──✗──►  不出海计（IDE 直接开上线网站）
CodeBuddy  ──✗ 默认不再作为 docs 同步源
```

同步命令：

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\97907\Desktop\上线网站\scripts\sync-to-chuhaiji-kb.ps1"
```

或：

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\97907\Desktop\出海计\scripts\sync-from-repo.ps1"
```

---

## 禁止事项

- 不要用 CodeBuddy 全量覆盖 `上线网站`（除非用户明确要求合并）
- 不要把 CodeBuddy 当作「当前进度 / 当前测试数」的权威（多为过期快照）
- 开发工具栈（`.cursor`、`.codegraph`）见 `docs/DEV-TOOLS-ISOLATION.md`，与产品源码隔离

---

## 本地运行（固定）

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-dev-admin.ps1
```

- API `http://127.0.0.1:8001`
- Admin `http://127.0.0.1:5173`
- DB `backend/youding_dev.db`

详见 `docs/WORKSPACE-ISOLATION.md`。
