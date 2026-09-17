---
feature: acquisition-reply-intent
status: delivered
updated: 2026-09-18
branch: feat/acquire-mobius-20260918
commits: d657dcc6..HEAD
---

# 回复意图判断与阶段入卡（compose-next#4）


## Report

**What was built** — 回复意图判断：规则分类（压价/要报价/要样/付款/认证/数量港/流失风险/泛意向/unknown）→ 建议阶段与下一步话术；reply-ingest 返回 intent_analysis 并写入跟单卡 stage/next_action；已 lost 不被普通回复覆盖；前端作战台展示意图判断。

**Verification** — `pytest tests/unit` **58 passed**（评审修复后）；硬锁未破。

**Journey log**
1. lost 保护必须在 API 层，materialize 会覆盖 stage。
2. 前端引用常量/ref 必须在 script 中先定义，否则运行即崩。
3. talk_track 要进 UI 提示，不能只写进 tips 数组。
4. 规则意图 unknown 诚实降级，后续可换成 LLM 同接口。
## [S1] Problem

作战台能建卡，但客户消息只进了「联系」摘要，**系统不知道对方想干什么**，下一步建议固定一句，不够「傻子都行」。需要：自动判断意图 → 建议阶段 → 建议动作/话术，写入跟单卡。

## [S2] Design

**工作区**：沿用 `agents-acquire-mobius-20260918-011631`。

**契约**：

1. `services/acquisition/intent_classifier.py`
   - `classify_reply(text, country="") -> dict`
   - 输出：`{intent, stage_suggestion, confidence, reason, next_action, talk_track}`
   - 意图枚举（规则优先，诚实）：`price_haggling` / `request_quote` / `request_sample` / `payment_discuss` / `cert_insist` / `quantity_port` / `reject_competitor` / `generic_interest` / `unknown`
   - 匹配中英关键词（price/报价/便宜、sample/样品、T/T/定金/付款、SASO/认证/CIF、qty/moq/柜、同行/别家…）
   - 无命中 → `unknown` + 通用 next_action（资格四问），**不编造意图**
   - stage 映射：quote 路径→`qualifying/quoted`，sample→`sampling`，payment→`negotiating`，reject→`lost_risk`，generic→`engaged`

2. `reply-ingest` API
   - 对 `message` 调 `classify_reply`
   - materialize 时带 `stage=stage_suggestion`（若现卡 stage 已是 lost 则不覆盖）
   - `next_action` 用分类结果，否则默认资格四问
   - talk_track 追加进 card.playbook_tips
   - 响应增加 `intent_analysis`

3. 前端 `acquisition-ops.vue`
   - 展示「意图判断：xxx · 建议阶段 yyy」+ reason/talk_track
   - 不改硬锁

4. 测试
   - price/sample/payment/reject/unknown 各 1 例
   - reply-ingest 响应含 intent_analysis 且 card.stage 符合映射
   - 旧测不回归

5. 硬锁：ROUTE_PREFIX、鉴权、登录/壳/薄荷不变

## [S3] Out of Scope

- LLM 意图分类（后续可替换同一接口）
- 多语言全量词典
- 合并 main

## Tasks

- [x] T1: intent_classifier — acceptance: 规则分类表 + unknown 诚实 (covers: S2.1)
- [x] T2: reply-ingest 接线 — acceptance: 响应 intent_analysis；stage/next_action 更新 (covers: S2.2)
- [x] T3: 前端展示 — acceptance: 作战台显示意图与建议 (covers: S2.3)
- [x] T4: 测试全绿 — acceptance: 新测+旧测 PASS (covers: S2.4)
- [x] T5: spec/大脑 — acceptance: delivered (covers: S2; depends: T4)
