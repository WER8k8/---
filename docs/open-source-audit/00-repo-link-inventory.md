# 00 · 用户发过的仓库/链接总清单（含遗漏核对）

> **更新**：2026-06-01  
> **用途**：回答「有没有漏掉我发过的链接」；各库**最值得抄什么**；与 `_ref/` 克隆状态对照  
> **深读索引**：[98 效率范式](./98-efficiency-paradigms-by-vendor.md) · [99 汇总门禁](./99-synthesis-for-uac.md)

---

## 一、结论（先读）

| 维度 | 状态 |
|------|------|
| **战略层解读** | 你发过的 **15 个 URL/站点** 均已写入 ECC/PM/开源审计文档 |
| **本地 `_ref/` 克隆** | **12/12 已 clone**（见 `_ref/clone-manifest.json`） |
| **浅读审计 04–09、14** | **未完成**（Element / Naive / Pure / Art Pro / HTMLrev 精选） |
| **琢磨先生视频** | **无具体 URL 存档**；设计原则已提炼进 SaaS/三壳文档（见 §四） |
| **DeerFlow** | 项目内 UBrain 对标引用，**非 Admin 换皮源库** |

---

## 二、完整链接表（按你发送顺序 + 后续补充）

### A. Admin 模板（8 套 + RuoYi）

| # | 名称 | 链接 | 深读文档 | 本地 `_ref/` | **最值得抄的「优秀作品」** |
|---|------|------|----------|--------------|---------------------------|
| 1 | **Vue Vben Admin 5** | https://github.com/vbenjs/vue-vben-admin | [01](./01-vben-web-antd.md) | ✅ `vue-vben-admin-full` | `web-antd` Layout、多标签、`accessMode:backend` 动态路由、按钮权限、`preferences` 主题 |
| 2 | **RuoYi-Plus-Soybean** | https://github.com/m-xlsea/ruoyi-plus-soybean | 99 对照 | ✅ | Java **代码生成器**、租户套餐/字典/审计 **能力清单**（不搬 Java） |
| 3 | **Vue Element Admin** | https://github.com/PanJiaChen/vue-element-admin | ⏳ 04 | ❌ 待 clone | `generateRoutes(roles)`、meta 白名单、`v-permission` — **权限流程鼻祖** |
| 4 | **Vue-Admin-Better** | https://github.com/zxwk1998/vue-admin-better | [06](./06-vue-admin-better.md) | ❌ | CRUD **三件套**命名、`mock/controller` 热扫描 — 对标自建 OpenAPI 生成器 |
| 5 | **Pure Admin** | https://gitee.com/yiming_chang/vue-pure-admin | ⏳ 08 | ❌ | Mock 生态、移动侧栏、schema-form **demo 超市**（抄一页上一页） |
| 6 | **Soybean Admin** | https://github.com/soybeanjs/soybean-admin | [03](./03-soybean-admin.md) | ❌ | API 三层 + **refresh 队列**、Elegant Router 规范、`0000` 业务码约定 |
| 7 | **Naive UI Admin** | https://github.com/jekip/naive-ui-admin | ⏳ 09 | ❌ | **分屏 Login**、留白 Dashboard、空状态 — **只抄布局不抄 Naive 库** |
| 8 | **Art Design Pro** | https://github.com/Daymychen/art-design-pro | ⏳ 07 | ❌ | 上游视觉规范、统计卡密度（Edge 的上游 diff） |
| 9 | **Art Design Pro Edge** | https://github.com/ChnMig/art-design-pro-edge | [02](./02-art-design-pro-edge.md) | ⚠️ 曾浅 clone，manifest 未列 | **734 行 useTable**、ArtSearchBar、列拖拽、多租户 login→menu 链 |

### B. 表单 / 营销扩展（你后补的 4 项）

| # | 名称 | 链接 | 深读文档 | 本地 `_ref/` | **最值得抄** |
|---|------|------|----------|--------------|-------------|
| 10 | **Formily 核心** | https://github.com/alibaba/formily | [13](./13-formily-antdv-x3.md) | ✅ | JSON Schema 驱动、`FormStep`/`ArrayTable` — **1 页试点** |
| 11 | **Formily antdv-x3** | https://github.com/formilyjs/antdv-x3 | [13](./13-formily-antdv-x3.md) | ✅ | Ant Design Vue 3 组件映射 |
| 12 | **Formily 文档** | https://formilyjs.org/ | — | — | 协议范式、联动 side effect |
| 13 | **Designable** | https://designable-antd.formilyjs.org/ | — | — | 拖拽出 Schema（**W3 评估，不上生产设计器**） |
| 14 | **daisyUI** | https://github.com/saadeghi/daisyui | ⏳ 14 | ✅ | `btn`/`card`/`hero` 语义 class — **仅 marketing/Landing** |
| 15 | **HTMLrev** | https://htmlrev.com/ | ⏳ 15 | —（站点非 git） | Tailwind Landing 区块；**禁止**整页 iframe 进 Admin |

### C. 项目内引用（非你发的 Admin 清单，但文档出现过）

| 名称 | 链接 | 角色 |
|------|------|------|
| **DeerFlow** | https://github.com/bytedance/deer-flow | UBrain 商业 OS **研究对标**；不进软著 60 页主体 |
| **Vben 演示站** | https://vben.pro/ | 视觉/交互参考，非代码源 |
| **Art Design Pro X** | 商业闭源 | **不在清单** — 用 Edge MIT 版替代 |

---

## 三、遗漏核对清单

### ✅ 已覆盖（文档中有解读）

- 六套 MIT 模板清单（Vben / Element / Better / Pure / Soybean / Naive）
- Art Pro + Art Edge（分两次发送）
- RuoYi-Plus-Soybean（绑在 #1 消息里）
- daisyUI + Formily + formilyjs.org + HTMLrev（2026-05-31 补充）

### ⚠️ 部分覆盖 / 待补实

| 遗漏项 | 说明 | 下一步 |
|--------|------|--------|
| `_ref/` 仅 5/12 clone | 2026-05-31 旧数据 | **已 12/12** · 见 manifest |
| **审计 04–09、14–15** | PHASE0 标 ⏳ | IP-UX 计划 W1 内补浅读（各 2h） |
| **琢磨先生具体视频 URL** | 对话中仅引用「抖音 B 端切片审美」 | 见 §四；Owner 可补 3 条链接进 `docs/design/douyin-b端审美对照.md` |
| **专利轨道** | 交底书已有，未进 PM 总表 | 见 `pm-one-shot-ip-ux-masterplan.md` PAT-01~06 |
| **软著专职专家角色** | 任务在 COMP-01~06，无独立 ECC 席位 | 新增 `ip-compliance-expert` |

### ❌ 不在「Admin 百家」范围（刻意不纳入）

- Art Design Pro **X**（商业版，无 GitHub 源）
- 整库 Element / Naive 进生产（与 Vben 底座冲突）

---

## 四、琢磨先生 / 抖音 B 端审美（无视频 URL 时的可执行对照）

> 来源：ECC SaaS 培训、三壳 remediation；**未存档具体抖音链接**。

| 琢磨类批评 | 现网反例 | 目标（Linear/飞书/Stripe 风） | 对应任务 |
|------------|----------|-------------------------------|----------|
| emoji 菜单像玩具 | Client 15 项 emoji 侧栏 | Lucide + ≤5 一级项 | FE-06, SA-K3 |
| 彩虹渐变 KPI | Agent `performance.vue` | 白底 + 细边框 + 单强调色 | FE-04, UX-02 |
| 营销 hero 进后台 | Platform `hierarchy` glass | 标准列表页 | FE-05, UX-03 |
| 角色串台 | Agent→`/admin/aggregation` | 壳隔离零链接 | FE-03 |
| 半成品菜单丢人 | 80+ Stub/lab | Hide/PlanGate/Lab | PM-01, SAAS-01 |
| 3 秒不懂干啥 | 234 路由无北极星 | Bento「今日任务」 | FE-07~08, bento-spec |

**Owner 可选**：发 3 条最认同的琢磨先生视频链接 → 写入审美对照表，视觉部按帧截图进 UX-07。

---

## 五、各库 → 优丁落地文件（速查）

| 源 | 落地 |
|----|------|
| Vben | `frontend/admin-vben`（W1 fork） |
| Art Edge | `youding-admin-kit/composables/useYoudingTable.ts`（W2 扩至 734 行能力） |
| Soybean | `backend/app/api/v1/admin_bff/` 契约 + API 命名 |
| Better | `scripts/gen-crud-from-openapi.mjs`（W3） |
| Formily | site-editor **1 页试点**（W3） |
| Naive/Pure | `TenantLogin.vue`、`YdEmpty` 布局参考 |
| daisyUI/HTMLrev | `frontend/marketing`（W3） |
| RuoYi | FastAPI 字典/审计 **路线图**，非代码搬迁 |

---

*维护：文档部 · 克隆状态以 `_ref/clone-manifest.json` 为准，每周一 sync*
