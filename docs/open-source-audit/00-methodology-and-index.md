# 开源深读审计 · 方法论与总索引

> **原则**：好饭不怕晚 — **先逐库深读、记录、汇总，再写生产代码**。  
> **禁止**：未审计就 clone Vben、未对照就改 270+ 页。  
> **权威开发仓**：`Desktop/上线网站`

---

## 一、为什么要「每一行都解读」

| 浅读（此前） | 深读（现在起） |
|--------------|----------------|
| README + star 数 + 技术栈标签 | 入口文件 → hooks → 典型页 → API 契约 |
| 「借 useTable」 | 734 行 `useTable.ts` + `tableCache` + 列拖拽 + 分页双轨 |
| 「用 Formily」 | `@formily/antdv-x3` 维护状态、Designable 协议、与 BFF 字段映射 |
| 文档里写「集百家所长」 | **审计表**：每个模块 Yes/Partial/No + 落地文件路径 |

**产出物**：每个源库一份 `docs/open-source-audit/NN-*.md`，全部汇总到 `docs/open-source-audit/99-synthesis-for-uac.md` 后再开 Wave 1 编码。

---

## 二、单库审计模板（每库必填）

```markdown
# NN · 库名

## 元信息
- URL / clone 路径 / 版本或 commit / 文件数 / UI 栈

## 目录地图（一级）
## 核心模块表（路径 | 功能 | 导出 | 依赖）
## UI 规则与约定（从代码提取，非 README）
## 权限 / 路由 / 登录 / 菜单 数据流
## 拖拽与低代码相关代码位置
## Ant Design Vue 可抽取性（Yes/Partial/No + 原因）
## 优丁落地建议（kit 文件 / BFF / Wave）
## 风险与禁止抽取项
## 待深读文件队列（下一批）
```

---

## 三、审计顺序（按 ROI × 与 UAC 耦合度）

| 序 | 库 | URL | 本地副本 | 状态 | 审计文档 |
|----|-----|-----|----------|------|----------|
| 0 | 方法论 | — | — | ✅ | 本文 |
| 1 | **Art Design Pro Edge** | [ChnMig/art-design-pro-edge](https://github.com/ChnMig/art-design-pro-edge) | `_ref/art-design-pro-edge` | ✅ **首轮完成** | [02-art-design-pro-edge.md](./02-art-design-pro-edge.md) |
| 2 | **Vue Vben Admin 5** | [vbenjs/vue-vben-admin](https://github.com/vbenjs/vue-vben-admin) | 待 shallow clone → `_ref/vue-vben-admin` | ⏳ 待审计 | `01-vben-web-antd.md` |
| 3 | **优丁现网 admin** | — | `frontend/admin` | ⏳ 待审计 | `10-youding-admin-current.md` |
| 4 | **优丁 Admin BFF** | — | `backend/app/api/v1/admin_bff` | ⏳ 待审计 | `11-youding-admin-bff.md` |
| 5 | **youding-admin-kit** | — | `frontend/youding-admin-kit` | ⏳ 待审计 | `12-youding-admin-kit-gap.md` |
| 6 | Soybean Admin | [soybeanjs/soybean-admin](https://github.com/soybeanjs/soybean-admin) | 待 clone | ⏳ | `03-soybean-admin.md` |
| 7 | Art Design Pro 上游 | [Daymychen/art-design-pro](https://github.com/Daymychen/art-design-pro) | 待 clone | ⏳ | `04-art-design-pro-upstream.md` |
| 8 | Vue Element Admin | [PanJiaChen/vue-element-admin](https://github.com/PanJiaChen/vue-element-admin) | 待 clone | ⏳ | `05-vue-element-admin.md` |
| 9 | Vue-Admin-Better | [zxwk1998/vue-admin-better](https://github.com/zxwk1998/vue-admin-better) | 待 clone | ⏳ | `06-vue-admin-better.md` |
| 10 | Pure Admin | [vue-pure-admin](https://gitee.com/yiming_chang/vue-pure-admin) | 待 clone | ⏳ | `07-pure-admin.md` |
| 11 | Naive UI Admin | [jekip/naive-ui-admin](https://github.com/jekip/naive-ui-admin) | 待 clone | ⏳ | `08-naive-ui-admin.md` |
| 12 | RuoYi-Plus-Soybean | [m-xlsea/ruoyi-plus-soybean](https://github.com/m-xlsea/ruoyi-plus-soybean) | 待 clone | ⏳ | `09-ruoyi-plus-soybean.md` |
| 13 | **Formily** | [alibaba/formily](https://github.com/alibaba/formily) + [antdv-x3](https://github.com/formilyjs/antdv-x3) | 待 clone | ⏳ | `13-formily-designable.md` |
| 14 | **daisyUI** | [saadeghi/daisyui](https://github.com/saadeghi/daisyui) | npm 源码 | ⏳ | `14-daisyui-marketing.md` |
| 15 | **HTMLrev** | [htmlrev.com](https://htmlrev.com/) | 在线模板 | ⏳ | `15-htmlrev-landing-picks.md` |
| 16 | **论坛/Q&A Sidecar** | [apache/answer](https://github.com/apache/answer) 等 | `_ref/answer` 等 | ✅ FORUM-01~04 已落地 | [16-forum-community-sidecar.md](./16-forum-community-sidecar.md) |
| 17 | **租户 L-Pro 店面** | GrooveShop/Nuxtless/sales-portal 等 | `_ref/` 见 clone 脚本 | ⏳ W0 骨架 | [17-tenant-premium-storefront.md](./17-tenant-premium-storefront.md) |
| 99 | **汇总合成 UAC** | — | — | ⏳ Wave1 前 | `99-synthesis-for-uac.md` |

---

## 四、深读操作规范（执行时）

1. **Shallow clone** 到 `_ref/<repo-name>/`，记录 commit hash。  
2. **入口**：`package.json` → `src/main.ts` → `router` → `store` → 典型 CRUD 页。  
3. **逐文件记录**：用审计模板填表，**不复制整文件进 doc**（只记路径 + 行为 + 行号范围）。  
4. **UI 规则**：从 SCSS/class 名/formatter 空值 `--`/分页 layout 等 **代码**提取。  
5. **对照优丁**：每一模块标注「现网有无 / kit 有无 / 差距」。  
6. **禁止边读边改生产代码**；发现可抽取代码先记 `pending-extracts.jsonl`。  
7. 单库审计 **≥2h** 有效深读后再标记 ✅；README 级不算完成。

---

## 五、编码门禁（Wave 1 解锁条件）

全部满足才允许 `git clone` Vben 到 `frontend/admin-vben`：

- [ ] `01-vben-web-antd.md` 完成（access、layouts、preferences、web-antd 入口）  
- [ ] `02-art-design-pro-edge.md` 完成 ✅  
- [ ] `10-youding-admin-current.md` 完成（234 路由分类：主链/Stub/实验室）  
- [ ] `11-youding-admin-bff.md` 完成（与 Edge 契约 diff）  
- [ ] `12-youding-admin-kit-gap.md` 完成（kit 与 Art 完整 useTable 差距清单）  
- [ ] `99-synthesis-for-uac.md` v1 发布（抽取优先级 + 文件级任务）  

---

## 六、首轮发现（Art Edge 深读摘要）

> 详见 [02-art-design-pro-edge.md](./02-art-design-pro-edge.md)

| 发现 | 对优丁含义 |
|------|------------|
| `useTable.ts` **734 行** + LRU 缓存 + 5 种刷新策略 | 现 kit 仅简化版，**差距大** |
| 列拖拽在 `art-table-header` + `vue-draggable-plus` | 模块化拖拽第一优先抽取 |
| 分页 **current/size** vs API **page/pageSize** 双轨 | BFF/kit 必须统一 adapter |
| 多租户登录完整链：tenant_code → login → info → menu | 与 UAC BFF 设计一致，可对照实现 |
| Element Plus 深度绑定 | UI 层 Partial；**逻辑层 Yes** |

---

## 七、相关文档

- UAC 蓝图：`docs/youding-admin-composite-blueprint.md`  
- ECC 第二轮纪要：`docs/ecc-round2-meeting-minutes-20260531.md`  
- 任务板：`docs/youding-admin-overhaul-tasks.md`  

---

*创建：2026-05-31 · Phase 0 深读阶段*
