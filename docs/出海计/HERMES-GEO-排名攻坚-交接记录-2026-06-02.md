# Hermes · GEO 排名攻坚 — 交接记录（2026-06-02）

> **交接时间**：2026-06-02  
> **交接方**：Cursor Agent（上线网站仓）  
> **接收方**：下一 IDE / 后端 Lane E / PM-07  
> **开发记录**：[HERMES-GEO-排名攻坚-开发记录-2026-06-02.md](./HERMES-GEO-排名攻坚-开发记录-2026-06-02.md)

---

## 一、30 秒读懂

1. **Hermes 第一准则**：排名效果 > 其它运维；无 probe → 无电话 → 无续费。  
2. **已落地**：07:00 日循环骨架、去 AI 味成稿、平台排名优先、多引擎注册表（豆包/通义等 API 探针）。  
3. **未落地**：360 / 文心 / 元宝 / Kimi 真实探针 → **Sprint-GEO-R1（HRANK-01~08）先设计完，等 D1–D5 拍板再编码**。  
4. **知识库**：本文 + geo 文档已同步到桌面 `出海计`（跑 sync 脚本）。

---

## 二、接手人第一件事

| 序 | 动作 | 路径/命令 |
|----|------|-----------|
| 1 | 读 Hermes 宪章 | `docs/geo/hermes-rank-first-charter.md` |
| 2 | 读任务拆分 | `docs/geo/sprint-geo-r1-hrank-task-design.md` |
| 3 | 确认 D1–D5 决策 | 文心 Key？staging Playwright？ |
| 4 | 跑单测 | `pytest tests/unit/test_hermes_daily_rank_ops.py -q` |
| 5 | 开 HRANK-01 PR | 仅探针契约 + mock |

---

## 三、关键 API / 模块索引

| 能力 | 入口 |
|------|------|
| 日排名攻坚 | `hermes/daily_rank_ops.py` · Celery `hermes_daily_rank_cycle` |
| 多引擎分轨 | `geo/multi_engine_rank_registry.py` |
| 平台发布顺序 | `GET /api/v1/platforms/rank-priority` |
| 平台缺口发现 | `GET /api/v1/platforms/discovery` |
| GEO 成稿（去 AI 味） | UBrain intent `geo_content_matrix` |
| 司令部快照 | `command_center` → `hermes_rank_ops` |
| ECC 排名专家 | `ecc_expert_panel` · `geo-rank-strategist` |

---

## 四、Celery Beat 配置提醒

若生产/staging **未注册** `hermes_daily_rank_cycle`，07:00 循环不会跑。  
任务定义：`backend/app/tasks/geo_tasks.py`  
与 `geo_tech_radar_daily` / `geo_rank_guard_check` 一并注入 Beat。

---

## 五、售卖与对外口径（勿越界）

- `/platform` 与 plan-catalog 已含 GEO 能力项；**probe_ready 外平台不得写「已监测」**。  
- `promise_boundary`：不承诺具体排名，承诺可复盘信号 + 询盘资产。  
- HRANK-08 完成前勿对外说「全入口 AI 排名监测已上线」。

---

## 六、同步到出海计知识库

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\97907\Desktop\上线网站\scripts\sync-to-chuhaiji-kb.ps1"
```

个人收工笔记（不覆盖）：`C:\Users\97907\Desktop\出海计\records\IDE-交接记录.md`

---

## 七、风险与阻塞

| 风险 | 缓解 |
|------|------|
| 文心/360 无 API Key | HRANK-02/04 走 bounded Playwright（仅 staging） |
| 大模型蒸馏导致 probe 漂移 | 日更 + Tavily 战术雷达 + 昨日对比回归告警 |
| 平台年费 vs 利润 | 排名优先 live 平台；exploration 队列按 geo_weight 建设 |
| 未 commit 代码丢失 | 接手后先 `git status` /  Founder 定是否提交 |

---

## 八、下一里程碑

| 里程碑 | 标志 |
|--------|------|
| M0 | D1–D5 拍板 ✅ |
| M1 | 文心 probe MVP + 司令部 7 日趋势 |
| M2 | staging Celery 07:00 连续 7 天 |
| M3 | 360/元宝/Kimi 再 live ≥2 |
| M4 | HRANK-08 过 gate，售卖文案对齐 |

---

## 九、相关对话主题（创始人决策链）

- 不堆 6980 GEO + 1688/慧聪/6 万代运营年费 → 自研 + AI 员工编排  
- 平台数与排名相关 → 持续 discovery + live 适配器  
- 专利/国标公开事实 → 脱敏改写，非照搬权利要求  
- 豆包/360/百度机制不同 → Hermes + ECC **每日**攻坚，非一次性功能  
