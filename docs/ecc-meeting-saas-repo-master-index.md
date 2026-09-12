# ECC 会议 · SaaS 专家 · 百家仓库 — 总索引（PM 维护）

> **统计人**：ECC 产品经理  
> **更新**：2026-05-31  
> **用途**：回答「会议纪要在哪？」「SaaS 专家说的开发条件和进程呢？」「我发的仓库链接集成的功能呢？」  
> **结论**：**没有删除**；此前 tracker 改成批次 changelog + 任务统计，**没链回本文档链**，看起来像丢了。

---

## 一、ECC 会议记录（按时间 · 全部在仓内）

| 轮次 | 文档 | 日期 | 核心决议 |
|------|------|------|----------|
| **二轮** | [`ecc-round2-meeting-minutes-20260531.md`](./ecc-round2-meeting-minutes-20260531.md) | 5/31 | 8 套开源 + **Vben 唯一壳** + UAC BFF 契约；百家组装矩阵 |
| **三轮** | [`ecc-round3-meeting-minutes-20260601.md`](./ecc-round3-meeting-minutes-20260601.md) | 6/1 | Phase 0 通过；**99 汇总 = Wave 1 编码门禁**；W1-2→W1-1→W1-3 顺序 |
| **四轮** | [`ecc-round4-meeting-minutes-saas-composite-20260601.md`](./ecc-round4-meeting-minutes-saas-composite-20260601.md) | 6/1 | **集百家所长 × SaaS 改造**；增补 SaaS 专家席；六方案 A–F |
| **SaaS 内训** | [`ecc-saas-expert-training-20260601.md`](./ecc-saas-expert-training-20260601.md) | 6/1 | 什么是 SaaS；四层蛋糕 L1–L4；**与抖音高级感差距** |
| **全员最优** | [`ecc-optimal-saas-masterplan-20260601.md`](./ecc-optimal-saas-masterplan-20260601.md) | 6/1 | 90 天总纲；**SaaS 专家三条铁律**；视觉/营销强制交付 |
| **PM 汇报** | [`pm-executive-report-summary-20260601.md`](./pm-executive-report-summary-20260601.md) | 6/1 | Owner 向；ECC 决策链一览；三轨 90 天 |
| **Design Skill 全员宣贯** | [`meetings/ECC-DESIGN-SKILL-ALL-HANDS-CONVENE.md`](./meetings/ECC-DESIGN-SKILL-ALL-HANDS-CONVENE.md) | 待召开 | **184+38+研发强制对齐**；Skill 栈 + 四屏门控 + 独立线 UI；会务包见独立线 `02-ECC-ALL-HANDS` |
| **登录 Glass + 四门户 · PM×设计×营销** | [`meetings/ECC-LOGIN-GLASS-PORTAL-PM-DESIGN-MKT.md`](./meetings/ECC-LOGIN-GLASS-PORTAL-PM-DESIGN-MKT.md) | 执行中 | 玻璃拟态 + 四角色欢迎语 + RACI + 7 天清单 |
| **联合评审会议通知** | [`meetings/ECC-LOGIN-GLASS-PORTAL-CONVENE-NOTICE.md`](./meetings/ECC-LOGIN-GLASS-PORTAL-CONVENE-NOTICE.md) | 待召开 | 设计/营销签字用 |
| **媒体工厂 ECC** | [`meetings/MEDIA-FACTORY-STORAGE-ECC-MINUTES.md`](./meetings/MEDIA-FACTORY-STORAGE-ECC-MINUTES.md) | — | 存储/视频云专项 |
| **周报** | [`ecc-weekly-report-latest.md`](./ecc-weekly-report-latest.md) | 5/31 | 灯色 + 风险（待 PM 续更） |

**开源深读 / 编码门禁（三轮主输入）**

| 文档 | 作用 |
|------|------|
| [`open-source-audit/99-synthesis-for-uac.md`](./open-source-audit/99-synthesis-for-uac.md) | **百家汇总 v1 · Wave 解锁依据** |
| [`open-source-audit/98-efficiency-paradigms-by-vendor.md`](./open-source-audit/98-efficiency-paradigms-by-vendor.md) | 各库效率范式 |
| [`open-source-audit/00-repo-link-inventory.md`](./open-source-audit/00-repo-link-inventory.md) | **你发的 15 个 URL 总清单** |
| [`youding-admin-composite-blueprint.md`](./youding-admin-composite-blueprint.md) | UAC 1.0 组装蓝图 |

---

## 二、SaaS 专家 · 开发条件（执行约束 · 不是丢了）

来源：[`ecc-optimal-saas-masterplan-20260601.md`](./ecc-optimal-saas-masterplan-20260601.md) · [`ecc-saas-expert-training-20260601.md`](./ecc-saas-expert-training-20260601.md)

### 2.1 三条铁律（违反 = SaaS 专家否决）

1. **租户不见 Stub** — Hide / Plan Gate / Lab；无产品签字不上线。  
2. **Client 一级菜单永远 ≤5** — 获客 | 发品 | 履约 | 账户（+ 财旺 FAB）。  
3. **先 L3/L4 再特效** — 未完成激活层 + 四支柱前，禁止全站 glass 讨论。

### 2.2 North Star（30 秒三问）

> 我今天该干什么？ · 店运转正常吗？ · 套餐还够用吗？

### 2.3 六类产品部件（必交付感知）

| # | 部件 | 文档要求 | **现网落地** |
|---|------|----------|--------------|
| 1 | 工作区身份 | Header + 租户品牌 | ✅ `YdWorkspaceHeader` · BFF `user/info` |
| 2 | 激活向导 | Onboarding 卡 | ✅ `YdOnboardingCard` + **六步真实进度**（`onboarding_progress_service`） |
| 3 | 任务导航 | 四支柱 ≤5 | ✅ BFF seed + `client/layout` |
| 4 | 用量/套餐 | 用量条 + billing | ✅ `YdUsageMeter` · Plan Gate |
| 5 | 工作队列 | inbox | ✅ 三队列 PAGE-02 · Agent `/agent/clients` inbox |
| 6 | 升级动线 | Plan Gate CTA | ✅ `plan-gate.vue` + BE-04 |

### 2.4 改造顺序（不得打乱）

```text
W1  可信+壳     Stub Hide · Vben+BFF · backend 菜单 · 禁 emoji
W2  像 SaaS     四支柱 · Bento Dashboard · TenantLogin · 三队列
W3  可扩展      Formily 1 页 · Plan Gate · OpenAPI CRUD · 字典
W3+ 对外        marketing · 投流与 Admin 同源
```

### 2.5 阶段验收（SaaS 五问）

| Gate | 文档 |
|------|------|
| S0 | [`saas-gate-s0-five-questions.md`](./saas-gate-s0-five-questions.md) |
| W2 | [`saas-gate-w2-five-questions.md`](./saas-gate-w2-five-questions.md) |

---

## 三、SaaS 专家 · 开发进程（2026-06-02 实态）

| Wave | ECC/SaaS 要求 | 进程 | 说明 |
|------|---------------|------|------|
| **Phase 0** | 12 库 clone + 深读 | ✅ **12/12 clone** | `_ref/clone-manifest.json` |
| **W1** | Vben + BFF + Stub | ✅ | `frontend/admin-vben` · `backend/app/api/v1/admin_bff/` |
| **W2** | Bento · Login · 四支柱 · 三队列 | ✅ | `client/dashboard.vue` · kit 组件 · PAGE-01/02 |
| **W3** | Formily · Plan Gate · CRUD gen | ✅ **约 95%** | Formily `YdFormilyForm` · Plan Gate ✅ · **12 页 CRUD** + `generated-crud-routes.ts` |
| **S2 人类** | 手册 · 彩排 · 签字 | ⏳ 置后 | 见 [`pm-task-statistics-20260602.md`](./pm-task-statistics-20260602.md) §五 |
| **CERT** | staging · 72h | 🔄 | **R1-dev-gate 全绿** · 72h 待 HTTPS 域 |

**Sprint-R1 交付索引（2026-06-02 第七轮）**

| ID | 交付物 |
|----|--------|
| 全链 | **`run-r1-dev-gate.ps1` 15 步 ALL PASS** · `r1-dev-gate-latest.json` |
| QA-04 | `validate-qa-04-locust-bundle.py` |
| MOD-04/08 | 录屏归档目录 · `mod-08-owner-blockers.json` |
| PAT-02 | `export-pat-02-handoff-bundle.py` |
| ARCH-01 | `validate-arch-01-preflight.py`（快速读报告） |

**易误导的旧数据（已过时，勿信）**

| 文件 | 旧显示 | 实际 |
|------|--------|------|
| `module-progress.json` → `admin-overhaul` | 2/10 | **9/10**（差 SaaS 正式签字） |
| `00-repo-link-inventory.md` §一 | 5/12 clone | **12/12**（manifest 2026-05-31 已齐） |
| 本文 §三 W3 | 约 70% | **约 95%**（BJ-01~03 代码完成） |

---

## 四、你发的仓库链接 → 集百家所长 · 落地对照

**完整 URL 表**：[`open-source-audit/00-repo-link-inventory.md`](./open-source-audit/00-repo-link-inventory.md)

| # | 源库 | 本地 `_ref/` | ECC 要抄什么 | **优丁落地路径** | 状态 |
|---|------|--------------|--------------|------------------|------|
| 1 | **Vben 5** | ✅ `vue-vben-admin-full` | Layout、backend 菜单 | `frontend/admin-vben/` | ✅ fork + BFF 接线 |
| 2 | **Art Edge** | ✅ | 734 行 useTable、列拖拽 | `useYoudingTable.ts` · 三队列页 | ✅ 列拖拽+搜索+单测 |
| 3 | **Soybean** | ✅ | API 分层、refresh 队列 | `frontend/admin/src/api/admin-bff.ts` | ✅ |
| 4 | **Element Admin** | ✅ | meta 白名单、动态路由 | `stubVisibility.ts` · router guard | ✅ |
| 5 | **Better** | ✅ | CRUD 三件套 / OpenAPI 生成 | `gen-crud-from-openapi.mjs` · **12 页** | ✅ |
| 6 | **Naive Admin** | ✅ | 分屏 Login、留白 Dashboard | TenantLogin · Bento dashboard 参考 | 🔄 |
| 7 | **Pure Admin** | ✅ | Mock、移动侧栏 | `client/layout` 响应式侧栏 | 🔄 |
| 8 | **RuoYi-Soybean** | ✅ | 字典/审计/套餐清单 | BE-05 `plan_features` · 路线图 | 🔄 非 Java 搬迁 |
| 9 | **Formily** | ✅ formily + antdv-x3 | Schema 复杂表单 | `YdFormilyForm` · `site-editor-lab` | ✅ BFF+五问（待签字） |
| 10 | **daisyUI** | ✅ | 营销语义 class | `frontend/marketing/` | ✅ 骨架 |
| 11 | **HTMLrev** | 站点非 git | Landing 区块 | marketing 选型 | 🔄 |
| 12 | **Art Pro** | ✅ | 上游视觉 | 参考 diff Edge | 📖 只读 |

**四轮会议「SaaS 能力矩阵」→ 代码映射**（摘自 R4 §二）

| R4 方案 | 百家来源 | 落地 |
|---------|----------|------|
| A JTBD 导航 | Vben + 四壳文档 | BFF CLIENT seed · FE-07 |
| B 激活层 | Art + Naive + SaaS 专家 | YdOnboarding / TodayQueue / UsageMeter |
| C 工作区身份 | Art Edge 登录 + Naive 分屏 | TenantLogin · YdWorkspaceHeader |
| D 三队列 inbox | Art useTable | PAGE-02 三队列 |
| E Plan Gate | RuoYi 字典 + SaaS | BE-04 · `plan-gate.vue` |
| F 对外同源 | daisyUI/HTMLrev | MKT-05 marketing |

---

## 五、还没做完的「百家能力」（2026-06-02 更新）

| 缺口 | ECC 出处 | 下一步 |
|------|----------|--------|
| SaaS **正式签字** | BJ-01 五问 | `bj-01-formily-saas-five-questions.md` 经办签字 → 10/10 |
| RuoYi **字典/审计** UI | 99 汇总 W3 | BFF dict 扩展 + 超管页 |
| Pure **移动看板**完整版 | R4 · W2 | Client 移动 3 指标摘要 |
| 浅读 **04–09** 审计笔记 | PHASE0 | 非阻塞，IP 计划补 2h/库 |

**已完成（原 §五 缺口）**：Formily site-editor · Art table 三队列 · Better CRUD 12 页。

---

## 五-b、出海计 App（MOD-06 · DOC-02 sync）

| 项 | 路径 / 说明 | 状态 |
|----|-------------|------|
| 模块进度 | `module-progress.json` → `chuhaiji-app` **9/10** | 🔄 |
| 缺口 | 商店上架实机包 | Owner/App 提审 |
| 与 Admin 关系 | 独立 Capacitor 包，共用 BFF API | 构建链 ✅ |

---

## 六、文档怎么读（推荐顺序）

```text
1. 本文（总索引）
2. ecc-round4-meeting-minutes-saas-composite-20260601.md（集百家 × SaaS 六方案）
3. ecc-saas-expert-training-20260601.md（开发条件 + 差距）
4. open-source-audit/00-repo-link-inventory.md（你的 15 个链接）
5. open-source-audit/99-synthesis-for-uac.md（编码门禁）
6. pm-task-statistics-20260602.md（79 任务统计）
7. ecc-delivery-tracker.md（本周 3 件事）
8. 思维导图-优丁SaaS改造全员对齐.md（全员一图）
```

---

## 七、PM 承诺（防再丢）

1. **任何 tracker 改写**必须链回 **本文 §一–§四**。  
2. **每周一** PM-07 同步：`module-progress.json` 的 `admin-overhaul` 与 §四表一致。  
3. **研发 standup** 先报 §四「状态 🔄/⏳」项，再报 S2 人类项。  
4. Owner 补 **琢磨先生视频 URL** → 写入 `docs/design/douyin-b端审美对照.md`（可选）。

---

*ECC 产品经理 · 会议/SaaS/百家 总索引 v1 · 2026-06-02*
