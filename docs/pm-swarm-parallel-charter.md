# PM 蜂群并行开发宪章

> **签发**：ECC 产品经理（PM-07）  
> **生效**：2026-06-02 · **永久**（直至 PM 书面修订）  
> **机器规则**：`.cursor/rules/00-pm-swarm-parallel-charter.mdc`（`alwaysApply: true`）  
> **分配表**：[`pm-task-allocation-20260602.md`](./pm-task-allocation-20260602.md)

---

## 一、总则

产品经理以 **M3 蜂群合议** 模式调度各专家团队：**并行开发、边界清晰、质量优先**。

| 维度 | 要求 |
|------|------|
| **代码质量** | 最小正确 diff；单测/脚本/门禁有证据；不引入 cert:gate 回归 |
| **思路清晰** | 每交付附「目标 ID → 做法 → 验收 → 不测范围」四行摘要 |
| **逻辑严谨** | 数据流与权限链可追溯；失败路径有处理或显式 TODO+ID；**禁止假接口/假成功/假数据**（见 `docs/no-fake-delivery-charter.md`） |
| **边界清** | In/Out/Interface 三栏必填；禁止跨 Lane 顺手改 |

**硬规则**：Sprint-S2（人类/签字）不占蜂群带宽；研发 standup 只报 Sprint-R1 泳道。

---

## 二、蜂群泳道 · Sprint-R1（并行，无隐式串行）

```text
Lane A 架构 ── ARCH-01 ──┐
         └── ARCH-04 ──┤
Lane B 前端 ── BJ-01 ───┤
Lane C 表格 ── BJ-02 ───┼──► Gate-W2 / cert:gate（Lane F 守门）
Lane D CRUD ── BJ-03 ───┤
Lane E 后端 ── BE-06 ───┤
Lane F QA ──── QA-04 ───┤
         └── QA-02 ────┤
Lane G IP ──── PAT-02 ──┤
         └── COMP-06 ──┤
Lane H PM ──── PM-07 ───┘
         └── DOC-02
```

### 依赖矩阵（仅下列为硬依赖）

| 任务 | 依赖 | 说明 |
|------|------|------|
| QA-04 72h | ARCH-01 冒烟通过 | 72h 全量压测；冒烟可并行 |
| BJ-03 路由注册 | BJ-03 生成物 | 不依赖 BJ-01/02 |
| BJ-01 验收 | SaaS 专家 | 产品否决权，非技术阻塞 |
| ARCH-04 | MOD-01 可选联调 | 与百家 Lane **可并行** |

**其余 Lane 两两无硬依赖，默认同时推进。**

---

## 三、Lane 边界契约

### Lane A · 架构（ARCH-01 / ARCH-04）

| | |
|--|--|
| **In** | `scripts/run-arch-01-cert-gate.ps1`、`staging-preflight`、`docker-compose` HTTPS、DNS 记录 |
| **Out** | Admin/Client Vue 业务页、BFF 业务逻辑 |
| **Interface** | 输出 `docs/staging-preflight-auto-latest.json`；compose 日志路径写入 tracker |

### Lane B · 前端 Formily（BJ-01）

| | |
|--|--|
| **In** | `site-editor-lab`、`_ref/formily-antdv-x3` 接入、BFF 草稿读写 |
| **Out** | 全局 Layout 重构、234 页批量替换 |
| **Interface** | SaaS 专家五问验收；`cert:gate` 不新增 P1+ |

### Lane C · 表格（BJ-02）

| | |
|--|--|
| **In** | `useYoudingTable`、列拖拽、搜索条、Art 734 对齐 |
| **Out** | Formily、CRUD 生成器 |
| **Interface** | 单测覆盖列配置 + 搜索；不改 OpenAPI |

### Lane D · CRUD（BJ-03）

| | |
|--|--|
| **In** | `gen-crud-from-openapi.mjs` 产出、`views/_generated/*`、路由注册 Top12 至少 3 页 |
| **Out** | 新建后端 endpoint、改 OpenAPI 契约 |
| **Interface** | 仅用已有 OpenAPI；页面须过 plan-gate meta |

### Lane E · 后端导出（BE-06）

| | |
|--|--|
| **In** | `export-rz-60-pages.py`、meta 校验、readability 脚本 |
| **Out** | Admin 前端、专利正文人类撰写 |
| **Interface** | 绿档 JSON + 文件清单归档 `docs/` |

### Lane F · QA（QA-04 / QA-02）

| | |
|--|--|
| **In** | Locust 冒烟/72h、`cert:gate` 周报 |
| **Out** | 直接改业务功能（开 bug → 指派 Lane 主责） |
| **Interface** | `docs/qa-locust/`、`certification-gate-admin-latest.json` |

### Lane G · IP/专利（PAT-02 / COMP-06）

| | |
|--|--|
| **In** | 检索 memo、律师复审表草稿 |
| **Out** | 产品代码、S2 签字 |
| **Interface** | PDF/MD 归档；COMP-07 扫描维持 PASS |

### Lane H · PM/文档（PM-07 / DOC-02）

| | |
|--|--|
| **In** | 统计、分配、进度条、三文档一致 |
| **Out** | 代写各 Lane 实现代码 |
| **Interface** | 周一更新 tracker + `pm-dev-task-progress.json` |

---

## 四、质量门禁（全 Lane）

1. **提交前**：Lane 主责自测清单打勾（见各 Lane Interface）。
2. **合并前**：`npm run cert:gate` → P0/P1/P2=0（Lane F 每周五强制）。
3. **越界审查**：PR 文件 diff 出现 Out-of-Scope 路径 → PM 拒收或拆 PR。
4. **进度诚实**：`pct` 仅在有可演示/可脚本证据时上调。

---

## 五、PM 下达指令（2026-06-02 · 永久）

1. **即日起** 各专家团队按上表 **Lane 并行开工**，standup 报 **Lane + ID + pct**。
2. **6/3 10:00 前** 各 Lane 主责在 [`ecc-delivery-tracker.md`](./ecc-delivery-tracker.md) 确认认领。
3. **质量四原则**（代码质量、思路清晰、逻辑严谨、边界清）为 **永久验收标准**。
4. 修订本宪章须 PM-07 书面版本号 + 更新 `.mdc` 与分配表。

---

*ECC 产品经理 · 蜂群并行宪章 v1 · 永久生效*
