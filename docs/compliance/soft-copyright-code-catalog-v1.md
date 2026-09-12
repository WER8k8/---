# 软著登记 · 自研代码目录 v1（COMP-01 / RZ-01）

> **合规/IP** · W1 定稿 · **不含** Vue Vben / Naive Admin / `_ref` / Stub 演示页  
> **两件套**：① 优丁 AI-SaaS 后端服务 · ② 优丁管理端自研组件与 BFF 适配层

---

## 1. 登记策略

| 件 | 语言 | 页数目标 | 范围 |
|----|------|----------|------|
| **A. 后端** | Python | 30 | `backend/app/` 自研模块 |
| **B. 前端自研** | TS/Vue | 30 | `youding-admin-kit` + BFF 消费层 + 四壳 layout（非 Vben  Fork） |

**排除清单**：`_ref/**` · `frontend/admin-vben/**` · `node_modules` · 纯配置 · 第三方 LICENSE 文件

---

## 2. 后端目录（件 A · 优先导出）

```
backend/app/
├── api/v1/admin_bff/          # UAC 契约 · auth/menu/user 适配
├── core/                      # admin_auth · security · response
├── models/                    # 租户/用户/业务实体
├── services/                  # 询盘 · 产品 · SEO · AI 调度
├── middleware/
└── main.py
```

**专利交底交叉**：`services/` 内 AI 多模型调度 → [`专利/技术交底书-AI多模型调度.md`](../专利/技术交底书-AI多模型调度.md)

---

## 3. 前端自研目录（件 B · 60 页中的前端部分）

```
frontend/admin/src/
├── constants/stubVisibility.ts    # PM-01 矩阵 + 送检菜单
├── views/client/                  # 四支柱
├── views/agent/                   # 五栏 · KPI 白底
├── views/admin/                   # 鉴定面相关
├── components/youding/            # 自研 kit（W2 扩）
├── styles/design-tokens*.scss
└── api/admin-bff.ts               # BFF 客户端（待 FE-02）
```

**现网 admin** 为绞杀者源；**Vben 壳**仅工程依赖，不进入登记页。

---

## 4. 证据包（RZ-03 预备）

| 文件 | 用途 |
|------|------|
| `docs/pm-stub-visibility-matrix-v1.md` | 功能边界说明 |
| `docs/pm-four-pillars-top12-route-map.md` | 路由与送检对照 |
| Git 提交记录（2025-10 起） | 开发时间线 |
| 部署 staging URL + 账号说明 | 鉴别材料 |

---

## 5. W1 出口（Gate）

- [x] 目录 v1 本文档  
- [ ] 研发 readability 签字（BE-06 / FE-12）  
- [ ] 60 页 v1 导出脚本（W2 RZ-02）  

---

*COMP-01 · RZ-01 · 2026-06-02*
