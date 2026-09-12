# UBrain + DeerFlow 融合获客智能体 × Accio 工作台

> 2026-05-25 · 回答：这样组合**能否加快获客**  
> **结论**：能加快 **执行速度**（内容、发布、回询盘草稿），从而放大您日更/推流的效果；**不能替代**备案、HTTPS、接电话。无成绩前对外称「试点副驾」，不吹三方名字。

---

## 一、融合后是什么（一个对外名）

**对外建议名**：**优丁卖货副驾**（对内代号：UBrain-X）

| 层 | 技术 | 干什么 |
|----|------|--------|
| **壳（Accio 形态）** | `/client/copilot` 单页 | 一句话下单、任务卡片、**发送/发布前必须点确认** |
| **脑（UBrain-X）** | 现有 `UBrainOrchestrator` 扩展 | 懂意图：获客/回询盘/发文/GEO/SSL/出口 |
| **手（DeerFlow 2.0）** | 旁路部署，Docker 沙箱 | 长任务：一夜 N 篇 FAQ、批量变体、周报 PDF |
| **账本（本系统）** | FastAPI + `inquiries` + 发布队列 | 唯一真相：线索、来源、订单、Token |

**不是三个产品叠 logo**，是 **一个副驾 + 一个执行引擎 + 您的卖货 OS**。

---

## 二、能否加快获客？— 分时间看

| 时间 | 不加融合 | 加融合（接好工具+您人审） |
|------|----------|---------------------------|
| **第 1～2 周** | 建站慢、文写得慢 | **略快**：FAQ/llms 批量草稿、询盘分级；电话仍靠您推流 |
| **第 3～4 周** | 日更耗您 3～4 小时/天 | **快 1～2 小时/天** → 可多推 1 条视频或接更多电话 |
| **第 2～3 月** | SEO 复利一般 | **内容产能稳定** → 长尾词、矩阵更易坚持 |

**地板不变**：第 1 月 **0 推流仍≈0 电话**；融合不能把 6980 GEO 半个月 magically 复制，除非执行清单等价。

**加快的本质**：让您这家 **保温厂** 用更少时间完成「6980 包里的活」，把省下的时间用于 **出镜、接电话、老客转化**。

---

## 三、融合智能体 — 6 个获客工具（DeerFlow Skill = 本系统 API）

| 工具 ID | 触发话术示例 | DeerFlow 做 | 写回系统 |
|---------|--------------|-------------|----------|
| `lead_content_pack` | 「今晚生成 10 篇保温长尾」 | 写稿、落盘 | CMS 草稿待审 |
| `geo_submit_pack` | 「按 GEO 清单检查本站」 | llms.txt、FAQ 结构检查 | 运维勾选表 |
| `matrix_publish` | 「把这篇发到我勾的 3 平台」 | 调发布 Worker（或导出待人工发） | `publish_tasks` |
| `inquiry_score` | 「这条询盘多高意向」 | 读 `inquiries` 分析 | 分级+跟进建议 |
| `inquiry_reply_draft` | 「用英文回这条」 | 草稿 | **人点发送** |
| `weekly_lead_report` | 「本周线索复盘」 | CSV+一句话 | 给您/政府附件 |

**禁止自动**：对外发短信、自动砍价、自动扣 Token 大额、未确认发布。

---

## 四、架构（落地不重写）

```text
用户（Accio 单页）
    → POST /api/v1/ubrain-x/chat
        → 短任务：Orchestrator 直接调 Service
        → 长任务：入队 deerflow_job_id，轮询状态
    → DeerFlow 沙箱内 Skill 调 https://您的域/api/v1/...
    → 结果回显 + 写入 inquiries / content / publish
```

**Phase 0（2 周）**：不部署完整 DeerFlow 也可 — Orchestrator 直接调现有 API，DeerFlow 仅本地帮您跑「一夜 10 篇」.  
**Phase 1（4 周）**：DeerFlow 与生产 API 联通 + 任务队列。

---

## 五、与 Accio Work 的关系

| Accio 有 | 我们 Phase 0～1 |
|----------|-----------------|
| 国际站私有插件 | **不做**，除非合作 |
| 桌面 Electron | 可选后期；**先做 Web 副驾** |
| 浏览器 CDP 自动发帖 | **5+5 试点 + 人审**；合规优先 |
| 工作台 + 确认门 | **必做**（Accio 形态） |

---

## 六、对产品 / 营销 / 技术各一句

- **产品**：对外只卖 **「卖货副驾 + 网站 + 线索进后台」**；融合是交付加速器，不是新 SKU 名堆砌。  
- **营销**：保温厂试点话术：「副驾帮您连夜写稿，您白天发视频、接电话。」  
- **技术**：P0 仍是 HTTPS、手机必填、来源、导出；融合不插队这些。

---

## 七、验收（谦逊）

| 指标 | 4 周内 |
|------|--------|
| 副驾完成 ≥1 次 `lead_content_pack` 且您审后上线 | 是/否 |
| ≥1 条真实手机号进 `inquiries` 且 `source_channel` 有值 | 是/否 |
| 您主观：比不用副驾 **每周少干 ≥3 小时文案** | 是/否 |

三条有其二 → 融合值得继续；全否 → 先修 P0，不扩 DeerFlow。

---

## 八、2026-05-25 Phase 0 已落地（后端）

已在 `UBrainOrchestrator` 中接入可供 Accio 工作台调用的获客工具：

- `lead_content_pack`：保温/建材长尾 FAQ 获客内容包计划
- `geo_submit_pack`：HTTPS、手机号、llms.txt、FAQ、结构化数据、百度提交清单
- `matrix_publish`：3～5 平台矩阵发布计划，**需人工确认**
- `inquiry_score`：询盘意向高/中/低分级与下一步建议
- `weekly_lead_report`：按租户统计线索样本、手机号数量、状态与来源

同时修正线索数据质量底座：

- 周报按 `tenant_id` 过滤，避免跨租户泄露
- 公开询盘不再把 `email` 或 `"web"` 写入 `phone`
- 公开询盘可使用传入 `merchant_id` 归属商家
- 统一序列化输出 `source_channel`

验证命令：

```powershell
$env:JWT_SECRET_KEY='test-jwt-secret-key-for-ubrain-phase0-1234567890'
python -m pytest backend/tests/unit/test_ubrain_trade_intel.py
```

结果：`10 passed`（仅有既有 Pydantic/SQLAlchemy deprecation warnings）。

**仍未完成**：

- `/client/copilot` Accio 形态前端单页
- DeerFlow 独立队列与 Docker 沙箱执行
- 真实 CMS 草稿写入、真实发布 Worker 调用
- 询盘手机号必填的前端/公开接口强校验

---

## 相关

- `DeerFlow-Accio-本系统-验真话术与30天指标.md`
- `自有保温厂-30天试点与生存链.md`
- `docs/UBrain-统一调度大脑-产品规格.md`
