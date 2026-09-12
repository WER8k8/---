# admin-vben 独立线（单开一版）

> **与 `frontend/admin` 并行**：旧壳送检/兼容；**新 UI 只在本目录迭代**。  
> 配置：`.project/admin-vben-standalone.json`

## 一键启动

```powershell
powershell -File scripts/start-dev-admin-vben.ps1
```

| 服务 | 地址 |
|------|------|
| **Vben 新壳** | http://127.0.0.1:5666/ |
| API | http://127.0.0.1:8001/docs |
| 旧 admin（并行） | http://127.0.0.1:5173/admin |

## 演示账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 租户 | `tenant_demo` | `TenantDemo@2026!` |
| 超管 | `admin` | `admin123` |

## 架构

```text
admin-vben (5666) → /api/v1/admin-bff/*  菜单/登录
                 → /api/v1/*            业务 API（client/dashboard 等）
legacy admin (5173)  完整业务页面临时保留，独立线通过链接跳转
```

## 独立线已迁入页面

- `views/client/dashboard.vue` — Bento 工作台
- `views/inquiries/index.vue` — 询盘列表
- `views/products/index.vue` — 发品中心 Hub
- `views/client/billing.vue` — 套餐用量（充值页下一迭代迁入）

## 开发

```bash
cd frontend/admin-vben
pnpm install
pnpm dev:antd
```

## 规则

1. 新功能 **只加 admin-vben**，不往 legacy admin 堆 UI  
2. 菜单以 BFF `menu_seeds.py` / DB 为准  
3. kit 组件放 `frontend/youding-admin-kit`
