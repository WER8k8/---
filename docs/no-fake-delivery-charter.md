# 禁止假交付宪章（No-Fake Delivery Charter）

> **签发**：PM-07 + QA-02  
> **生效**：永久 · 机器规则：`.cursor/rules/01-no-fake-delivery-hardgate.mdc`  
> **门禁脚本**：`scripts/validate-no-fake-delivery.py`

---

## 一、背景

客户付费场景（矩阵发布、出口开通、自动谈单、询盘、推送）若返回假接口/假成功/假数据，等同于欺诈性交付。ECC 各 Lane 设计与实现 **一律遵守本宪章**。

---

## 二、定义

| 术语 | 定义 |
|------|------|
| **假接口** | 路由存在且 200，但内部无实现（TODO 模板、硬编码 JSON、永远成功） |
| **假成功** | 业务层宣称成功，但无可验证副作用（无作品 URL、无上游 ref、无 message_id） |
| **假数据** | 用 stub /generator 数据当作生产探测或统计结果展示给客户 |
| **生产路径** | `ENVIRONMENT=production` 或租户可见 API/后台页面默认链路 |
| **真实证据** | 上游响应片段、DB 行、第三方 ID、可复现脚本 |

---

## 三、铁律（不可谈判）

1. **能失败就必须失败** — 条件不满足时返回 4xx/5xx + `error_code`，禁止「温柔」200。
2. **成功必须可验证** — 每条成功状态对应至少一个可核对字段（见下表）。
3. **Stub 不得冒充生产** — 开发 Mock 必须显式标记，且不得写入客户可见终态。
4. **一条失败路径** — 每个 Lane 交付须有测试或脚本证明失败时不会假成功。

### 成功可验证字段（最低要求）

| 能力 | 成功必要条件 |
|------|----------------|
| 视频发布 | `platform_post_url`（http）或可核对 `platform_post_id` |
| egress 开通 | 非占位 host、`port>0`、账密非空、`upstream_ref` |
| 询盘入库 | 真实 `phone` 或渠道方唯一 ID |
| 自动谈单回复 | 平台侧发送回执或 Worker 日志 + `interaction_id` |
| 推送 | 企微/WhatsApp `msgid` 或 API 明确成功体 |
| 收录探测 | `probe_mode=real` 且探测来源可追溯；stub 不计入 included |

---

## 四、已有收口（复用，禁止绕过）

- 发布：`publish_capability_registry.normalize_publish_result`
- 支付 mock：`PAYMENT_ALLOW_MOCK` + `ENVIRONMENT` 门控
- egress mock：仅 `EGRESS_PROVIDER=mock` + `.mock-egress.local`

新代码 **必须** 复用同等模式或新增 `app/core/no_fake_delivery.py` 助手。

---

## 五、R2 Lane 设计约束

| Lane | 禁止 | 必须 |
|------|------|------|
| I 社媒谈单 | 未拉评却显示「已回复」 | `SocialInteraction.status` 状态机：pending→sent/failed |
| P 推送 | 仅写 DB「已通知」 | 调用企微 API 失败则 `failed` + 重试队列 |
| D 询盘 | 伪造手机号 | 校验格式 + 来源渠道 |
| A egress | 无余额仍 assigned | 上游失败 → `slot_status=failed` + `provision_error` |
| B 发布 | 跳过验真 | Hermes 仍以 `verified_posts` 为准 |

---

## 六、QA 门禁（全量深度扫描）

```powershell
python scripts/validate-no-fake-delivery.py
```

扫描范围：`backend/app/**/*.py` + `frontend/admin/src/**/*.{vue,ts}`  
报告：`docs/no-fake-delivery-scan-latest.json`

- **P0**：生产路径假接口/假成功/假数据 → **阻塞合并**
- **P1**：dev mock 未标记或 `mock:true` 未门控 → 限期修复
- **P2**：已门控 Mock、明示演示区（彩排/营销示意）→ 记录不阻塞

### 底层硬拒绝（运行时）

| 层 | 模块 | 行为 |
|----|------|------|
| 后端出站 | `app/core/no_fake_delivery_middleware.py` | `ENVIRONMENT=production` 时扫描所有 `/api/*` JSON 200 响应，命中未门控 mock → **503 FAKE_DELIVERY_BLOCKED** |
| 后端异常 | `NotConfiguredError` / `FakeDeliveryViolation` | 全局 503，禁止假成功 |
| 后端助手 | `app/core/no_fake_delivery.py` | `stamp_mock` / `mock_allowed` / `dev_mock_or_raise` |
| 前端 API | `utils/noFakeDelivery.ts` + `utils/api.ts` | 生产构建拒绝 `mock:true`/`data_source:mock`；`persistentGet` 禁止 localStorage 冒充实盘 |
| CI | `npm run cert:gate` | 聚合 `validate-no-fake-delivery.py` |

与 `cert:gate` 并列；QA-02 周报须带扫描结果。

---

## 七、PR 四行摘要模板（强制）

```
任务 ID + 目标
做法（1–3 句）
验收证据（脚本/测试路径，含一条失败路径）
Out-of-Scope / 明确未假装的未实现项
```

---

*ECC · No-Fake Delivery Charter v1 · 永久生效*
