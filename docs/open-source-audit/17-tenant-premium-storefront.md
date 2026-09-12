# 17 · 租户 L-Pro 高级店面（Nuxt B2B）

> **任务**：SITE-DESIGN-01b · Phase 0 审计（先读再写生产代码）  
> **契约**：`.project/site-design-target.json`  
> **落地面**：`frontend/pages/tenant/` · `frontend/components/tenant/`（禁止第二套 React 栈）

---

## 元信息

| 项 | 值 |
|----|-----|
| 目标 | ydalison 信任叙事 + T-Global 产品中心路由/筛选/详情/下载 |
| Clone 脚本 | `scripts/clone-open-source-refs.py`（已增 5 仓） |
| 优丁现网 | `TenantSite.vue` · `public-sites.ts` tenant-site |

---

## 候选库（待深读）

| ID | URL | 本地 `_ref/` | 重点抽取 | 状态 |
|----|-----|--------------|----------|------|
| grooveshop-nuxt | [vasilistotskas/grooveshop-storefront-ui-node-nuxt](https://github.com/vasilistotskas/grooveshop-storefront-ui-node-nuxt) | `grooveshop-storefront-ui-node-nuxt` | 产品列表/筛选/SSR 目录结构 | ⏳ 待 shallow clone |
| nuxtless | [grandant/nuxtless](https://github.com/grandant/nuxtless) | `nuxtless` | SEO 路由、i18n base、Vendure 分层 | ⏳ |
| sales-portal | [geins-io/sales-portal](https://github.com/geins-io/sales-portal) | `sales-portal` | 多租户 hostname、主题 CSS 变量 | ⏳ |
| cf_b2b | [geeeeeeeek/cf_b2b](https://github.com/geeeeeeeek/cf_b2b) | `cf_b2b` | Cloudflare B2B 展示结构对照 | ⏳ reference_only |
| web_b2b | [geeeeeeeek/web_b2b](https://github.com/geeeeeeeek/web_b2b) | `web_b2b` | Python B2B 模板信息架构 | ⏳ reference_only |

---

## 优丁对照表（W1 前必填）

| 能力 | L-Pro 要求 | 现网 TenantSite | 差距 |
|------|------------|-----------------|------|
| `/products` 多级导航 | 必须 | 部分/JSON 驱动 | 待审计 |
| SKU 详情 + 规格表 | 必须 | 待确认 | 待审计 |
| 筛选/对比/询盘钩 | 必须 | 待确认 | 待审计 |
| `/downloads` | 必须 | 待确认 | 待审计 |
| About/工厂叙事 | 必须 | 有骨架 | 视觉未达 ydalison |
| 12 语 + 可选翻译挂件 | Tier1/2 | `useVisitorLocale` | UI 待 W3 |

---

## 抽取原则

1. **只借路由与组件模式**，结账/Stripe/会员体系整段跳过（Out-of-Scope）。  
2. 产品数据 **只消费** 已有 OpenAPI/BFF，禁止前端造字段。  
3. 审计完成前 **不改** `frontend/admin` 建站编辑器默认脸。  
4. 深读 ≥2h/库 后改状态 ✅；README 级不算完成。

---

## 待深读文件队列（grooveshop 首批）

1. `nuxt.config.ts` — SSR、i18n、路由  
2. `pages/` — products 列表与 `[slug]` 详情  
3. 筛选 composable / server API 代理层  
4. 对比/收藏（若存在）— 只取询盘钩子 UX  

---

## 风险与禁止

- 禁止把 `_ref/` 整仓 copy 进 `frontend/`  
- 禁止未审计即替换 `TenantSite.vue` 为 GrooveShop 全量  
- 禁止生产路径返回假产品列表或假 `included: true` 收录
