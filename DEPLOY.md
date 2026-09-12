# 生产环境部署说明（认证与矩阵后台）

本文档覆盖 **Python 主后端**（统一登录签发）、**seo-backend**（矩阵 API / JWT 联邦校验）及 **frontend/admin**（统一登录页）上线要点。

---

## 1. 部署顺序建议

1. 配置 **Python** 环境变量与数据库迁移（含 `users` 表）。
2. 配置 **seo-backend** 环境变量并启动（主库 + 可选矩阵第二连接）。
3. 部署 **frontend/admin**（Vite 统一登录页），将 `UNIFIED_ADMIN_LOGIN_URL` 指向该站点登录路径。
4. 将 **Nuxt** `NUXT_PUBLIC_UNIFIED_ADMIN_LOGIN_URL`（若使用）指向同上。
5. 确认 **MAIN_ADMIN_JWT_SECRET**（Node）与 **JWT_SECRET_KEY**（Python）**完全一致**，且 **≠** `JWT_SECRET`（Node）。

---

## 2. 配置项清单

### 2.1 Python（`backend`）

| 变量 | 必填 | 说明 |
|------|------|------|
| `JWT_SECRET_KEY` | 是 | 签发主站 Access / Refresh；须与 seo-backend `MAIN_ADMIN_JWT_SECRET` 一致 |
| `DATABASE_URL` | 是 | 主业务库 |
| `SEO_MATRIX_DATABASE_URL` 或 `SEO_MATRIX_DB_*` | 否 | 矩阵 `admin_users` 所在库（生产多为 MySQL）；未配时可依赖 `SEO_MATRIX_SQLITE_PATH` 本地文件 |
| `SEO_MATRIX_SQLITE_PATH` | 否 | 本地/开发矩阵 SQLite 路径 |

### 2.2 seo-backend（矩阵 Node）

| 变量 | 生产必填 | 说明 |
|------|----------|------|
| `JWT_SECRET` | 是 | **仅**矩阵本机 refresh / 历史 Node Token；长度建议 ≥32 |
| `MAIN_ADMIN_JWT_SECRET` | **是** | 与 Python `JWT_SECRET_KEY` 一致；**禁止**与 `JWT_SECRET` 相同 |
| `UNIFIED_ADMIN_LOGIN_URL` | **是** | 合法 `http(s)` 绝对 URL；`GET /api/v1/auth/login` 302 目标 |
| `SEO_MATRIX_DB_HOST` / `NAME` / `USER` | 条件 | 三者需同时配置才启用第二连接；`PASSWORD` 可空；**禁止**只配一半 |
| `API_PREFIX` | 否 | 默认 `/api/v1` |
| `NODE_ENV` | 建议 `production` | 启用更严的启动校验 |

### 2.3 行为说明

- **`POST /api/v1/auth/login`**：固定 **403**，不提供矩阵独立 JSON 登录。
- **`GET|HEAD|… /api/v1/auth/login`**（非 POST、非 OPTIONS）：**302** 到 `UNIFIED_ADMIN_LOGIN_URL`；**OPTIONS** 返回 **204**（便于 CORS 预检）。
- **矩阵 MySQL 第二连接**：启动时若认证失败，**自动降级**（打日志、关闭连接），**进程不退出**；矩阵 `admin_users` 校验仍可由主站 Python 完成。

---

## 3. 启动自检（失败即退出）

seo-backend 在 `listen` 前依次执行：

1. `validateStartupConfigOrThrow()` — JWT 长度、`SEO_MATRIX_DB_*` 完整性、`UNIFIED_ADMIN_LOGIN_URL`（生产必填且合法 URL）等。
2. `assertJwtSecretsSafeOrThrow()` — 若同时配置了 `MAIN_ADMIN_JWT_SECRET` 与 `JWT_SECRET`，二者**不得相同**。

控制台会输出明确中文 `[配置错误] …` 原因，请按提示修正后重启。

---

## 4. 常见问题排查

| 现象 | 排查 |
|------|------|
| 启动报 `E_JWT_SECRET_COLLISION` | 为统一登录单独生成 `MAIN_ADMIN_JWT_SECRET`，与 `JWT_SECRET` 区分，并写入 Python `JWT_SECRET_KEY` |
| 启动报 `SEO_MATRIX_DB_* 不完整` | 删除所有 `SEO_MATRIX_DB_*` 以关闭第二连接，或补全 HOST/NAME/USER |
| 启动报 `UNIFIED_ADMIN_LOGIN_URL` | 生产必须配置完整 `https://…/login` |
| 矩阵 API 401 | 请求是否带 `Authorization: Bearer`；Token 是否由主站签发且含 `mid`；`MAIN_ADMIN_JWT_SECRET` 是否与 Python 一致 |
| 第二连接降级告警 | 检查矩阵库网络、账号权限、防火墙；主站统一登录仍可用则属预期降级 |

---

## 5. 安全与运维

- 生产环境 **HTTPS** 部署统一登录页与矩阵 API。
- 定期轮换 `JWT_SECRET` / `MAIN_ADMIN_JWT_SECRET`（与 Python 同步轮换联邦密钥）。
- 勿在日志中打印完整密钥；`.env` 不入库。

---

## 6. 回归验证（建议发布前执行）

```bash
# Python 认证接口
cd backend && python -m pytest tests/test_api/test_auth.py -q

# 管理端类型检查
cd frontend/admin && npx vue-tsc --noEmit
```

---

## 7. 正向 / 逆向自检（发布前 mentally 过一遍）

**正向**

- 生产环境缺 `MAIN_ADMIN_JWT_SECRET` 或 `UNIFIED_ADMIN_LOGIN_URL` → 启动失败。
- `SEO_MATRIX_DB_*` 只配一半 → 启动失败。

**逆向**

- `MAIN_ADMIN_JWT_SECRET === JWT_SECRET` → 启动失败（`E_JWT_SECRET_COLLISION`）。
- 矩阵 MySQL 宕机 → 进程启动成功，日志出现降级说明；主库与主站登录不受影响。
