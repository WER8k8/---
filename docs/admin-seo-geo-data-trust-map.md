# Admin SEO / GEO 菜单 — 数据可信度对照表

> **用途**：老板与 ECC 看数字时，先查本表再决策。  
> **更新**：2026-06-02 · 与代码实现同步  
> **图例**  
> - ✅ **真实**：可当作工作依据（仍须结合询盘/电话验证效果）  
> - ⚠️ **半真**：有真检测，但易失败、降级、或「间接测量」  
> - 🔌 **需配置**：不配 Key/Token/域名则不算测过  
> - 📋 **示意/占位**：界面可能有数，**不能当排名业绩**  
> - ❌ **与推广无关**：菜单名像 GEO，但不是 AI 搜索优化  

---

## 一、GEO / AI 可见性（Generative Engine Optimization）

| 菜单路径 | 页面名称 | 评级 | 数据从哪来 | 您该怎么信 | 不能指望什么 |
|----------|----------|------|------------|------------|--------------|
| `/admin/geo-engine` | GEO 引擎模型收录 | 🔌→✅ | 配好 AI Key 后，**真调大模型 API**，问「是否认识品牌/是否推荐」 | 看各模型卡片：**已提及 / 未提及 / 监测未接通**；未接通=没测 | **不是** ChatGPT 网页真实搜索榜；**不能保证** AI 里排第一 |
| `/admin/geo-engine` | 监测综合分 | ⚠️ | 由上面探测结果汇总 | 看分 + 下方说明；分低=AI 目前不太提您 | 不等于「GEO 优化已完成」 |
| `/admin/geo-engine` | 提及率趋势图 | ⚠️ | 后端**只返回真实历史**；无历史则空（已禁止随机假曲线） | 页头仍写「示意」——**有历史点才信**，空=还没积累 | 不能当市占率曲线 |
| `/admin/geo-engine` | 竞品对比 | 🔌→⚠️ | 同上，多关键词批量探测 | 对比「谁被模型提到多」，不是市场份额 | 不能代替真实竞品调研 |
| `/admin/geo-engine` | 优化建议卡片 | ✅ | 基于探测结果的文案建议 | 当**改内容 checklist** | 改完不自动上榜 |
| `/admin/geo-engine` | 统一 GEO 分 unified-geo-v1 | ⚠️ | 合并 AEO/Optimizer/Engine/AI Search；无 Key 时分项为 null | 看 **overall + 分项**；探针未接通不算收录 | 不是真实搜索榜 |
| `/client/geo-visibility` | 租户 GEO 可见性 | ⚠️→✅ | 真实读 cross-border API + unified-geo-v1 | AEO/就绪度/llms 链接可信；引文仍为 honest_stub | 引文追踪未接实盘前勿报「已被 AI 引用」 |
| `/admin/geo` | GEO 基因分析 | ❌ | **NCBI 生物基因数据库**，与建材/AI 搜索**完全无关** | 科研用，**别当 SEO/GEO** | 与卖货、排名无关 |
| `/publish/unified` | GEO 统一发布台 | ✅ | AI 写稿 + 多平台变体（真实任务队列） | 当**内容生产工具**；人审后再发 | 发了不等于收录/排名 |
| 卖货副驾 | GEO 内容矩阵 / 提交包 | ✅ | `geo_content_matrix` 等意图走真实后端 | 生成草稿，人审 | 不自动发布、不保证引文 |

**GEO 总口诀**：配 Key → 看「提没提到」→ 改产品和内容 → **用电话询盘验证**，别只盯分数。

---

## 二、SEO 工具箱（`/seo/*`）

| 菜单路径 | 页面名称 | 评级 | 数据从哪来 | 您该怎么信 | 不能指望什么 |
|----------|----------|------|------------|------------|--------------|
| `/seo` | SEO 概览 | ✅ | 读数据库：关键词表、审计分、优化页数等 | 数字为 **0 就是 0**（已去掉演示注入） | 概览不等于排名好 |
| `/seo/site-audit` | 站点体检 | ✅ | **真抓 URL**，查 Meta/结构/移动/违禁词等 | 分数与问题列表可照着改站 | 高分**不保证**百度前三 |
| `/seo/keyword-ranking` | 关键词排名追踪 | ⚠️ | 调用 `/api/v1/seo/keywords`；追踪用 **KeywordTracker 爬虫**（简化解析） | API 失败时前端会 **降级 mock 列表**——要看是否加载失败 | 排名位次**不可靠**；勿报给客户 |
| `/api/v1/rank/check` | （API，部分页可间接用） | ⚠️ | **RankChecker 真爬**百度/Google/Bing | 返回里必看 **`is_simulated`**：`true`=模拟，别当真 | 百度反爬常触发模拟 |
| `/seo/baidu-tools` | 百度站长工具 | 🔌→📋 | 有 **site_token** 调百度 API；**无 token 用内置 mock** | 页上有 mock 提示；无 token **整页数字不可信** | 不能代替百度站长后台 |
| `/seo/llms-txt` | llms.txt | ✅ | 读写站点 llms.txt 配置（AEO 辅助） | 配好对 AI 爬虫友好 | 不保证被引用 |
| `/seo/content-optimizer` | AI 内容优化 | ✅ | AI 改文案 + **保留技术参数**校验 | 优化建议可用；规格勿乱改 | 不自动发布 |
| `/seo/compliance` | 合规扫描 | ✅ | 后端扫描违禁广告用语 | 发内容前过一遍 | 仅文案合规 |
| `/seo/building-wiki` | AI 建材百科 | ✅ | AI 生成文章，可发布 CMS | 当内容工厂；主题尽量用**真实产品词** | 文章多≠排名高 |
| `/seo/schema-markup` | Schema 结构化数据 | 📋 | 页面 mostly 本地/占位加载 | 以**实际生成的 JSON-LD 预览**为准 | 很多入口仍待接满 |
| `/seo/eeat` | E-E-A-T 评估 | 📋 | 挂载时仅探测 `/seo`，**无独立深度审计** | 当说明页/半成品 | 分数勿当真 |
| `/seo/batch-seo` | 批量 SEO 管理 | 📋 | 同上，入口级 | 批量操作前确认 API 已通 | — |
| `/seo/performance` | 性能与安全 | ⚠️ | 调 `/api/v1/seo/performance`；失败保留 mock | 看接口是否成功 | 非真实 RUM 时仅参考 |
| `/client/seo` | 客户端 SEO 优化 | ✅ | 同 `/seo` 概览 | 同左 | 同左 |

---

## 三、SEO 矩阵系统（`/seo-matrix/*`）

| 菜单路径 | 页面名称 | 评级 | 数据从哪来 | 您该怎么信 | 不能指望什么 |
|----------|----------|------|------------|------------|--------------|
| `/seo-matrix/dashboard` | 矩阵数据看板 | ✅ | DB：生成词、发布数、收录统计 | 有发布才有收录数字 | 0 发布=正常全 0 |
| `/seo-matrix/settings` | 矩阵设置 | ✅ | 租户/系统配置持久化 | 改完保存即生效 | — |
| `/seo-matrix/regions` | 地域管理 | ✅ | 省市区县域词库（DB） | 大城/县域词在此维护 | 词库有≠已排名 |
| `/seo-matrix/keywords` | 关键词管理 | ✅ | 矩阵生成词 DB | 跟踪「生成了哪些词」 | 不是百度排名榜 |
| `/seo-matrix/content` | 内容管理 | ✅ | 矩阵生成正文 DB | 人审后再用 | — |
| `/seo-matrix/publish` | 多平台发布 | ✅ | 真实发布任务/账号/Egress | 看发布状态、失败原因 | 发成功≠收录 |
| `/seo-matrix/inclusion` | 收录监控 | ⚠️ | **生产环境** `site:` 百度探测；**本地 dev 为 stub 跳过** | 点「检查收录」看返回 `probe_mode` | dev 环境收录全跳过 |
| `/seo-matrix/growth-tools` | 增长工具 | ⚠️ | 热词库 + 流量引擎注册表 + 探针状态 | 「API 探针就绪数」= 能测的引擎数，不是排名 | Perplexity 等多为「探索中」 |
| `/client/seo-publish` | 平台绑定/发布 | ✅ | 同矩阵发布 API | 同 publish | 同左 |

---

## 四、老板 30 秒自检（不用懂代码）

1. **GEO 引擎**：模型卡片是「监测未接通」→ **整页 GEO 分不算数**。  
2. **关键词排名**：接口有 **`is_simulated: true`** 或页面加载失败出现假列表 → **别当真**。  
3. **百度站长**：没绑 **site_token** → **全是演示数**。  
4. **收录监控**：本地开发环境 → **不会真查百度**；上生产再信。  
5. **GEO 基因分析**（`/admin/geo`）→ **跟卖货 SEO 无关**，别混。  
6. **最终效果**：以 **独立域收录 + 站长后台 + 真实询盘电话** 为准，不以 Admin 绿条为准。

---

## 五、与「推广难、排名难」对应的真能力（现阶段）

| 您要的 | 系统里**真能帮上忙**的菜单 | 仍缺/弱 |
|--------|---------------------------|---------|
| 站能不能被百度收 | 收录监控、站点体检、llms.txt | 稳定 SERP 排名 API |
| AI 里会不会提到厂名 | GEO 引擎（配 Key） | 真实 Perplexity/Google AIO 快照 |
| 大城长尾词内容 | 矩阵地域词 + 建材百科 + 统一发布台 | 与产品库强制绑定（在补） |
| 排名多少位 | rank/check（看 is_simulated） | 百度站长 token、KeywordTracker 弱 |
| 有没有来电话 | 询盘管理（非本表 SEO 菜单） | SEO→询盘全链路 honest 报表 |

---

## 六、维护说明（研发）

- 假数据门禁：`python scripts/validate-no-fake-delivery.py`  
- 收录：`INCLUSION_PROBE_REAL_ENABLED` 或 `ENVIRONMENT=production`  
- GEO 探测：`geo_engine_service.py` + AI 配置 Key  
- 排名爬虫：`rank_checker.py`（`is_simulated`）vs `keyword_tracker.py`（弱）  

*ECC PM-07 · 供大城基本盘工厂客户与内部验收使用*
