# Stub 可见性矩阵 v1

> **PM-01 + SAAS-01** · 2026-06-02  
> **代码唯一源**：`frontend/admin/src/constants/stubVisibility.ts`  
> **送检菜单**：同上 `CERT_INSPECTION_MENU`

---

## 四级策略

| 策略 | 含义 | 租户 | 代理 | 超管送检 |
|------|------|------|------|----------|
| **show** | 正常展示 | ✓ | ✓ | ✓ |
| **hide** | 菜单不可见，直链重定向 | ✓ | — | — |
| **planGate** | 展示升级 CTA（W2） | 暂 hide | — | — |
| **lab** | 仅 `admin_lab_enabled=1` | hide | — | 默认 hide |
| **kill** | 路由下线（未用） | — | — | — |

---

## 租户 Client（Hide / Lab）

| 路径 | 策略 | 说明 |
|------|------|------|
| `/client/media-factory` | lab | 视频工厂 |
| `/client/article-to-video` | lab | 文章转视频 |
| `/client/ai-scenarios` | lab | AI 场景 |
| `/client/egress` | planGate | 出口 IP · 企业版 |
| `/client/app` | hide | 出海计 App |
| `/client/copilot` | hide | 卖货飞轮 |

**菜单**：四支柱（工作台·获客·发品·账户）— 见 `client/layout.vue`

---

## 超管 Platform 送检菜单（FE-10）

开启 `admin_cert_mode`（默认开）时，侧栏 **仅** 见 `CERT_INSPECTION_MENU` 四组 + 设置。

关闭送检模式或开启实验室：见 `admin/platform-zones.vue`。

---

## 验收

- [x] 租户直链 `/client/media-factory` → 重定向 `/client/dashboard`
- [x] 超管送检模式侧栏 ≤ 鉴定面 + 设置
- [x] 超管直链 `/admin/v2ray` → 重定向 `/admin`（lab 关时）
- [x] Agent 无 `/admin/*` 链接（FE-03 ✅）

---

*联签：PM · SaaS 专家 · 前端*
