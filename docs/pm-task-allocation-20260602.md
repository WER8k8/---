# PM 全量任务统计与分配表

> **签发**：ECC 产品经理（PM-07）  
> **统计日**：2026-06-02  
> **性质**：**唯一分配依据** — standup / 研发 / Owner 均按本文执行  
> **蜂群宪章（永久）**：[`pm-swarm-parallel-charter.md`](./pm-swarm-parallel-charter.md) · `.cursor/rules/00-pm-swarm-parallel-charter.mdc`  
> **索引链**：[`ecc-meeting-saas-repo-master-index.md`](./ecc-meeting-saas-repo-master-index.md) · [`pm-master-schedule-kpi-20260601.md`](./pm-master-schedule-kpi-20260601.md)

---

## 一、全量统计（五层合并）

| 层级 | 代号前缀 | 条数 | ✅ | 🔄 | ⏳ | 说明 |
|------|----------|------|----|----|-----|------|
| **L1** PM 总表 ID | PM/FE/BE/… | **79** | 54 | 14 | 11 | 考核与 Gate 绑定 |
| **L2** 工程增量 | ENG-01~08 | **8** | 8 | 0 | 0 | 已交付，并入 L1 或 BJ |
| **L3** 百家收尾 | BJ-01~03 | **3** | 0 | 0 | 3 | ECC R4 · 99 汇总未完成项 |
| **L4** 业务模块缺口 | MOD-01~08 | **8** | 0 | 8 | 0 | `module-progress.json` 非 10/10 项 |
| **L5** 人类/签字链 | H-01~17 | **17** | 0 | 10 | 7 | **S2 批次**，不占研发 Sprint |
| | **合计活跃** | **115** | **62** | **32** | **21** | L1+L3+L4+L5 未✅ |

### L1 总表（79）按状态

| 状态 | 数量 |
|------|------|
| ✅ | 54 |
| 🔄 | 14 |
| ⏳ | 11 |

### L1 按部门（灯色）

| 部门 | 总数 | ✅ | 待办 | 灯色 | Sprint 归属 |
|------|------|----|------|------|-------------|
| PM | 8 | 2 | 6 | 🟡 | R1: PM-07 · S2: PM-03~08 |
| SaaS | 8 | 8 | 0 | 🟢 | 验收签字 |
| 前端 FE | 12 | 12 | 0 | 🟢 | R1: BJ-01~03 |
| 后端 BE | 6 | 5 | 1 | 🟢 | R1: BE-06 脚本收尾 |
| 视觉 UX | 8 | 8 | 0 | 🟢 | — |
| 营销 MKT | 6 | 5 | 1 | 🟡 | S2: MKT-06 |
| 架构 ARCH | 5 | 3 | 2 | 🟡 | **R1 主力** |
| QA | 4 | 3 | 1 | 🟡 | **R1: QA-04** |
| 合规 COMP | 7 | 2 | 5 | 🟡 | R1 脚本 / S2 人类 |
| IP | 4 | 2 | 2 | 🟡 | R1+PAT / S2 签字 |
| 专利 PAT | 6 | 2 | 4 | 🟡 | R1: PAT-02 / S2 申请 |
| 页面 PAGE | 2 | 2 | 0 | 🟢 | R1: BJ-02 |
| 文档 DOC | 3 | 2 | 1 | 🟢 | R1: DOC-02 |

---

## 二、Sprint 分配（已拍板 · 蜂群并行 · 立即执行）

### Sprint-R1 · 研发攻坚（6/3 – 6/16）

> **目标**：百家 10/10 · ARCH CERT 就绪 · Gate-W2 代码项清零  
> **模式**：**M3 蜂群并行** — 8 泳道同时推进，见 [`pm-swarm-parallel-charter.md`](./pm-swarm-parallel-charter.md)  
> **永久标准**：代码质量高 · 思路清晰 · 逻辑严谨 · 边界清  
> **规则**：SaaS 专家三条铁律有效；**不启动 S2 人类稿**

#### 蜂群泳道（Lane · 并行认领）

| Lane | 主责 | ID | 并行 | 边界（Out） |
|------|------|-----|------|-------------|
| **A** | 架构 | ARCH-01, ARCH-04 | ✅ | 不改 Vue 业务页 |
| **B** | 前端 | BJ-01 | ✅ | 不扩全局路由 |
| **C** | 页面搭建 | BJ-02 | ✅ | 不碰 Formily |
| **D** | 页面搭建 | BJ-03 | ✅ | 不新建后端 API |
| **E** | 后端 | BE-06 | ✅ | 不改 Admin UI |
| **F** | QA | QA-04, QA-02 | ✅ | 不修功能（开单指派 Lane） |
| **G** | IP/专利 | PAT-02, COMP-06 | ✅ | 不写产品代码 |
| **H** | PM/文档 | PM-07, DOC-02 | ✅ | 不代写 Lane 实现 |

**硬依赖仅 1 条**：QA-04 **72h 全量** 待 ARCH-01 冒烟通过；其余 Lane **默认同时开工**。

| 序 | ID | 任务 | **主责** | 协责 | 交付物 | 截止 |
|----|-----|------|----------|------|--------|------|
| 1 | **ARCH-01** | staging preflight 0 fail | 🎖 架构指挥官 | 后端架构师 | `docs/staging-preflight-auto-latest.json` ok | **6/10** |
| 2 | **ARCH-04** | HTTPS + compose 实跑 | 🎖 架构指挥官 | DevOps | compose 日志 + 域名记录 | **6/14** |
| 3 | **QA-04** | Locust 冒烟→72h 归档 | QA 组 | 架构 | `docs/qa-locust/locust-smoke-latest.json` + 72h CSV | **6/16** |
| 4 | **BJ-01** | Formily 接 `_ref/formily-antdv-x3` | 🧱 前端架构师 | SaaS 专家 | `site-editor-lab` 真 Formily | **6/12** |
| 5 | **BJ-02** | Art 734 行 table 能力补齐 | 🔧 后台页面搭建 | 前端 | `useYoudingTable` 列拖拽+搜索条 | **6/14** |
| 6 | **BJ-03** | Better CRUD 生成 Top12×3 | 🔧 后台页面搭建 | 后端 | `views/_generated/*` + 路由注册 | **6/14** |
| 7 | **BE-06** | backend 60 页导出校验 | 🗄 后端架构师 | IP 合规 | `export-rz-60-pages.py` 绿 + meta | **6/8** |
| 8 | **PAT-02** | 新颖性检索 memo | IP/专利 | PM | memo PDF/MD 归档 | **6/18** |
| 9 | **COMP-06** | 律师复审表（填表） | IP 合规专家 | PM | 申请表 PDF 草稿 | **6/20** |
| 10 | **COMP-07** | 范围扫描（已完成） | IP | BE | 维持 `comp-07-scope-scan PASS` | ✅ |
| 11 | **QA-02** | cert:gate 每周五 | QA | 前端 | `certification-gate-admin-latest.json` | **每周五** |
| 12 | **PM-07** | 统计+分配+周报 | 📋 产品经理 | 文档 | 本文 + tracker 更新 | **每周一** |
| 13 | **DOC-02** | 总表/索引 sync | 📝 文档 | PM | 三文档一致 | **每周一** |

### Sprint-R1 · 按部门认领（一人一眼）

| 部门/角色 | 本周必须交付 | ID |
|-----------|--------------|-----|
| **架构** | preflight 0 fail + HTTPS compose 记录 | ARCH-01, ARCH-04 |
| **QA** | 周五 cert:gate 绿 + Locust 冒烟通过 | QA-02, QA-04 |
| **前端** | Formily 真接入（BJ-01） | BJ-01, FE-11+ |
| **页面搭建** | useTable 734 + CRUD 3 页（BJ-02/03） | BJ-02, BJ-03 |
| **后端** | 60 页导出脚本终验 | BE-06 |
| **IP/专利** | 检索 memo + 律师表草稿 | PAT-02, COMP-06 |
| **PM/文档** | 本分配表 + 周一统计 | PM-07, DOC-02 |
| **SaaS 专家** | BJ-01 试点验收 + 五问抽检 | 顾问 |
| **视觉/营销** | **R1 无新编码任务** | — |

---

### Sprint-S2 · 人类/签字批次（7/1 – 7/25 · 暂不启动）

| 序 | ID | 任务 | **主责** | 截止 |
|----|-----|------|----------|------|
| H-01 | PM-03 | 送检脚本 v2 彩排 30min | PM | 7/15 |
| H-02 | PM-04 | L3 六项 + signoff.json | PM | 7/18 |
| H-03 | PM-05 | 手册 PDF | PM + 营销 | 7/20 |
| H-04 | PM-06 | Owner Blocked 书面 | PM → Owner | 滚动 |
| H-05 | PM-08 | 阶段 Gate 签字 | PM + 各部门 | 各 Gate |
| H-06 | MKT-06 | 手册正文人类撰写 | 营销 | 7/18 |
| H-07 | COMP-02 | 60 页研发签字 | BE + FE | 6/18→S2 |
| H-08 | COMP-03 | 人类说明书 | 营销 + IP | 6/22→S2 |
| H-09 | COMP-05 | 手抄承诺提交 | 经办人 | 7/6 |
| H-10 | COMP-06 | 律师复审签字 | IP | 7/10 |
| H-11 | COMP-07 | 冲突复核签字 | IP + BE | 7/28 |
| H-12 | IP-02 | 禁止清单签字 | IP | 6/18→S2 |
| H-13 | IP-03 | 手抄承诺培训 | IP | 7/1 |
| H-14 | PAT-04 | 发明人 Owner 签字 | Owner | 7/10 |
| H-15 | PAT-05 | 正式专利申请 | 专利 | 7/25 |
| H-16 | PAT-06 | 软著②冲突复核 | IP | 7/28 |
| H-17 | BE-06 | readability 签字 | BE | S2 |

---

### Sprint-MOD · 业务链缺口（与 ARCH-04 并行 · 6/10 – 6/30）

> 来源：`module-progress.json` · 七步闭环 · 不挡 Admin 百家，但挡 **实机送检**

| ID | 模块 | 缺口 | **主责** | 交付 |
|----|------|------|----------|------|
| MOD-01 | 独立域/SSL | 实机 DNS+证书 | 架构 | 1 个 HTTPS 演示域 |
| MOD-02 | 询盘 IM | 企微/抖音生产密钥 | 后端 | 联调记录 |
| MOD-03 | 40 平台 | PM 正式表签字 | PM | 签字表 |
| MOD-04 | 运维 | 七步实机录屏 | QA + PM | 录屏 1 套 |
| MOD-05 | 商业飞轮 | alembic 025/026 生产 | 后端 | migration 绿 |
| MOD-06 | 出海计 App | 商店上架包 | 前端 App | 包 + 清单 |
| MOD-07 | 贸易情报 | PM 矩阵签字 | PM | 矩阵签字 |
| MOD-08 | PM/QA | 5+5 平台 + HTTPS 域 | PM + Owner | blocker 清零 |

---

## 三、L2 工程增量（ENG · 已交付归档）

| ID | 交付 | 挂靠 L1 | 状态 |
|----|------|---------|------|
| ENG-01 | onboarding 六步真实进度 | BE-03 | ✅ |
| ENG-02 | Lab Plan Gate | BE-04 / SAAS-03 | ✅ |
| ENG-03 | Agent 辖区 inbox | Agent 五栏 | ✅ |
| ENG-04 | FE-11 BFF 草稿 | FE-11 | ✅ |
| ENG-05 | COMP-07 扫描脚本 | COMP-07 | ✅ |
| ENG-06 | QA-04 Locust 冒烟 | QA-04 | ✅ |
| ENG-07 | gen-crud-from-openapi | → BJ-03 | ✅ |
| ENG-08 | cert:gate P0/P1/P2=0 | QA-02 | ✅ |

---

## 四、L3 百家收尾（BJ · ECC R4 分配）

| ID | 源库 | 任务 | 主责 | 验收 |
|----|------|------|------|------|
| **BJ-01** | Formily antdv-x3 | site-editor 真 Schema 表单 | 前端 | SaaS 专家签字 1 页 |
| **BJ-02** | Art Edge 734 | useYoudingTable 全能力 | 页面搭建 | 列拖拽+搜索+分页单测 |
| **BJ-03** | Vue Admin Better | OpenAPI CRUD Top12 至少 3 页 | 页面搭建 | cert:gate 不回归 |

**百家组装进度**：7/10 → **R1 完成后目标 10/10**

---

## 五、Gate 与分配对齐

| Gate | 目标日 | R1 必须完成项 | 负责 |
|------|--------|---------------|------|
| **W2 补完** | 6/23 | BJ-01~03 · BE-06 脚本 | FE/PAGE/BE |
| **CERT 前置** | 7/25 | ARCH-01 · ARCH-04 · QA-04 | ARCH/QA |
| **S2** | 7/21 | H-01~17 批次 | PM 牵头 |
| **S0** | — | 已过 | — |

---

## 六、ECC 角色 ↔ 任务速查

| ECC 角色 | Sprint-R1 任务 |
|----------|----------------|
| 🎖 架构指挥官 | ARCH-01, ARCH-04, MOD-01 |
| 🧱 前端架构师 | BJ-01, cert:gate 配合 |
| 🔧 后台页面搭建 | BJ-02, BJ-03 |
| 🗄 后端架构师 | BE-06, MOD-05 |
| 🔒 安全专家 | ARCH-04 HTTPS 审查 |
| 📋 产品经理 | PM-07, MOD-03/07/08, S2 编排 |
| 🚀 SaaS 专家 | BJ-01 验收 · 五问 |
| 🎨 视觉 | R1  standby · S2 截图重拍配合 |
| 📣 营销 | S2: MKT-06 |
| IP/专利 | PAT-02, COMP-06, S2 签字链 |
| QA | QA-02, QA-04, MOD-04 |
| 📝 文档 | DOC-02 |

---

## 七、文档地图（统计+分配+会议）

```text
pm-swarm-parallel-charter.md       ← 蜂群宪章（永久 · Lane 边界）
pm-dev-progress-bars.md            ← 开发进度条（仅未完成 · standup 用）
pm-dev-task-progress.json          ← 进度数据源（改 pct 后跑 render 脚本）
pm-task-allocation-20260602.md     ← 分配
pm-task-statistics-20260602.md     ← 统计数字
pm-master-schedule-kpi-20260601.md ← 79 ID 明细
ecc-meeting-saas-repo-master-index.md ← 会议/SaaS/15仓库
ecc-delivery-tracker.md            ← 看板（内嵌进度条）
```

---

## 八、PM 下达指令（2026-06-02 · 永久）

1. **蜂群并行** — 各 Lane 按 §二泳道表 **同时推进**；standup 报 **Lane + ID + pct**，不按人串行排队。  
2. **质量四原则（永久）** — 代码质量高 · 思路清晰 · 逻辑严谨 · 边界清；PR 须附四行摘要（见宪章 §五）。  
3. **开发任务以进度条展示** — 仅未完成项：[`pm-dev-progress-bars.md`](./pm-dev-progress-bars.md)（数据源 `pm-dev-task-progress.json`，跑 `scripts/render-dev-progress-bars.py` 刷新）。  
4. **即日起 standup 只报 Sprint-R1** — 各部门报 **Lane + ID + 进度条 %**。  
5. **各部门主责** 于 **6/3 10:00** 前在 tracker 确认认领。  
6. **SaaS 专家** 对 BJ-01 有否决权。  
7. **Owner** 仅需：PM-06 · MOD-01 HTTPS 域 · S2 H-14。

---

*ECC 产品经理 · 全量统计与分配 v2 · 蜂群并行 · 2026-06-02*
