# SITE-DESIGN-01 · 租户独立站 L-Pro 标准

> **机器契约**：`.project/site-design-target.json`  
> **状态**：2026-06-16 生效 · W0 契约已落库，W1–W3 待实施

---

## 1. 问题与结论（一句话）

当前 Hermes + ECC 管线能产出文案与 JSON 骨架，**不能**稳定达到 ydalison / T-Global 级专业外贸站；对外不能再卖「AI 一键生成精美网站」，应卖 **L-Pro 专业独立站**（固定高级模板 + 填槽 + 发布门禁）。

---

## 2. 目标模型 L-Pro

| 层 | 取自 ydalison | 取自 T-Global |
|----|---------------|---------------|
| 信任 | About、Since、工厂叙事、行业应用、多线路联系 | — |
| 转化 | 中英文、专业配图 | 多级 **Products**（列表/详情/筛选）、询盘/对比钩子、下载中心 |
| v1 不做 | — | 热工计算器、完整 GDPR Cookie 中心、8+ 区域子站、电商结账 |

**站点地图（v1 必达）**

```
/  /about  /products  /products/[cat]  /products/[sku]
/solutions  /downloads  /contact
```

**升级档 L-Plus**：T-Global 全量能力，单独 SKU / 项目，不占用 L-Pro 默认交付。

---

## 3. Hermes 职责收窄

| 做 | 不做 |
|----|------|
| 选模板（`premium-b2b-v1` 等签约皮） | 从零生成版式 |
| 填槽：标题、卖点、CTA、SEO | GrapesJS 作为默认对外脸 |
| 挂接租户产品图 | 无图/无规格仍 `success` 上线 |

管线定义：`backend/app/data/hermes_site_builder_pipeline.json`  
执行：`backend/app/services/hermes/site_builder_ecc_pipeline.py`

---

## 4. 发布门禁（禁止假交付）

生产路径须满足（详见 JSON `publish_gate`）：

1. 已绑定高级模板 ID  
2. ≥3 个带图 SKU，每 SKU ≥3 条规格字段  
3. About 非空 + 至少一条联系渠道  
4. 无 `probe_mode: stub` / `mode: mock` 冒充实盘  

校验（W2）：`scripts/validate-site-l-pro-publish.py`（待实现）+ 全局 `validate-no-fake-delivery.py`

---

## 5. 多语言策略

| 档 | 说明 |
|----|------|
| **Tier 1** | 12 语核心库（`im_locale_service.SUPPORTED_LANGUAGES`）；营销文案 AI+词表；**规格表锁定**防错译 |
| **Tier 2** | 可选「更多语言」自动翻译挂件（参考 ydalison EN 站长列表）；仅营销段，免责声明「规格以英文/源语言为准」 |
| **Tier 3 L-Plus** | T-Global 式区域 URL + 人工审校 |

---

## 6. 开源技术路径

1. `powershell -File scripts/clone-open-source-refs.py` 拉取参考仓到 `_ref/`（勿提交 git）  
2. 深读审计：`docs/open-source-audit/17-tenant-premium-storefront.md`  
3. **只改** Nuxt 租户前台：`frontend/pages/tenant/`、`frontend/components/tenant/`  

候选参考：GrooveShop Nuxt 店面、Nuxtless、geins sales-portal（多租户）、`geeeeeeeek/cf_b2b` / `web_b2b`（对照）。

---

## 7. 实施波次

| 波次 | 内容 | 任务 ID |
|------|------|---------|
| **W0** | 契约 + 审计索引 + 部署瘦身 | SITE-DESIGN-01a/b |
| **W1** | 路由 + `premium-b2b-v1` 视觉签认 | SITE-DESIGN-01c/d |
| **W2** | Hermes 填槽 + 发布门禁脚本 | SITE-DESIGN-01e/f |
| **W3** | 语言选择器 + Tier2 挂件 | SITE-DESIGN-01g |

验收脚本：`scripts/validate-site-design-w3.py`（12 语 API + 语言切换单测 + 前端/建站页文件门禁）

进度：`docs/pm-dev-task-progress.json` → sprint `SITE-DESIGN`

---

## 8. 部署与海外（摘要）

| 项 | 建议 |
|----|------|
| 入门 VPS | 4C / 8G / 80–100G SSD，Docker Compose 生产栈 |
| 上传包体积 | 全量 rsync ~434MB；核心运行时源码 ~22MB；须排除 `_ref`、`_build_check`、`staging-data`、`.nuxt` 等 |
| Cloudflare | 主站非必须；**R2** 建议用于海外媒体/产品图；出站 IP 用于外平台发布 |

---

## 9. 对外话术

- **说**：L-Pro 专业外贸独立站 — 信任页 + 产品中心 + 统一询盘 inbox  
- **不说**：215 专家 / ECC 自动生成媲美 ydalison 的网站  

相关痛点文档：`docs/pm-cn-seller-vs-foreign-buyer-pains.md`（XF-B1 模板商品化 P0）
