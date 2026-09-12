# Hermes · GEO 排名攻坚 — 开发记录（2026-06-02）

> **源码仓**：`C:\Users\97907\Desktop\上线网站`  
> **战略背景**：平台年费堆叠超利润；出口/工地集采需 **排名 → 电话 → 开户 → 续费**；Hermes **存在第一准则 = 排名效果**  
> **关联交接**：[HERMES-GEO-排名攻坚-交接记录-2026-06-02.md](./HERMES-GEO-排名攻坚-交接记录-2026-06-02.md)

---

## 一、本批目标（已达成 vs 待做）

| 目标 | 状态 | 说明 |
|------|------|------|
| Hermes 排名第一准则固化 | ✅ | 宪章 + 日循环 Celery |
| 去 AI 味 + Princeton GEO 写作战术 | ✅ | `geo_writing_policy.py` + 内容矩阵 humanize |
| 平台数 × 排名优先发布顺序 | ✅ | `platform_rank_registry` + discovery API |
| 公开技术资料脱敏引用 | ✅ | `public_tech_reference_service` |
| 多引擎 recommend 探针（API 类） | ✅ | 豆包/通义/DeepSeek/GPT/Gemini |
| 360/文心/元宝/Kimi 真实探针 | ⏳ | Sprint-GEO-R1 · HRANK-01~08 **仅设计，未编码** |
| `/platform` GEO 套餐与矩阵 | ✅（前序会话） | plan-catalog + 营销页 |

---

## 二、新建 / 主要改动文件

### 2.1 后端 · Hermes / GEO

| 路径 | 用途 |
|------|------|
| `backend/app/services/hermes/hermes_rank_first_constitution.py` | Hermes 存在第一准则 |
| `backend/app/services/hermes/daily_rank_ops.py` | 07:00 日循环：多引擎 probe + 战术雷达 + ECC 评审 |
| `backend/app/services/geo/multi_engine_rank_registry.py` | 百度/豆包/360/文心/元宝 分轨 |
| `backend/app/services/geo/platform_rank_registry.py` | 平台 GEO 权重 + 发布顺序 |
| `backend/app/services/geo/platform_discovery_service.py` | catalog vs live 缺口队列 |
| `backend/app/services/geo/public_tech_reference_service.py` | 专利/国标摘要脱敏 → GEO 成稿 |
| `backend/app/services/geo/geo_writing_policy.py` | 去 AI 味 + Princeton 战术评分 |
| `backend/app/tasks/geo_tasks.py` | `hermes_daily_rank_cycle` Celery 任务 |
| `backend/app/api/v1/routes/platform.py` | `GET /platforms/rank-priority` · `/discovery` |

### 2.2 文档（`docs/geo/`）

| 路径 | 用途 |
|------|------|
| `docs/geo/hermes-rank-first-charter.md` | Hermes 排名第一准则全文 |
| `docs/geo/research-geo-ranking-claims-2026.md` | 国内外 GEO 说法调研 |
| `docs/geo/sprint-geo-r1-hrank-task-design.md` | **HRANK-01~08 任务拆分（先设计后编码）** |

### 2.3 单测

| 路径 | 覆盖 |
|------|------|
| `tests/unit/test_hermes_daily_rank_ops.py` | 日循环 smoke |
| `tests/unit/test_platform_rank_discovery.py` | 排名注册表 + 脱敏 |
| `tests/unit/test_geo_writing_policy.py` | AI 味评分 |

---

## 三、每日自动化编排（Celery Beat 需注册）

| 时间 | 任务名 | 说明 |
|------|--------|------|
| **07:00** | `hermes_daily_rank_cycle` | **排名第一准则主循环** |
| 08:00 | `geo_tech_radar_daily` | 公开源 + Tavily GEO 动态 |
| 09:00 | `geo_competitor_monitor` | 竞品 recommend 监控 |
| 每 6h | `geo_rank_guard_check` | 收录/SEO 回归 |

快照 Redis：`hermes:rank_ops:latest` · 司令部：`command_center` → `hermes_rank_ops`

---

## 四、环境变量

```bash
HERMES_RANK_PROBE_KEYWORDS=品牌,品类,地区|...   # 可选
TAVILY_API_KEY=...                              # 外网 GEO/豆包/360 动态
AI_ARK_API_KEY=...                              # 豆包
AI_DASHSCOPE_API_KEY=...                        # 通义
AI_DEEPSEEK_API_KEY=...
```

---

## 五、Sprint-GEO-R1 待办（HRANK，未开工）

详见 [`docs/geo/sprint-geo-r1-hrank-task-design.md`](../geo/sprint-geo-r1-hrank-task-design.md)

| ID | 任务 | 阶段 |
|----|------|------|
| HRANK-01 | 探针契约 + 适配器接口 | A |
| HRANK-02 | 文心 recommend MVP | A |
| HRANK-03 | 探针历史 + 看板 | A |
| HRANK-04~06 | 360 / 元宝 / Kimi | B |
| HRANK-07 | 并入日循环 | B |
| HRANK-08 | QA 门禁 + 售卖诚实边界 | B |

**编码前待拍板**：D1 文心 API vs Playwright · D2 staging 容器 · D3 存储 · D4 租户可见度 · D5 360 入口 URL

---

## 六、业务口径（对内）

- **不卖**：「40 平台全通」「保证 AI 前三」  
- **卖**：独立站资产 + 可复盘 probe/询盘 + 矩阵复利  
- **6 万自投**优于 6 万代运营：投 API/1 条视频主渠道/1 条 B2B 低配，不堆平台 VIP  

---

## 七、验证命令

```powershell
cd C:\Users\97907\Desktop\上线网站\backend
python -m pytest tests/unit/test_hermes_daily_rank_ops.py tests/unit/test_platform_rank_discovery.py tests/unit/test_geo_writing_policy.py -q
```

本地 API（需起 `:8001`）：

- `GET /api/v1/platforms/rank-priority?region=cn`
- `GET /api/v1/platforms/discovery`

---

## 八、Git 状态说明

本批改动 **未统一 commit**（按仓库规则需创始人明确要求再提交）。换 IDE / 换人前请 `git status` 确认未提交文件列表。
