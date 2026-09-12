# Hermes 排名第一准则（存在第一意义）

> 2026-06 · 创始人战略 → Hermes / ECC 专家 / 研发对齐

---

## 一、第一准则

**Hermes 的存在第一意义：保证分散流量入口下的排名与 AI 推荐效果。**

无排名信号 → 无电话 → 无开户与续费。其它运维（巡站、依赖升级、文档）**不得挤占**每日排名攻坚带宽。

代码宪章：`backend/app/services/hermes/hermes_rank_first_constitution.py`

---

## 二、为什么必须 Hermes + ECC 每天做

| 现实 | 含义 |
|------|------|
| 流量入口分散 | 百度 SERP、豆包浏览器、360/纳米、文心、元宝、DeepSeek… **不是一套算法** |
| 无头浏览器与 AI 浏览器兴起 | 抓取与引用路径变化，传统 SEO 工具覆盖不足 |
| 大模型蒸馏/换版频繁 | 上周有效的 tactic，本周可能衰减 → **必须日更探测 + 外网战术雷达** |
| 平台数 × 有效发布 | 矩阵面越广，多源一致信号越强（见 platform_rank_registry） |

**这不是一次性功能，是 Hermes 驱动的日更运维。**

---

## 三、每日 07:00 主循环（Celery: `hermes_daily_rank_cycle`）

```
07:00 Hermes 排名攻坚
  ├─ multi_engine recommend probe（豆包/通义/DeepSeek/ChatGPT/Gemini…）
  ├─ geo_tactics_radar（Tavily：GEO 论文 + 豆包/360/百度蒸馏动态）
  ├─ platform_discovery 缺口（下一批适配器队列）
  ├─ rank_guard 收录/SEO 回归
  ├─ ECC 专家只读评审（geo-rank-strategist + 产品/GEO/QA）
  └─ 回归 → 飞书告警 + suggest_remediation（不自动改生产）

08:00 技术雷达（依赖/changelog/Schema）
09:00 竞品 GEO 监控
每6h  Rank Guard 轻量探针
```

实现：`backend/app/services/hermes/daily_rank_ops.py`

快照键：`hermes:rank_ops:latest` · 司令部只读：`command_center` → `hermes_rank_ops`

---

## 四、多引擎分轨（不可混用一套 SEO）

注册表：`backend/app/services/geo/multi_engine_rank_registry.py`

| 入口 | 家族 | 当前探针 | 蒸馏风险 |
|------|------|----------|----------|
| 百度搜索 | classic_search | SEO 矩阵 / 站长 | 中 |
| 豆包 | ai_browser | GEOEngine `doubao` recommend | **高** |
| 通义 | ai_search | GEOEngine `qwen` recommend | **高** |
| DeepSeek | llm_chat | GEOEngine `deepseek` recommend | **高** |
| 文心/元宝/360/Kimi | ai_* | **exploration**（待 headless/API） | **高** |

**攻坚队列**：优先把 exploration 引擎接入真实 probe，而不是对外宣传「全入口已覆盖」。

---

## 五、ECC 专家分工（只读评审，不自动热更）

| 专家 ID | 职责 |
|---------|------|
| `geo-rank-strategist` | 排名回归、战术版本、probe 通过率 |
| `insulation-material-product-manager` | GEO 内容/Schema/平台策略 |
| `testing-reality-checker` | 拒绝「假排名/假成功」 |
| `insulation-backend-security-expert` | 无头/外网抓取合规 |

门控：与 `maintenance_constitution` 一致 — **read_probe / suggest_remediation only**。

---

## 六、与收益闭环

```
Hermes 日更 probe ↑ → 推荐位/收录信号 ↑ → 询盘电话 ↑ → 开户/续费 ↑ → 再投内容与平台适配
```

环境变量（可选）：

```bash
HERMES_RANK_PROBE_KEYWORDS=品牌A,品类A,地区A|品牌B,品类B,地区B
TAVILY_API_KEY=...   # 外网 GEO/平台动态
AI_ARK_API_KEY=...   # 豆包
AI_DASHSCOPE_API_KEY=...  # 通义
```

---

## 七、Out of Scope（Hermes 不做）

- 不绕过 robots/付费墙批量爬专利网（公开文本脱敏引用走 `public_tech_reference_service`）
- 不自动发布、不自动改租户内容、不承诺具体排名名次
- 不把 DeerFlow/Hermes 品牌暴露给租户
