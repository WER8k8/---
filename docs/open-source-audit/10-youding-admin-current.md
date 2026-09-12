# 10 · 优丁现网 Admin（`frontend/admin`）

> **状态**：✅ Phase 0b 深读完成 · 2026-06-01

---

## 核心数字

| 项 | 值 |
|----|-----|
| 叶子路由（component） | **234** |
| redirect 路由 | **27** |
| 视图 `.vue` | **239** |
| 路由文件 | **1** 文件 ~1442 行 |
| 引用 BFF | **0** |
| 引用 kit | **0** |

---

## 四壳分布

| 壳 | Layout | 子路由约数 |
|----|--------|-----------|
| Client | `views/client/layout.vue` | 18 |
| Agent | `views/agent/layout.vue` | 6 |
| Platform/Ops | `layout/index.vue` 等 | ~204 |
| Public | login/register/landing | 6 |

---

## 路由分级

| 级 | 约数 | 说明 |
|----|------|------|
| **A 主链** | 45–55 | 真实 API，Wave 1 必保 |
| **B 半生产** | 25–35 | API + Mock 回退 |
| **C Stub/实验室** | 80+ | 演示 toast、overview 壳 |
| **D 模板 Mock** | 6 | `/templates/*` |
| **E Redirect** | 27 | 遗留别名 |

---

## 重点差距

### `client/layout.vue`
- 菜单 **硬编码 16 项 + emoji**，非 BFF 动态
- 缺 5 条已注册路由（assistant、copilot 等）

### 登录
- `/login` → `/api/v1/auth/login`（**非 BFF**）
- 无 tenant_code、无 Naive 分屏

### `drag-module.vue`
- HTML5 拖拽 + **内存假数据**，无 API 持久化 → 非生产模块化设计器

---

## Wave 1 阻塞（现网）

1. 单文件 234 路由 — 无法 incremental 迁移  
2. 零 BFF 接线  
3. Client 菜单与 router/BFF seed 不一致  
4. kit 未 import  
5. 无 `admin-vben`  
6. `99-synthesis-for-uac.md` 未发布  

---

## Wave 1 主链优先

Client：dashboard → products → inquiries → content → seo → billing  
Platform：dashboard、tenants、finance  
Agent：performance、commission、account-opening  

**暂缓**：templates/*、cognitive/*、drag-module、capability-hub

---

*Phase 0b*
