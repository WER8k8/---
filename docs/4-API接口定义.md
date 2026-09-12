# API 接口定义（与当前 FastAPI 实现对齐）

> **完整路由表（HTTP 方法 + Path）**：见同目录 [`api-routes-dump.json`](./api-routes-dump.json)（由 `app.main:app` 自动导出）。  
> **Base URL**：`/api`（业务 API 集中在 `/api/v1`）。  
> **交互式文档**：后端启动后访问 `/docs`、`/redoc`。

---

## 0. 通用约定

### 0.1 统一响应（多数业务路由）

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "total": null,
  "page": null,
  "page_size": null
}
```

- **成功**：`code === 0`，业务数据在 `data`。
- **业务失败**：常见模式仍为 **HTTP 200**，但 `code != 0`（如 403、404），`message` 为说明。前端 `useApi` 已按此约定解析并抛出错误。
- **HTTP 层错误**：校验失败可能返回 **422**（FastAPI）；未捕获异常可能为 **500**；部分子路由使用 `HTTPException` 返回 **401/403/404**（如部分 SEO 工具接口）。

**响应归一化中间件（`/api/v1`）**：`app.core.unify_response_middleware.UnifyV1ApiResponseMiddleware` 对 **HTTP 200** 且 `Content-Type: application/json` 的响应做处理：若 JSON **根级不含 `code`**，则包装为上述 `APIResponse`；若已是 `{ code, ... }` 则不改写。对仅含 `data` + `total` / `page` / `page_size` 的旧分页信封会**展平**到标准 `APIResponse`，避免 `data` 再嵌套一层。**排除**：`/api/v1/feishu/webhook`（飞书 challenge）、附件下载（`Content-Disposition: attachment`）。

- **根级探测**：`GET /api/v1/health` → `APIResponse`，`data.status === "ok"`（与 `/api/v1/system/health` 并存，后者返回更细的子系统字段）。

### 0.2 认证

- **Header**：`Authorization: Bearer <access_token>`
- **获取令牌**：`POST /api/v1/auth/login`（Body：`LoginRequest`：`username_or_email`, `password`）
- **刷新**：`POST /api/v1/auth/refresh`（`refresh_token`）
- **角色**：路由内校验 `User.role`（如 `admin` / `super_admin` / `editor` / `sales` / `viewer`）

### 0.3 错误码（业务码 `code` 与 HTTP 状态）

| 场景 | HTTP | code（若适用） | 说明 |
|------|------|----------------|------|
| 成功 | 200 | 0 | 数据在 `data` |
| 未登录 / 令牌无效 | 401 或 200 | 401 | 视路由实现 |
| 权限不足 | 200 或 403 | 403 | `message` 说明 |
| 资源不存在 | 200 或 404 | 404 | |
| 参数错误 | 200 或 422 | 400 / 422 | |
| 服务器错误 | 500 | 500 | |

---

## 1. 认证 `/api/v1/auth`

| 方法 | 路径 | 认证 | 请求体 / 说明 |
|------|------|------|----------------|
| POST | `/auth/login` | 否 | `LoginRequest` → `TokenResponse`（包装在 `data`） |
| POST | `/auth/refresh` | 否 | `TokenRefreshRequest` |
| POST | `/auth/logout` | 否 | 占位成功 |
| POST | `/auth/send-email-code` | 否 | `EmailVerificationRequest` |
| POST | `/auth/login-by-email` | 否 | `EmailLoginRequest` |
| POST | `/auth/third-party-login` | 否 | `ThirdPartyLoginRequest` |
| GET | `/auth/oauth/providers` | 否 | 各渠道是否已配置 + `dev_bypass` + `redirect_uri` |
| GET | `/auth/oauth/{provider}/authorize` | 否 | Query：`state?` → `OAuthAuthorizeResponse`（`authorize_url`, `state`, `provider`） |

**第三方登录流程**：

1. `GET /auth/oauth/{provider}/authorize?state=<base64-json>` — `state` 建议含 `{ "provider", "redirect" }`  
2. 浏览器跳转授权页，回调至 `OAUTH_REDIRECT_URI`（默认 `{FRONTEND_URL}/login/oauth-callback`）  
3. `POST /auth/third-party-login` — Body：`{ "provider", "code", "state" }` → 与密码登录相同的 JWT 结构  

**管理端绑定**：仅 `third_party_logins` 已绑定用户可登录；开发模式 `OAUTH_DEV_BYPASS=true` 可用 `code=dev:{provider}` 模拟。详见 `docs/管理端统一登录与OAuth对接.md`。

---

## 2. 用户 `/api/v1/users`

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/users/` | JWT | 分页列表；管理员 |
| GET | `/users/me` | JWT | 当前用户 |
| GET | `/users/logs` | JWT | 操作日志（**注意**：静态路径须在 `/{user_id}` 之前注册） |
| GET | `/users/{user_id}` | JWT | 单用户 |
| POST | `/users/` | JWT | 创建 |
| PUT | `/users/{user_id}` | JWT | 更新 |
| DELETE | `/users/{user_id}` | JWT | 删除 |
| POST | `/users/{user_id}/change-password` | JWT | 改密 |
| POST | `/users/{user_id}/status` | JWT | 状态 |
| POST | `/users/batch-delete` | JWT | 批量删除 |

---

## 3. 产品 `/api/v1/products`

**查询参数（列表）**：`page`, `page_size`, `category_id`, `is_active`, `search`

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/products/categories` | 否 | 分类列表 |
| GET | `/products/categories/tree` | 否 | 分类树 |
| GET | `/products/categories/{category_id}` | 否 | 单个分类 |
| POST/PUT/DELETE | `/products/categories...` | JWT | 管理分类 |
| GET | `/products/` | 否 | 产品分页列表 |
| GET | `/products/popular` | 否 | 热门（须在 `/{product_id}` 之前匹配） |
| GET | `/products/slug/{slug}` | 否 | 按 slug |
| GET | `/products/{product_id}` | 否 | 按 ID |
| POST/PUT/DELETE | `/products/`, `/{product_id}` | JWT | 维护 |
| POST | `/products/batch-delete`, `/products/batch-status` | JWT | 批量 |
| GET/POST/DELETE | `/products/{product_id}/documents`, `/products/documents/{doc_id}` | 混合 | 产品文档 |

---

## 4. 案例 `/api/v1/case-studies`

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/case-studies/` | 否 | 分页列表 `page`, `page_size`, `status`, `search` |
| GET | `/case-studies/{case_id}` | 否 | 详情（公开） |
| POST | `/case-studies/{case_id}/images` | JWT | 新增图片 |
| POST/PUT/DELETE | `/case-studies/`, `/{case_id}` | JWT | 维护 |

---

## 5. 内容 `/api/v1/content`

**页面**：`/content/pages` 系列（列表、搜索、slug 详情、统计、批量、版本、SEO 子资源等）。**路由顺序**：静态段（如 `/pages/slug/{slug}`、`/pages/stats`、batch、upload）必须在 `/pages/{page_id}` 之前注册。

**通用 SEO（产品 / 案例 / 页面）**：

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/content/seo/{resource_type}/{resource_id}` | JWT | `resource_type` ∈ `product`, `case_study`, `page` |
| PUT | `/content/seo/{resource_type}/{resource_id}` | JWT | 部分更新 `SeoMetadataUpdate` |
| POST | `/content/seo` | JWT | 创建 `SeoMetadataCreate` |

---

## 6. 新闻 `/api/v1/news`

列表 / 详情 / 创建 / 更新 / 删除；列表与写操作需 **JWT**（实现以路由文件为准）。

---

## 7. 询盘 `/api/v1/inquiries`

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/inquiries/` | JWT | `status` 或 `status_filter`（等价别名）、`search` |
| GET | `/inquiries/export` | JWT | CSV 导出（须在 `/{id}` 之前） |
| GET | `/inquiries/{inquiry_id}` | JWT | 详情 |
| POST | `/inquiries/` | **否** | 前台提交询盘 |
| PUT | `/inquiries/{inquiry_id}` | JWT | 全量更新 |
| PUT | `/inquiries/{inquiry_id}/status` | JWT | 仅更新 `status` |
| DELETE | `/inquiries/{inquiry_id}` | JWT | 删除 |

---

## 8. SEO 聚合 `/api/v1/seo`

由多个子路由拼接，主要包括：

| 前缀 | 说明 |
|------|------|
| `/seo/dashboard` 等 | `dashboard.py`：**GET `/seo/dashboard`** 返回统一 `APIResponse`，`data` 含 `total_products`、`total_inquiries`、关键词与 AI 统计、`keyword_trend`、`page_coverage`（四类页面 SEO 占比）、`recent_inquiries`、`hot_keywords`、`product_stats`；查询参数 **`range`**：`today` \| `week`（默认）\| `month`（影响趋势天数）。另有关键词组、运行审计 `POST /seo/run-audit` |
| `/seo/content-optimizer` | `content_optimizer.py`：`/optimize`, `/validate-content`, `/extract-params` |
| `/seo/llms-txt` | `llms_txt.py`：`/generate`, `/validate-llms-txt`, `/llms-txt-template` |
| `/seo/site-audit` | `site_audit.py`：创建/列出审计记录 |
| `/seo/schema-markup` | `schema_markup.py`：类型、生成、校验、CRUD、导出 |
| `/seo/compliance` | 合规扫描与管理 |
| `/seo/eeat` | EEAT 相关 |
| `/seo/keywords` | `keyword_ranking.py`：**GET `/` 返回裸数组**（非 `APIResponse`）；其余 CRUD 多为 ORM + `HTTPException` |
| `/seo` 根级 | `audits`, `llms` 配置等（见 `seo/__init__.py`） |

> 旧的 `app/api/v1/routes/seo.py` **未**挂载到主路由树，仅作参考或废弃。

---

## 9. 数据分析 `/api/v1/analytics`

`GET /`、`/dashboard`、`/traffic`、`/products`、`/export` — 均需管理员类角色（见实现）。

---

## 10. 设置 `/api/v1/settings`

`GET /`、`PUT /site`、`PUT /seo`、`PUT /system`

---

## 11. AI 配置 `/api/v1/ai-config`

`GET /`、`PUT /`、`POST /provider/{provider_id}/toggle`、`GET /stats`

---

## 12. A/B 测试 `/api/v1/ab-test`

列表、详情、创建、更新、删除、`/{id}/start`、`/{id}/stop`

---

## 13. 合规 `/api/v1/compliance`

概览、审计、问题列表、解决、报告等

---

## 14. 系统 `/api/v1/system`

**注意**：`routes/system.py` 与 `system_routes.py` **同时**以 `/system` 前缀挂载，存在路径重叠风险；以 `api-routes-dump.json` 为准排查。

---

## 15. 飞书 `/api/v1/feishu`

Webhook、绑定、报表等（见 `routes/feishu.py`）

---

## 16. SEO 矩阵 `/api/v1/seo-matrix`

县域矩阵、关键词、内容模板、发布任务等大模块（见 `routes/seo_matrix.py`）

---

## 17. 根与健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 项目信息与运行状态（`APIResponse`） |
| GET | `/health` | 健康检查 |

---

## 18. 与 Schema 的对应关系

Pydantic 模型位于 `backend/app/schemas/`，与路由强相关的包括：`auth`, `user`, `product`, `content`（含 `SeoMetadata*`）, `news`, `case_study`, `inquiry`, `seo`, `schema_markup`, `ab_test`, `ai_config`, `compliance` 等。具体请求/响应字段以各路由函数的 `response_model` 及函数内联 `BaseModel` 为准。

---

## 19. 修订记录（本次同步）

- 与前端对齐：`case-studies`、`schema-markup`、`content-optimizer`、`llms-txt` 等路径。  
- 修复动态路由与静态路径冲突（users / products / content pages / inquiries）。  
- 补充询盘导出与状态接口；案例图片上传与公开详情。  
- `SeoMetadata` 模型扩展 `resource_type` / `resource_id` 及 OG 字段，以支持 `/content/seo/...`。
- 管理端路径与功能一一对照表：[`管理端路由与功能映射表.md`](./管理端路由与功能映射表.md)。  
- 蜂群/调度用机器任务队列：[`admin-route-task-board.json`](./admin-route-task-board.json)（`npm run task-board:validate` 校验）。
