# 06 · Vue-Admin-Better

> **本地**：`_ref/vue-admin-better` @ `bac0216` · v3.0.2  
> **栈**：Vue **2.7** + Element UI + Vuex（**不可整库采用**）  
> **状态**：✅ 本地深读 · Phase 0b

---

## 核心结论

开源仓 **无 CRUD 自动生成脚本**；`setting.config.js` 的 `templateFolder` 指向商业版生成器。  
优丁只借 **三件套模式** → 自建 `scripts/gen-crud-from-openapi.mjs`。

---

## CRUD 三件套（canonical：`userManagement`）

| 件 | 路径 | 约定 |
|----|------|------|
| API | `src/api/userManagement.js` | `getList` POST · `doEdit` · `doDelete` |
| 页面 | `views/personnelManagement/userManagement/index.vue` | VabQueryForm + el-table + 分页 |
| 弹窗 | `components/UserManagementEdit.vue` | 新增/编辑 |

**分页**：`pageNo` / `pageSize` / 响应 `totalCount` → adapter 到优丁 `page/pageSize/total`。

---

## Mock 自动挂载（非页面生成）

- `mock/utils/index.js` → `handleMockArray()` 扫描 `mock/controller/*.js`
- `mock/index.js` → devServer + chokidar 热更新

---

## UI 规则（代码提取）

| 规则 | 值 |
|------|-----|
| 主色 | `#4d8af0` |
| 侧栏 | `#191a23` |
| loading | 固定文案 + **300ms** 最小展示 |
| QueryForm | Top/Left/Right/Bottom 四区 |
| 路由 | **hash** · 单文件 `router/index.js` ~400 行 asyncRoutes |

---

## 抽取 vs 禁止

| Partial | No |
|---------|-----|
| 三件套页面结构 → OpenAPI 模板 | Element UI 组件 |
| getList/doEdit/doDelete 命名思路 | Vab Layout |
| intelligence/all 双模式对照 UAC | Vue2 Options 页面 |

---

*Phase 0b*
