# 14 · 开源论坛 / 问答社区 · Sidecar 选型（建材 B2B · SEO/GEO）

> **原则**（同 `money-loop.md`）：**只抄契约与编排，不整库 fork 进产品仓。**  
> **读者**：PM-07 · 架构 · 老板（要「像样社区」又不想养 PHP/Ruby 团队）

---

## 一、先问：老板要的是哪种「论坛」？

| 场景 | 要不要 Discourse 级大论坛 | 优丁更合适的形态 |
|------|---------------------------|------------------|
| 海外买家在独立站问「岩棉 A1 多厚」 | 要 **公开 Q&A + SEO** | ✅ **问答 Sidecar**（Answer） |
| 大城厂之间交流工艺 | 可选，非 P0 | 产业带 Wiki（已有 `building-wiki`） |
| 抖音评论谈单 | 不要论坛 | 已有 `social_interactions` |
| 询盘跟进 | 不要论坛 | 已有 `inquiries` + 语言桥 |

**结论**：对「没学历、不会英语」的工厂老板，论坛的价值不是「聊天室」，而是：

1. **独立站 SEO/GEO** — 长尾问答题面（Google / AI 引用）
2. **信任** — 真实问答比硬广像样
3. **减轻客服** — 常见规格问一次、多人可见

---

## 二、候选库（可克隆到 `_ref/` 深读，禁止进送检包）

| 优先级 | 项目 | License | 栈 | 适合 | 不适合 |
|--------|------|---------|-----|------|--------|
| **P0** | [Apache Answer](https://github.com/apache/answer) | Apache-2.0 | Go + React | B2B 问答、Help Center、Docker 一键、中文社区 | 重度游戏化勋章 |
| **P1** | [Flarum](https://github.com/flarum/flarum) | MIT | PHP | 轻量美观、扩展多 | 需 PHP 运维；与 FastAPI 栈分离 |
| **P1** | [NodeBB](https://github.com/NodeBB/NodeBB) | GPL-3.0 | Node.js | 与 JS 栈接近、插件丰富 | GPL 传染需法务看嵌入方式 |
| **P2** | [Discourse](https://github.com/discourse/discourse) | GPL-2.0 | Ruby | SEO 极强、成熟 | 重、资源贵、Ruby 栈 |
| **P2** | [Vanilla Forums](https://github.com/vanilla/vanilla) | GPL-2.0 | PHP | 企业社区 | 同 Flarum，运维分离 |

**PM 推荐默认**：**Apache Answer Sidecar** — 问答形态 = 建材规格长尾词；Apache 协议；官方 `apache/answer:2.x` 镜像。

---

## 三、落地架构（与 n8n Sidecar 同套路）

```text
租户独立站 (Vue / 公开页)
    │  iframe / 子路径 / 子域名 forum.{tenant}.example.com
    ▼
Apache Answer (Sidecar, deploy/examples/forum-sidecar)
    │ Webhook: question.created / answer.created
    ▼
优丁 API (FastAPI)
    ├── SEO 矩阵：长尾词入库 (dacheng_keyword_seed)
    ├── building-wiki：优质回答同步词条
    └── 高意向问题 → 询盘 (inquiries) 可选

认证：OIDC / JWT 单点（Answer 插件）— 租户 Admin 免二次注册
```

**禁止**：

- 把 Answer/Flarum 源码拷进 `backend/`、`frontend/`
- 未 PM 审计就改 270+ Admin 页去「仿论坛 UI」
- 假数据灌帖冒充活跃社区（违背 honest 数据）

---

## 四、抄什么 / 不抄什么

| 抄 | 不抄 |
|----|------|
| Docker compose、持久卷、反代 TLS 模板 | 全站 UI 皮肤重写到 admin |
| REST：问题列表、标签、投票排序 | Ruby/PHP 运行时进主栈 |
| Sitemap / 结构化数据思路 → SEO 页 | 整库当子模块 git submodule 进产品仓 |
| OAuth/OIDC 对接租户登录 | GPL 代码与 Apache 产品混编（NodeBB/Discourse 需法务） |

---

## 五、与现有能力接口（冻结点）

| 已有模块 | 论坛 Sidecar 关系 |
|----------|-------------------|
| `building-wiki` | 问答「采纳答案」→ Wiki 条目草稿 |
| `seo_matrix` / 产业带词库 | 新问题标题 → `IndustryKeyword` 候选 |
| `inquiries` | 含邮箱/电话的提问 → 可选转询盘 |
| `cross-border` 语言桥 | 英文问 → 中文摘要给老板；中文答 → 英文发布 |

---

## 六、本地深读（克隆到 `_ref/`，已 gitignore）

```powershell
powershell -File scripts/clone-forum-ref-repos.ps1
```

| 路径 | 用途 |
|------|------|
| `_ref/answer` | P0 问答 Sidecar 源码审计 |
| `_ref/flarum` | P1 轻论坛对比 |
| `_ref/nodebb` | P1 Node 论坛对比 |

Sidecar 运行：

```powershell
cd deploy/examples/forum-sidecar
docker compose up -d
# 浏览器 http://localhost:9080 完成初始化
```

---

## 七、Wave 建议（研发泳道）

| ID | 交付 | Lane |
|----|------|------|
| FORUM-01 | Sidecar compose + README + 健康检查 | ARCH |
| FORUM-02 | 租户子域反代模板（Caddy/Nginx snippet） | ARCH |
| FORUM-03 | Webhook → SEO 词库（只读入库） | BE |
| FORUM-04 | 公开页嵌入「买家问答」Tab（iframe/OAuth） | FE |
| FORUM-05 | 语言桥：英问中读 / 中答英发；Webhook→询盘草稿+Wiki 草稿 | 跨境+BE |

**Out of Scope**：自建 Discourse 级 moderation AI、论坛积分商城。

---

## 八、验收

1. `docker compose` 起 Answer，`:9080` 可发帖  
2. Webhook 打到 dev API `:8001`，产生一条 SEO 候选词（无自动发布）  
3. 产品仓 `git status` **不含** `_ref/` 与论坛 vendor 代码  

索引回链：`docs/open-source-audit/00-methodology-and-index.md`
