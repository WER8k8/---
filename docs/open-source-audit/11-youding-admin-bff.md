# 11 · 优丁 Admin BFF（`admin_bff`）

> **基址**：`/api/v1/admin-bff/*`  
> **状态**：✅ Phase 0b 深读完成 · **零前端消费**

---

## 端点（6）

| Method | Path | 状态 |
|--------|------|------|
| POST | `/auth/login` | ✅ 转发 `auth_login` |
| GET | `/auth/captcha` | ⚠️ stub |
| GET | `/auth/tenant/search` | ⚠️ 空数组 stub |
| GET | `/user/info` | ✅ `tenant` 恒 null |
| GET | `/menu/routes?shell=` | ✅ DB 或 seed |
| GET | `/menu/permissions` | ✅ |

---

## 文件职责

| 文件 | 行级职责 |
|------|----------|
| `schemas.py` | `UacMenuRoute`, `UacUserInfo`, `UacPermissionBundle`, `authList` |
| `auth_adapter.py` | LoginBody 含 tenant_code；转发 legacy login |
| `user_adapter.py` | shell + homePath + roles |
| `menu_adapter.py` | `resolve_shell`, CLIENT/PLATFORM seed, `build_menu_tree` |
| `__init__.py` | 挂载 auth/user/menu |

---

## 已知 Bug / Gap

| # | 问题 | 状态 |
|---|------|------|
| 1 | `resolve_home_path('agent')` 曾为 `/agent/dashboard` | ✅ 已改为 **`/agent/performance`** |
| 2 | 无 AGENT/OPS seed | ✅ 已加 `AGENT_SEED` / `OPS_SEED` |
| 3 | CLIENT seed 仅 6 项 vs 现网 18 路由 | ⏳ 待 DB seed / Wave 2 |
| 4 | captcha / tenant search 未实现 | ⏳ P1 |
| 5 | 前端仍打 `/api/v1/auth/login` | ⏳ Wave 1 Vben 接线 |

---

## Wave 1 BFF 顺序

1. 修 agent homePath  
2. tenant search + user.info.tenant  
3. AGENT_SEED + OPS_SEED  
4. admin-vben 四 API 接 BFF  
5. AdminMenu DB seed 覆盖主链  

---

*Phase 0b*
