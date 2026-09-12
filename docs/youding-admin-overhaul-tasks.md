# 优丁 Admin 换皮 · 任务分配板

> **总 PRD**：`youding-admin-overhaul-prd.md`  
> **更新**：2026-05-31  
> **用法**：按 **Wave** 推进；每任务带 **负责角色（ECC）**、**依赖**、**验收**。

**状态**：`todo` | `doing` | `done` | `blocked`

---

## Wave 0 · 本周启动（PM + 摸底）

| ID | 任务 | 负责（ECC） | 依赖 | 验收 | 状态 |
|----|------|-------------|------|------|------|
| **T-PM-01** | 拉取 **30 天路由访问**（或埋点方案：PostHog/网关日志），产出 Top30 真实页 | 产品经理 · 数据 | — | `docs/analytics/admin-route-usage.md` | todo |
| **T-PM-02** | **Stub/实验室可见性矩阵**：每壳哪些菜单对外、哪些仅内网、哪些下线 | 产品经理 | 未开发任务清单 | 表格 + 产品签字 | todo |
| **T-PM-03** | **迁移地图**：旧路径 → 新路径（含 301 列表） | 产品经理 · 文档 | 四壳文档 | 1 页用户向说明 | todo |
| **T-PM-04** | 定 **Brand Tier**（统一壳 / Logo+主色 / 白标登录） | 产品经理 · 视觉 | branding API | 写入 PRD 附录 | todo |
| **T-PM-05** | 问清 **送检**：换 Client 壳是否触发手册重拍 | 产品经理 · 合规 | 省级达标清单 | 书面结论 | todo |
| **T-PM-06** | **MIT 开源声明** 页（Vben + kit 依赖） | 产品经理 · 合规 | — | `docs/OPEN-SOURCE-NOTICES.md` | todo |
| **T-ARCH-01** | 评审 **三轨并行** 与仓库目录（admin / admin-vben / kit） | 架构指挥官 | PRD | 架构纪要 1 页 | todo |

---

## Wave 1 · 底座 + BFF（第 2–3 周）

| ID | 任务 | 负责（ECC） | 依赖 | 验收 | 状态 |
|----|------|-------------|------|------|------|
| **T-FE-01** | Clone **Vben web-antd** → `frontend/admin-vben`，dev 跑通 | 前端架构师 | T-ARCH-01 | `pnpm dev:antd` OK | todo |
| **T-FE-02** | 配置 API 代理 → `:8001`，对接 **admin-bff** 登录/用户信息 | 前端架构师 · API | BFF 已有 | 登录进 Layout | todo |
| **T-FE-03** | 接 **menu/routes + permissions** 动态路由（Client shell） | 前端架构师 | T-BE-02 | Client 菜单 ≤5 项 | todo |
| **T-BE-01** | BFF **P1 安全**：captcha 或加强限流；tenant/search 防枚举 | 后端架构师 · 安全 | security  doc | 单测 + 限流配置 | todo |
| **T-BE-02** | BFF **component 路径白名单**；菜单种子与 DB 树合并策略 | 后端开发 | menu_adapter | 恶意 path 403 | todo |
| **T-BE-03** | **主链 P0 接线**（referral、super-admin 等见未开发清单）与换皮页对齐 | 后端开发 | T-PM-02 | 关键 API 200 | todo |
| **T-UX-01** | **Client Dashboard 线框**（欢迎区+4 支柱+onboarding 卡） | 陈列视觉 · UI | T-PM-04 | Figma/截图评审 | todo |
| **T-UX-02** | 扩展 **design-tokens**（租户渐变、卡片阴影） | 陈列视觉 | kit tokens | 与 branding 一致 | todo |
| **T-OPS-01** | **双前端并行 + 回滚** runbook（Nginx / 环境变量） | DevOps | T-FE-01 | 10 分钟切回旧 admin | todo |

---

## Wave 2 · Client 换皮（第 4–6 周）

| ID | 任务 | 负责（ECC） | 依赖 | 验收 | 状态 |
|----|------|-------------|------|------|------|
| **T-FE-10** | **TenantShell** Layout（Naive 留白 + Vben 侧栏） | 后台页面搭建 · 视觉 | T-UX-01 | 移动断点可用 | todo |
| **T-FE-11** | **Dashboard** 用 YdStatsCard + onboarding | 后台页面搭建 | T-BE-03 | 真实 API 数据 | todo |
| **T-FE-12** | **财旺 FAB** 迁入 Vben Client 壳 | 全栈 | UBrain 现网 | 拖动+对话 OK | todo |
| **T-FE-13** | **useYoudingTable** 接 3 页：询盘、开票、产品 | 后台页面搭建 | kit | 表格约定 table.md | todo |
| **T-FE-14** | Client **Top12** 路由迁入或 iframe 过渡 | 后台页面搭建 | T-PM-01 Top 列表 | 12 页 smoke | todo |
| **T-FE-15** | **登录页** 分屏品牌 + tenant_code | 后台页面搭建 · 视觉 | T-BE-01 | 登录 E2E | todo |
| **T-UX-03** | Client **移动端** 验收清单（侧栏、表格横滚） | 陈列视觉 · QA | T-FE-10 | checklist 全绿 | todo |
| **T-QA-01** | **四壳泄漏 E2E**：代理不见超管菜单 | 后端测试 · QA | T-FE-03 | 自动化或脚本 | todo |
| **T-QA-02** | **Lighthouse 基线**（Dashboard、登录） | 性能 · QA | T-FE-11 | 报告存档 | todo |
| **T-DOC-01** | 用户向 **「What's changed」** + 客服话术 | 产品经理 · 文档 | T-PM-03 | 1 页 + FAQ | todo |

---

## Wave 3 · Platform / Agent + 治理（第 7–10 周）

| ID | 任务 | 负责（ECC） | 依赖 | 验收 | 状态 |
|----|------|-------------|------|------|------|
| **T-FE-20** | Platform **Tab A/B/C** 菜单与 8 主干页 | 后台页面搭建 | T-BE-02 | 超管 smoke | todo |
| **T-FE-21** | Agent **5 页** + 零超管泄漏复核 | 后台页面搭建 | T-QA-01 | agent E2E | todo |
| **T-FE-22** | **Stub 菜单隐藏** + 「开发中」统一页 | 产品经理 · 前端 | T-PM-02 | 租户不见 stub | todo |
| **T-BE-10** | **操作审计** 接 RuoYi 清单（登录/权限变更） | 后端开发 | audit 模型 | 超管可查 | todo |
| **T-BE-11** | OpenAPI **CRUD 生成器** v0（询盘类） | 后台页面搭建 · 后端 | Better 思路 | 生成 1 模块 | todo |
| **T-SEC-01** | 安全门禁全绿（见 security.md 第八节） | 安全 · QA | Wave1–2 | checklist | todo |

---

## Wave 4 · 切换与复盘（第 11–12 周）

| ID | 任务 | 负责（ECC） | 依赖 | 验收 | 状态 |
|----|------|-------------|------|------|------|
| **T-OPS-02** | **生产切换** admin-vben 为默认；旧 admin 只读备份 | DevOps · 架构 | Wave2–3 | 切换窗口记录 | todo |
| **T-OPS-03** | **回滚演练** 1 次 | DevOps | T-OPS-01 | 演练报告 | todo |
| **T-PM-10** | **OKR 复盘**（KR1–4）+ 下一季度 scope | 产品经理 | M4 | 复盘文档 | todo |
| **T-DOC-02** | 送检材料/UI 截图 **如需则更新** | 产品经理 · 文档 | T-PM-05 | 签字 | todo |

---

## 并行轨 A · 产品完善（与换皮全程交织）

| ID | 任务 | 负责 | 说明 | 状态 |
|----|------|------|------|------|
| **T-PROD-01** | 七步主链 **未接线 API** 按 P0 清单清零 | 后端开发 | 见 `未开发任务清单.md` | doing* |
| **T-PROD-02** | Onboarding **后端状态机**（步骤完成度 API） | 后端 · 产品 | Dashboard 卡片数据源 | todo |
| **T-PROD-03** | **Copilot vs 财旺** 文案与入口统一 | 产品经理 | 对外只说财旺/租户品牌 | todo |
| **T-PROD-04** | 实验室 **Feature Flag** 默认关 | 后端 · 前端 | Platform 治理区 | todo |

\* 与现有 Sprint 重叠处由 Owner 合并，避免重复开工。

---

## ECC 角色 ↔ 任务负载（建议）

| 角色 | Wave0–1 | Wave2 | Wave3–4 |
|------|---------|-------|---------|
| **产品经理** | T-PM-01~06 主导 | T-DOC-01、验收 | T-PM-10、送检 |
| **架构指挥官** | T-ARCH-01 | 技术债评审 | 切换决策 |
| **前端架构师** | T-FE-01~03 | 代码评审 | Vben 升级策略 |
| **后台页面搭建** | — | T-FE-10~15 主力 | T-FE-20~22 |
| **后端开发** | T-BE-01~03 | 支持 Client API | T-BE-10~11 |
| **陈列视觉** | T-UX-02 | T-UX-01/03 | Dashboard 迭代 |
| **DevOps** | T-OPS-01 | 预发环境 | T-OPS-02~03 |
| **QA/安全** | — | T-QA-01~02 | T-SEC-01 |

---

## 本周立即开工（建议顺序）

```
1. 你（Owner）签字 PRD「不做什么」          ← 30 分钟
2. T-PM-02 Stub 可见性矩阵                  ← 产品 1 天
3. T-ARCH-01 + T-FE-01 Vben 底座            ← 前端 2 天
4. T-BE-03 与 T-PROD-01 主链 API 对齐       ← 后端 并行
5. T-UX-01 Dashboard 线框                   ← 视觉 并行
```

---

## 阻塞项（需你输入）

| 阻塞 | 需要决定 |
|------|----------|
| B-01 | 项目 **Owner** 姓名/角色 |
| B-02 | 预发/生产 **切换窗口** 最早日期 |
| B-03 | 送检是否 **M2 后必须重拍手册**（T-PM-05） |
| B-04 | 旧 admin **下线日期** 硬 deadline 有无 |

---

## 进度同步

- 每周五更新本表 `状态` 列  
- 同步写入 `docs/module-progress.json` → 模块 `admin-overhaul`  
- 蜂群/Task 子 agent 按 **Wave + ID** 领任务，避免同文件冲突

**下一步执行口令**：回 **「执行 Wave0」** 或 **「执行 T-FE-01」**，按 ID 自动开工。
