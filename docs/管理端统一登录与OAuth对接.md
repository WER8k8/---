# 管理端统一登录与 OAuth 对接说明

> **版本**：v1.0 · 2026-05-24  
> **状态**：✅ 已对接（密码登录 + 第三方 OAuth + 回调修复）  
> **代码位置**：`frontend/admin/src/views/login/` · `backend/app/api/v1/routes/auth.py` · `backend/app/services/oauth_login.py`

---

## 一、角色与入口（超管 / 代理 / 租户）

本系统 **不拆三套登录 API**，统一走 `POST /api/v1/auth/login`，由 JWT 内 `role` 决定登录后进哪个工作台。

| 角色类型 | JWT `role` 示例 | 前端入口 | 登录成功后跳转 |
|----------|-----------------|----------|----------------|
| **超级管理员 / 平台管理员** | `super_admin`、`admin` | `/login` | `/admin` |
| **各级代理** | `admin` / `editor` / `sales` 等（前端映射 L1～L5） | `/login` | `/admin`（能力由 `agentCapabilities` 控制菜单） |
| **租户管理员** | `tenant_admin` | `/login` 或 `/client/login` | `/client/dashboard` |

**说明**：

- 管理端统一登录页：`frontend/admin/src/views/login/index.vue`（标题「统一管理员登录」）。
- 租户客户后台登录：`frontend/admin/src/views/client/login.vue`，**同一套** `auth.login()` 与 `/api/v1/auth/login`。
- 代理层级（L1～L5）为 **登录后会话能力**，不是独立登录接口；映射见 `frontend/admin/src/utils/jwtPayload.ts`。

---

## 二、登录方式一览

| 方式 | 前端实现 | 后端接口 | 管理端 UI |
|------|----------|----------|-----------|
| **用户名 + 密码** | `useAuthStore().login()` | `POST /api/v1/auth/login` | ✅ 主表单 + 滑块人机校验 |
| **QQ 第三方** | `startOAuth('qq')` → 回调 | `GET /auth/oauth/qq/authorize` → `POST /auth/third-party-login` | ✅ OAuth 按钮 |
| **微信第三方** | 同上 | `GET /auth/oauth/wechat/authorize` → 同上 | ✅ |
| **飞书第三方** | 同上 | `GET /auth/oauth/feishu/authorize` → 同上 | ✅ |
| **钉钉第三方** | 同上 | `GET /auth/oauth/dingtalk/authorize` → 同上 | ✅ |
| **邮箱验证码** | 未做 Tab | `POST /auth/send-email-code`、`POST /auth/login-by-email` | ⬜ 后端已有，UI 待加 |
| **刷新令牌** | `performSilentTokenRefresh()` | `POST /api/v1/auth/refresh` | 自动（路由守卫） |

---

## 三、密码登录对接

### 3.1 请求

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username_or_email": "admin",
  "password": "********"
}
```

路径可通过环境变量 `AUTH_LOGIN_ROUTE` 配置别名；前端通过 `VITE_AUTH_LOGIN_PATH` 与之一致（默认 `/auth/login`）。

### 3.2 响应（成功）

`code === 0` 时，`data` 含：

- `access_token`、`refresh_token`
- `user`（含 `role`、`force_password_change` 等）
- 可选 `force_password_change: true` → 首次登录须改密

### 3.3 前端存储

| Key | 用途 |
|-----|------|
| `admin_token` | Access JWT |
| `admin_refresh_token` | Refresh JWT |
| `admin_username` | 展示用 |

### 3.4 本地开发

- 管理端 Vite：`http://localhost:5173`，代理 `/api` → `http://localhost:8001`
- 确保 `backend/.env` 中 `JWT_SECRET_KEY` 已配置（长度 ≥ 32）

---

## 四、第三方 OAuth 对接（QQ / 微信 / 飞书 / 钉钉）

### 4.1 流程图

```text
登录页点击 OAuth
  → GET /api/v1/auth/oauth/{provider}/authorize?state=...
  → 浏览器跳转各平台授权页
  → 平台回调 FRONTEND_URL/login/oauth-callback?code=...&state=...
  → 回调页从 state JSON 解析 provider（勿依赖 URL 上的 provider 参数）
  → POST /api/v1/auth/third-party-login { provider, code, state }
  → 写入 admin_token，router 跳转 /admin 或 state 内 redirect
```

### 4.2 关键实现文件

| 层级 | 路径 |
|------|------|
| 登录页 | `frontend/admin/src/views/login/index.vue` |
| OAuth 回调 | `frontend/admin/src/views/login/oauth-callback.vue` |
| 前端 API | `frontend/admin/src/api/oauth.ts` |
| 授权 URL / code 换身份 | `backend/app/services/oauth_login.py` |
| 路由 | `backend/app/api/v1/routes/auth.py` |

### 4.3 state 参数约定

登录页生成 state（Base64 URL-safe JSON）：

```json
{
  "redirect": "/admin",
  "ts": 1710000000000,
  "provider": "qq"
}
```

回调页 **必须** 从 `state` 读取 `provider`（QQ/微信等平台回调通常 **不带** `provider` 查询参数）。  
`sessionStorage` 键：`oauth_state_{provider}`，用于简易 CSRF 校验。

### 4.4 管理端绑定策略（安全）

- **已绑定** `third_party_logins` 的用户：可第三方登录进后台。
- **未绑定**：返回 `403`，提示先用用户名密码登录或由管理员绑定。
- **开发模式**：`OAUTH_DEV_BYPASS=true` 且 `code` 为 `dev:{provider}` 时，可模拟回调并绑定到 `admin` 用户（仅 development / bypass 开启时）。

### 4.5 环境变量（`backend/.env`）

```env
FRONTEND_URL=http://localhost:5173
OAUTH_REDIRECT_URI=http://localhost:5173/login/oauth-callback
OAUTH_DEV_BYPASS=true

QQ_APP_ID=
QQ_APP_KEY=
WECHAT_OPEN_APP_ID=
WECHAT_OPEN_APP_SECRET=
FEISHU_APP_ID=
FEISHU_APP_SECRET=
DINGTALK_APP_ID=
DINGTALK_APP_SECRET=
```

各开放平台「授权回调地址」须与 `OAUTH_REDIRECT_URI` **完全一致**。

### 4.6 配置探测接口

```http
GET /api/v1/auth/oauth/providers
```

返回示例：

```json
{
  "code": 0,
  "data": {
    "providers": { "qq": true, "wechat": false, "feishu": false, "dingtalk": false },
    "redirect_uri": "http://localhost:5173/login/oauth-callback",
    "dev_bypass": true
  }
}
```

登录页挂载时调用：未配置的渠道按钮置灰并提示。

---

## 五、验收清单（DoD）

### 5.1 密码登录

- [ ] `POST /api/v1/auth/login` 返回 `code=0` 与 token  
- [ ] 错误密码返回 401，文案「账号或密码错误」  
- [ ] 登录后进 `/admin`（或 `tenant_admin` 进 `/client/dashboard`）  
- [ ] 刷新页面仍保持登录（refresh 或有效 access）

### 5.2 开发模式 OAuth

- [ ] `OAUTH_DEV_BYPASS=true`  
- [ ] 点击 QQ → 跳转回调 → 进入 `/admin`  
- [ ] 未配置 AppId 时按钮仍可点（dev 模拟）

### 5.3 正式 OAuth（需 AppId）

- [ ] 各平台控制台回调 = `OAUTH_REDIRECT_URI`  
- [ ] 已在库中绑定第三方 ID 的账号可登录  
- [ ] 未绑定账号返回 403 明确提示  

### 5.4 脚本

```powershell
# 后端
cd backend
$env:JWT_SECRET_KEY="test-"+("x"*32)
python -c "from app.main import app; print([p for p in (getattr(r,'path','') for r in app.routes) if '/auth/oauth' in p])"

# 前端：浏览器打开 http://localhost:5173/login
```

---

## 六、常见问题

| 现象 | 原因 | 处理 |
|------|------|------|
| OAuth 点完提示「参数无效」 | 旧版回调未从 state 解析 provider | 已修复，见 `oauth-callback.vue` |
| 按钮灰色「未配置」 | 无 AppId 且未开 dev bypass | `.env` 设 `OAUTH_DEV_BYPASS=true` 或填 AppId |
| 503 无法获取授权地址 | 未配置且未 bypass | 同上 |
| 403 未绑定管理后台 | 第三方首次登录且无绑定记录 | 先用密码登录，或在库中写入 `third_party_logins` |
| 密码登录 Failed to fetch | 后端未启或代理错误 | 确认 8001 与 Vite proxy |

---

## 七、后续可选（未纳入 MVP UI）

| 项 | 说明 |
|----|------|
| 邮箱验证码登录 Tab | 对接已有 `send-email-code` / `login-by-email` |
| 管理端绑定第三方 UI | 用户中心「绑定 QQ/微信」 |
| 登录后强制改密页 | 已有 `force_password_change` 字段，前端引导待统一 |

---

## 八、修订记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-05-24 | v1.0 | 登录页 OAuth 回调修复、providers 探测、绑定策略、文档首发 |
