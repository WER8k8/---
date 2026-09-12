# GEO 多引擎探针攻坚 · 任务拆分设计（先设计后编码）

> **签发**：PM-07 · 对齐 [`hermes-rank-first-charter.md`](./hermes-rank-first-charter.md)  
> **批次代号**：**Sprint-GEO-R1**（Hermes 排名第一准则落地二期）  
> **原则**：先拆分、评审、接口冻结 → 再并行编码；**不对外承诺「全入口已覆盖」直到 probe MVP 验收**

---

## 一、北极星与边界

| 项 | 内容 |
|----|------|
| **北极星** | 360 / 文心 / 元宝 / Kimi 从 `exploration` → **可日复测的 recommend 探针**，并入 `hermes_daily_rank_cycle` |
| **第一准则** | Hermes 存在意义 = 排名效果；无 probe 数据 = 不能写进 `/platform` 售卖文案 |
| **不测什么** | 不承诺具体排名名次；不自动发稿；不绕过登录/验证码/robots 批量爬 |
| **收益链** | probe 通过率 ↑ → 运营知缺口 → 内容/平台补强 → 询盘电话 ↑ → 开户续费 |

---

## 二、现状基线（编码前共识）

| 能力 | 状态 | 路径 |
|------|------|------|
| 日更排名主循环 | ✅ 骨架 | `hermes/daily_rank_ops.py` · Celery `hermes_daily_rank_cycle` |
| API 探针（豆包/通义/DeepSeek/GPT/Gemini） | ✅ | `geo_engine_service.py` · `probe_mode=recommend` |
| 多引擎注册表 | ✅ exploration 标记 | `multi_engine_rank_registry.py` |
| 360/文心/元宝/Kimi | ⏳ exploration | `probe_via=headless_exploration` |
| 无头服务端 Playwright | ❌ 未建 | 仅有 `browser_companion` 本地扩展 |
| 百度 classic SERP | 🔄 分轨 | SEO 矩阵 / 站长，非 GEOEngine |

---

## 三、任务总览（8 项 · 3 泳道 · 2 阶段）

```
Phase A（接口 + 1 个 MVP 引擎）─────── 可并行 ────┐
  HRANK-01 探针契约冻结                              │
  HRANK-02 文心 MVP（优先：百度系、国内 B2B）         ├──→ HRANK-07 并入日循环
  HRANK-03 探针结果存储与看板                         │
Phase B（扩展 + 合规）──────────────── 依赖 A ────┤
  HRANK-04 360 纳米 MVP                              │
  HRANK-05 元宝 MVP                                  │
  HRANK-06 Kimi MVP                                  │
  HRANK-07 日循环与 ECC 评审对接                      │
  HRANK-08 QA 门禁与售卖边界                          │
```

| ID | 任务 | Lane | 阶段 | 并行 | 预估 |
|----|------|------|------|------|------|
| **HRANK-01** | 多引擎探针契约与适配器接口 | E 后端 + H PM | A | ✅ 与 02 可并行（02 消费契约） | 1d |
| **HRANK-02** | 文心一言 recommend 探针 MVP | E 后端 | A | ✅ | 2–3d |
| **HRANK-03** | 探针结果持久化 + 司令部/租户看板 | B 前端 + E | A | ✅（依赖 01 字段） | 2d |
| **HRANK-04** | 360/纳米 AI 探针 MVP | E 后端 | B | 与 05/06 可并行 | 2–3d |
| **HRANK-05** | 腾讯元宝探针 MVP | E 后端 | B | 同上 | 2–3d |
| **HRANK-06** | Kimi 探针 MVP | E 后端 | B | 同上 | 2d |
| **HRANK-07** | 接入 `hermes_daily_rank_cycle` + 回归告警 | E + H Hermes | B | 依赖 02 至少 1 个 | 1d |
| **HRANK-08** | QA 门禁 + plan/catalog 诚实边界 | F QA + G 合规 | B | ✅ | 1d |

**建议开工顺序**：HRANK-01 →（HRANK-02 ∥ HRANK-03）→ HRANK-07 →（HRANK-04 ∥ HRANK-05 ∥ HRANK-06）→ HRANK-08

---

## 四、分项任务卡（In / Out / Interface / 验收）

### HRANK-01 · 多引擎探针契约冻结

| 栏 | 内容 |
|----|------|
| **In-Scope** | 定义 `TrafficEngineProbeAdapter` 协议；统一入参/出参 JSON；扩展 `multi_engine_rank_registry` 的 `probe_via` 路由 |
| **Out-of-Scope** | 具体 360/文心实现；前端页面 |
| **Interface** | 入参：`brand, product_category, region, probe_mode=recommend`；出参：`status, rank_position, mentions_brand, confidence, engine_id, probe_method, latency_ms, error_code` |
| **交付物** | `backend/app/services/geo/engine_probe/` 包 + `docs/geo/engine-probe-contract.md` |
| **验收** | 单测 mock 适配器；`GEOEngine` 与 headless 适配器返回同形 dict |
| **主责** | 后端架构 |

---

### HRANK-02 · 文心一言 recommend 探针 MVP（Phase A 首选）

| 栏 | 内容 |
|----|------|
| **Why 文心先** | 百度系；与国内工地集采 / 百家号长尾同一生态；蒸馏风险高，需最先监测 |
| **In-Scope** | 方案二选一（PR 须写明选型）：**A)** 千帆/文心 OpenAPI（若已有 Key）；**B)** 隔离环境 Playwright 只读问句（固定 3 条 probe 模板，人工 Cookie 池，不超 QPS） |
| **Out-of-Scope** | 自动登录破解；租户侧暴露 Hermes；批量爬 SERP |
| **Interface** | 实现 `WenxinProbeAdapter`，注册到 `engine_id=wenxin` |
| **验收** | 对 `default_probe_keywords()` 至少 2 个品类跑通；结果写入 Redis 日快照；`exploration` → `geo_engine` 或 `headless_bounded` |
| **失败路径** | 无 Key / 无 Cookie → `status=not_configured`，不 fake success |
| **主责** | 后端 BE Lane E |

---

### HRANK-03 · 探针结果存储与看板

| 栏 | 内容 |
|----|------|
| **In-Scope** | DB 或 Redis 结构化历史（按 engine×keyword×day）；超管司令部展示 `hermes_rank_ops` + 7 日趋势；可选租户 `/client` 只读「我的品牌 probe 通过率」 |
| **Out-of-Scope** | 改 plan 计费；新建后端 CRUD API（租户只读聚合即可） |
| **Interface** | `GET /admin/geo-engine/multi-probe/history`（超管）；复用 `command_center` 字段 |
| **验收** | 可看到文心 MVP 接入前后通过率对比；导出 CSV |
| **主责** | 前端 B + 后端 E 各半 |

---

### HRANK-04 · 360 / 纳米 AI 探针 MVP

| 栏 | 内容 |
|----|------|
| **In-Scope** | `Qihoo360ProbeAdapter`；纳米 AI 搜索页或开放能力（调研 0.5d 写进 PR 首段） |
| **Out-of-Scope** | 360 广告投放 API；与百度 probe 混用 |
| **Interface** | 同 HRANK-01 契约 |
| **验收** | 1 个建材品类 recommend 探针可复现；合规说明写入 `COMP-06` memo |
| **依赖** | HRANK-01；Playwright 基础设施（若 02 选 B 则复用） |
| **主责** | 后端 E |

---

### HRANK-05 · 腾讯元宝探针 MVP

| 栏 | 内容 |
|----|------|
| **In-Scope** | `YuanbaoProbeAdapter`；强调微信生态问法模板（与公众号/视频号内容口径联动） |
| **Out-of-Scope** | 微信私有 API；自动发公众号 |
| **验收** | probe 结果含 `social_signal_note` 可选字段（是否提及微信生态，人工标注 10 条校准） |
| **主责** | 后端 E |

---

### HRANK-06 · Kimi 探针 MVP

| 栏 | 内容 |
|----|------|
| **In-Scope** | Moonshot API 优先；无 Key 则 bounded headless |
| **Out-of-Scope** | 长文全文抓取 |
| **验收** | 出口英文品类 probe 1 条通过 |
| **主责** | 后端 E |

---

### HRANK-07 · 并入 Hermes 日循环 + ECC 评审

| 栏 | 内容 |
|----|------|
| **In-Scope** | `daily_rank_ops._run_multi_engine_probes` 调用统一 adapter 路由；`exploration_engines` 动态缩短；ECC `geo-rank-strategist` 对 **新引擎首次上线** 强制 readonly review |
| **Out-of-Scope** | 改 Celery Beat 以外调度；自动 remediation |
| **验收** | 07:00 任务日志含 wenxin（及后续引擎）；回归 >5% 触发飞书 |
| **主责** | Hermes / 后端 E |

---

### HRANK-08 · QA 门禁与售卖诚实边界

| 栏 | 内容 |
|----|------|
| **In-Scope** | `cert:gate` 或等价脚本：probe 不得 fake success；`plan-catalog` / `/platform` 仅展示 **probe_ready** 引擎；MOD-03 平台数诚实文案 |
| **Out-of-Scope** | 改定价 |
| **验收** | QA-02 清单 + 截图；P0/P1=0 方可称「多引擎监测上线」 |
| **主责** | QA F + 合规 G |

---

## 五、泳道分配（蜂群并行）

| Lane | 任务 ID | 说明 |
|------|---------|------|
| **E 后端** | HRANK-01,02,04,05,06,07 | 探针适配器 + Hermes 对接 |
| **B 前端** | HRANK-03 | 司令部/租户看板 |
| **F QA** | HRANK-08 | 假成功门禁 |
| **G 合规** | HRANK-04,08 | 无头抓取合规 memo |
| **H PM/文档** | HRANK-01 契约评审, 本文件, tracker 刷新 | 不代写 Lane 实现 |

**冲突仲裁**：HRANK-01 与 HRANK-02 若同改 `geo_engine_service.py` → **先合并 01 契约 PR，再开 02**。

---

## 六、技术选型决策点（编码前必须拍板）

| 决策 | 选项 | 建议 | 决策人 |
|------|------|------|--------|
| D1 文心接入方式 | API vs bounded Playwright | **有千帆 Key 则 API 优先**；否则 Playwright + 人工 Cookie 池 | 创始人 + 后端 |
| D2 Playwright 运行位置 | 本机 worker vs 隔离 Docker | **staging 隔离容器**，禁止生产裸爬 | 架构 ARCH |
| D3 探针历史存储 | Redis only vs DB 表 | **Redis 90d + 可选 `geo_probe_snapshots` 表** | 后端 |
| D4 租户可见度 | 仅超管 vs 租户只看自己的 | **Phase A 仅超管**；Phase B 租户聚合只读 | PM + SaaS |
| D5 360 入口 URL | 纳米 AI vs 360 搜索 | 调研 0.5d 后写入 HRANK-04 PR | 调研岗 |

---

## 七、里程碑

| 里程碑 | 日期（建议） | 标志 |
|--------|--------------|------|
| **M0 设计评审** | +0d | 本文 + D1–D5 拍板 |
| **M1 Phase A** | +5 工作日 | 文心 probe MVP + 契约 + 司令部趋势 |
| **M2 日循环** | +7 工作日 | HRANK-07 上线 staging Celery |
| **M3 Phase B** | +12 工作日 | 360/元宝/Kimi 至少 2 个 additional live |
| **M4 售卖诚实** | +14 工作日 | HRANK-08 过 gate；`/platform` 文案对齐 |

---

## 八、环境变量（设计预留）

```bash
# 已有
AI_ARK_API_KEY          # 豆包
AI_DASHSCOPE_API_KEY    # 通义
HERMES_RANK_PROBE_KEYWORDS

# Phase A/B 新增（名称待定，实现时写入 .env.example）
AI_WENXIN_API_KEY       # 或 WENXIN_QIANFAN_AK/SK
AI_KIMI_API_KEY
GEO_HEADLESS_ENABLED=0  # staging 才 1
GEO_HEADLESS_COOKIE_POOL_PATH=...
GEO_PROBE_QPS_LIMIT=6
```

---

## 九、tracker 登记（待 PM-07 刷新）

```json
{
  "id": "HRANK-01",
  "pct": 0,
  "lane": "E",
  "phase": "A",
  "blocked_by": []
}
```

建议写入 `docs/pm-dev-task-progress.json` 与 `docs/ecc-delivery-tracker.md` 新章节 **Sprint-GEO-R1**。

---

## 十、下一步（你确认设计后）

1. **拍板 D1–D5**（尤其文心 API 有没有 Key、Playwright 能不能上 staging）  
2. **开 HRANK-01 PR**（仅契约 + mock，1 天）  
3. **并行 HRANK-02 + HRANK-03**（文心 MVP + 看板骨架）  
4. **staging 跑满 7 天日循环** → 再动 HRANK-04/05/06  

**未确认设计前不写生产代码。**
