# 统一管理员登录与安全部署说明

本文说明：**Redis 分布式防暴力破解**、**动态登录路径**、**Nuxt 跳转统一登录**、**网关（Nginx）路径隐藏** 的配置方式。适用于 `backend`（FastAPI）与 `frontend/admin`（Vite 管理端）、`frontend`（Nuxt 官网）组合部署。

---

## 1. Redis（登录防暴 + Refresh 黑名单）

登录防暴与 refresh 令牌黑名单**共用** `REDIS_URL` 连接（懒连接、失败降级，见 `app/core/login_bruteforce.py` 与 `app/core/refresh_token_blacklist.py`）。

| 环境变量 | 说明 |
|----------|------|
| `REDIS_ENABLED` | `true` 时尝试使用 Redis；`false` 时全程进程内内存（多实例防暴不一致）。 |
| `REDIS_URL` | 例如 `redis://:密码@redis.internal:6379/0`（密码在 URL 或 `REDIS_PASSWORD`）。 |
| `REDIS_PASSWORD` | 若 URL 中未带密码可单独设置。 |
| `LOGIN_BF_USE_REDIS` | 默认 `true`；仅关闭登录防暴的 Redis、仍保留其它逻辑时可设 `false`。 |
| `LOGIN_BF_REDIS_PREFIX` | 键前缀，默认 `login_bf`。 |
| `LOGIN_BF_REDIS_STATE_TTL` | 状态键 TTL（秒），默认 `1200`，须大于最长锁定时长。 |

**生产检查清单**

- [ ] `REDIS_ENABLED=true` 且 `REDIS_URL` 指向内网 Redis，勿对公网暴露 6379。  
- [ ] 与应用同网段或 VPC，降低延迟与断连概率。  
- [ ] Redis 故障时服务仍可登录（降级内存）；多实例下降级阶段各实例计数独立，应尽快恢复 Redis。

---

## 2. 动态登录路径（与前端一致）

后端在 **`/api/v1/auth/login`** 外，可按环境再挂一条**别名路径**（OpenAPI 中默认隐藏别名，减少枚举面）。

| 环境变量 | 说明 |
|----------|------|
| `AUTH_LOGIN_ROUTE` | 相对于 `auth` 前缀的路径段，**不含** `/api/v1`。仅允许 `[A-Za-z0-9/_-]`，禁止 `..`。默认 `login`（即仅标准 `/auth/login`）。示例：`session/x7k9m2` → 别名为 `POST /api/v1/auth/session/x7k9m2`，与标准 `/auth/login` **并存**。 |

**前端 `frontend/admin`（Vite）**

| 环境变量 | 说明 |
|----------|------|
| `VITE_API_BASE` | API 前缀，默认 `/api/v1`。 |
| `VITE_AUTH_LOGIN_PATH` | 须与后端实际路径一致，例如 `/auth/login` 或 `/auth/session/x7k9m2`（以 `/auth/` 开头）。 |

构建前在 `.env.production` 中设置，**`VITE_AUTH_LOGIN_PATH` 与 `AUTH_LOGIN_ROUTE` 必须对应**：  
`VITE_AUTH_LOGIN_PATH=/auth/<AUTH_LOGIN_ROUTE 去掉首尾斜杠后的整段>`。

---

## 3. Nuxt 官网跳转统一登录

| 环境变量 | 说明 |
|----------|------|
| `NUXT_PUBLIC_UNIFIED_ADMIN_LOGIN_URL` | **必填（生产）**：浏览器可访问的**完整 HTTPS URL**，指向 Vite 管理端登录页，例如 `https://admin.example.com/login`。勿带未部署域名或内网仅解析名（用户浏览器无法打开）。 |

格式示例：

```bash
NUXT_PUBLIC_UNIFIED_ADMIN_LOGIN_URL=https://admin.example.com/login
```

未配置时，`frontend/pages/admin/login.vue` 会提示「登录入口未配置」，避免误跳转到开发默认地址。

---

## 4. Nginx：网关级路径隐藏（示例）

思路：对外只暴露**不易猜测**的路径，由 Nginx **rewrite** 到内部真实 `auth/login`；后端可同时保留标准路径或仅允许内网访问标准路径。

**示例 A：对外路径 `/api/v1/auth/session/x7k9m2` → 内部 `/api/v1/auth/login`**

```nginx
# 仅示例：请将 x7k9m2 换为随机段，并与 AUTH_LOGIN_ROUTE、VITE_AUTH_LOGIN_PATH 对齐
location = /api/v1/auth/session/x7k9m2 {
    proxy_pass http://127.0.0.1:8000/api/v1/auth/login;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**示例 B：不 rewrite，由应用双路由处理**

设置 `AUTH_LOGIN_ROUTE=session/x7k9m2`，前端 `VITE_AUTH_LOGIN_PATH=/auth/session/x7k9m2`，Nginx 只做反代到同一 upstream，无需 rewrite。

**安全建议**

- 随机段定期轮换时，需**同时**更新环境变量与 Nginx，并重新构建前端。  
- 限制管理端源站仅允许办公网或 VPN 访问，比单纯隐藏路径更有效。

---

## 5. 相关源码索引

| 能力 | 路径 |
|------|------|
| Redis / 内存防暴 | `backend/app/core/login_bruteforce.py` |
| Redis 连接（与黑名单共用） | `backend/app/core/refresh_token_blacklist.py` |
| 登录路由 + 别名注册 | `backend/app/api/v1/routes/auth.py` |
| 前端登录 URL | `frontend/admin/src/api/authPaths.ts` |
| 登录请求 | `frontend/admin/src/stores/auth.ts` |
