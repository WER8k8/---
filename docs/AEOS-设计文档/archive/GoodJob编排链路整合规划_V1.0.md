# GoodJob 编排链路能力嫁接优丁 · 技术整合规划 V1.0

> 目标：把 GoodJob CRM 验证过的"紧实执行链路"工程模式嫁接到优丁（AI Global Growth OS），补齐四条链路（文章生成与分发 / 视频生成与分发 / 邮件发送与跟进 / 多平台同步分发）中**缺失的两个质量关卡：内容清洗、人工/自动复核**。
> 基准：冻结架构（Control Plane = 优丁单体；Hermes 内层编排；ECC 专家层；DeerFlow/n8n/Browser 平级 Adapter；Validator→Evidence→Experience Engine 闭环；租户隔离优先；Skill 版本化）。
> 本文仅规划，不含任何代码修改。

---

# 一、现状差距诊断（实测证据）

## 1.1 优丁四条链路的现有家底

| 链路 | 已有模块 | 现状评价 |
|---|---|---|
| 文章生成与分发 | `content_master_publish_service`、`content_service`、`content_scorer`、`eeat_scorer` | 生成强，**发布前关卡弱** |
| 视频生成与分发 | `video_publish_orchestrator`、`video_publish_router`、`media_factory_service`、`video_bind_hub_service` | 编排有，**复核与证据弱** |
| 邮件发送与跟进 | `email_queue_service`、`email_send_service`、`follow_up_engine`、`drip_sequence_service`、`email_tracking_service` | 最完整，但缺统一清洗/复核门 |
| 多平台同步分发 | `unified_publish`、`publish_dispatch_service`、`publish_queue_service`、`scheduled_publish_retry_service`、`publish_readiness_service`、`publish_result_notify_service` | 调度与重试有，**缺步级证据与审批** |

另有零散质量件：`hermes/brand_guard`（sanitize_public_copy）、`quality_gate_service`、`compliance_scanner`、`publish_preflight_checklist_service`、`paperclip/approval_gate`、`budget_guard`。

## 1.2 结论：缺的不是零件，是"强制链路"

质量件散落各处、各自可选，**没有一条被强制执行的流水线**把"清洗→复核→审批→分发→验证→留证"串成不可跳过的关卡。对照 GoodJob 获客闭环的实测设计：

| GoodJob 有（实测） | 优丁缺失 |
|---|---|
| 候选数据先清洗再进复核队列（`prospect-candidate-pipeline`） | 发布物无强制清洗关卡 |
| 复核是独立阶段，有通过/驳回/修改三态 | 复核要么跳过要么无状态记录 |
| 执行 checkpoint + lease（单泳道并发锁） | 发布任务断点恢复靠重试整单 |
| 幂等别名表（`agent_job_idempotency_aliases`） | 幂等分散、不统一 |
| Provider 请求台账 + 记账证据（`accounting_evidence`） | 分发步级证据缺失 |
| 审批图（`iam/approval-graph`，多级/委托/代理） | 仅 paperclip 单级 approval_gate |
| 每步失败有界（重试上限→死信→人工） | 部分链路无限重试风险 |

---

# 二、技术决策：三方案对比

## 2.1 关键前提

用户的核心诉求是**加固优丁自己的四条内容链路**。GoodJob 的紧实链路长在它的"获客域"里，**它无法替优丁分发文章/视频/邮件**——所以"整仓引入"只能解决获客闭环问题，解决不了本次诉求。这决定了推荐方向。

## 2.2 方案对比

| 维度 | A. TS→Python 全量转译 | B. 整仓引入原样运行 | C. 提取模式，Python 重建核心 |
|---|---|---|---|
| 能否加固优丁四链路 | ✅ 能 | ❌ **不能**（链路长在获客域） | ✅ 能 |
| 技术栈统一 | ✅ 纯 Python/PG | ❌ 双栈（Node+MySQL 常驻） | ✅ 纯 Python/PG |
| 工作量 | 6-10 周 | 2 周 | **3-4 周** |
| 运维复杂度 | 低 | 高（多一套服务/库/密钥） | 低 |
| 架构纯净度 | 高 | 中（外挂子系统） | **高** |
| 附带获得获客闭环 | ✅ | ✅ | ❌（可另行 B 方案补） |
| 与冻结基准冲突 | 无 | 无（Adapter 化） | 无 |
| 风险 | 转译失真、周期长 | 双栈长期维护成本 | 模式提炼需吃透源码 |

## 2.3 推荐结论

**主方案 = C（提取模式，Python 重建）**，理由：
1. 唯一能直接加固本次四条链路的方案；
2. 成本仅为 A 的 40%，且不引入双栈运维负担；
3. 提取的是"模式"而非代码——天然规避 GoodJob 代码层面的任何许可证/依赖牵连（Apache-2.0 允许参考，但重写后代码 100% 原创归属优丁）。

**并行可选 = B（整仓引入）**：仅当"获客闭环"本身也列为近期目标时启动（已在《嫁接融合可行性报告》给出方案，约 2 周）。两者互不冲突：C 建的是通用链路框架，B 的 GoodJob 实例将来也作为框架纳管的一个执行器。

---

# 三、与冻结架构的兼容性设计

## 3.1 总体落位（对齐"万能底座"口径）

```
用户/租户任务
   ↓
DeepSeek Harness（外层，仅 Adapter 桩，GA 前不启用）
   ↓
Hermes（内层编排 = 调度主权所在）
   ├─ 判定任务类型 → 选择链路（文章/视频/邮件/多平台）
   ↓
PublishPipeline Framework（本次新建，C 方案核心产物）
   阶段：GENERATED → CLEANSE(关卡1) → REVIEW(关卡2) → APPROVED
        → DISTRIBUTING → VERIFIED → DONE / FAILED→RETRY→人工
   ├─ ECC 注入：行业清洗规则/合规标准（建材 ECC 等，Skill 版本化）
   ├─ DeerFlow：深度生成/研究类步骤
   ├─ n8n：仅分发后的外部通知/联动
   ↓
Validator（多层验证：Schema→业务→事实→质量→人审）
   ↓
Evidence（步级证据）→ task_traces → Experience Engine（沉淀/进化）
   ↓
Metering（meter_events → Revenue OS）
```

**底座插件化**：四条链路本身注册为底座上的 Skill/Plugin——`content-publish-pipeline`、`video-publish-pipeline`、`email-sequence-pipeline`、`multi-channel-sync-pipeline`，全部进 `skills` 表版本化管理；行业差异（建材/机械/任意行业）通过 ECC 行业专家包注入清洗与复核规则，实现"同一底座、不同行业"。

## 3.2 三个关键裁决

### 裁决一：调度权归谁？
**归优丁 Control Plane（Hermes），GoodJob/任何外部系统只接单不派单。**
- `pipeline_runs` 由优丁任务面（`ai_tasks`）创建；
- GoodJob（若 B 方案引入）是 Execution Plane 的一个 Adapter，其内部调度（BullMQ）只服务于优丁下发的任务包，禁止自发起业务动作；
- DeerFlow 负责深步骤执行，n8n 只消费事件，均不得持有链路状态。

### 裁决二：租户隔离如何贯穿？
- 新表全部 `tenant_id NOT NULL` + Repository 层强制过滤；
- `pipeline_runs`、`step_evidence`、`review_tasks` 纳入 RLS 试点批次（现有 §4.6 三步走第 2 批）；
- 清洗/复核规则（ECC 行业包）按租户启用的行业包加载，跨租户规则不可见；
- 媒体/产物引用走 `tenants/{tid}/` 前缀对象存储（现有规范）。

### 裁决三：数据如何回传 Evidence / Metering？
- **步级**：每个 `pipeline_steps` 完成 → 写 `step_evidence`（输入摘要/输出引用/校验结果/耗时/成本）→ 同步 `task_traces`；
- **终态**：`pipeline_runs` 终态钩子 → `meter_events`（meter 按链路：`content_publish`/`video_publish`/`email_send`/`channel_sync`）→ Celery beat 汇总进 `token_ledger`/`wallet`（复用现有计费，零重建）；
- **经验**：成功/失败模式 → `ExperienceEntry`（kind=success/failure）→ Canary 门禁（进化只经 Draft→评估→灰度→人审）。

---

# 四、补强环节清单与补接方案（逐条）

| # | GoodJob 有 / 优丁缺 | 补接方案 | 落点 |
|---|---|---|---|
| 1 | **清洗关卡**（发布前强制） | 新建 `CleanseGate`：聚合现有 `brand_guard`（措辞清洗）+ `compliance_scanner`（合规）+ 敏感词/事实断言检查 + 查重；清洗结果结构化（问题清单+严重级），未过不得进复核 | `app/services/pipeline/gates/cleanse.py` |
| 2 | **复核关卡**（自动+人工双态） | 新建 `ReviewGate`：Validator Agent 打分（复用 `content_scorer`/`eeat_scorer`）→ ≥阈值自动过；低分或高风险（价格/承诺/医疗法规类）→ 人工复核队列；三态：通过/驳回/修改后重提 | `app/services/pipeline/gates/review.py` + admin 复核页 |
| 3 | **多级审批图** | 借鉴 GoodJob `approval-graph`：支持串行多级、委托、超时升级；升级现有 `paperclip/approval_gate` 为通用 `ApprovalGraphService` | `app/services/pipeline/approval_graph.py` |
| 4 | **Checkpoint 断点恢复** | `pipeline_steps` 记录步骤级检查点；任务恢复从最后成功步骤续跑，不重跑已完成步骤 | `pipeline_runs.checkpoint_json` |
| 5 | **单泳道并发锁（lease）** | 同一发布物同时只允许一个执行者持锁（`lease_owner`+`lease_expires`），杜绝双写双发 | 表字段 + 获取锁原语 |
| 6 | **统一幂等** | `idempotency_key` 全局唯一（租户+链路+业务键），重复投递直接返回既有结果 | `pipeline_runs.idempotency_key UNIQUE` |
| 7 | **有界失败重试** | 每步 `retry ≤3` 指数退避 → 超限转 `WAIT_HUMAN`（禁止无限重试，对齐冻结红线） | 状态机内置 |
| 8 | **步级台账 + 记账证据** | 每步写 `step_evidence`（含外部平台返回的 ID/URL/截图引用），发布类必须"外部状态核验"（如抓取已发布 URL 存证）才置 VERIFIED | `step_evidence` 表 + Validator |
| 9 | **失败运行记录可重放** | 失败步骤保留完整上下文（输入/规则版本/模型版本），支持一键重放 | 对接 `task_traces` |
| 10 | **规则版本化** | 清洗规则/复核阈值/行业合规包一律注册 `skills`/SOP 版本，变更走 Canary | 迁移 083 注册表 |

### 四条链路的接线方式

| 链路 | 接入点 | 关卡差异 |
|---|---|---|
| 文章 | `content_master_publish_service` 产文 → 进 pipeline | 清洗=查重+事实+品牌；复核=EEAT 分数阈值 |
| 视频 | `video_publish_orchestrator` 成片 → 进 pipeline | 清洗=字幕敏感词+封面合规；复核=高风险必人审；分发后核验平台视频 ID |
| 邮件 | `email_queue_service` 出队前 → 关卡前插 | 清洗=退订链接/合规（GDPR/CAN-SPAM）；复核=首封开发信必人审，序列内自动 |
| 多平台同步 | `publish_dispatch_service` 每渠道一步 | 每渠道独立证据；部分失败不回滚已成功渠道，失败渠道单独重试 |

---

# 五、数据模型（新增，纳入迁移 090-091）

```
pipeline_runs
  id, tenant_id, pipeline_type('article'|'video'|'email'|'multi_channel'),
  source_task_id FK→ai_tasks, subject_ref(内容物引用),
  status ENUM('generated','cleansing','cleansed','reviewing','approved',
              'distributing','verifying','done','failed','wait_human','retrying'),
  checkpoint_json, lease_owner, lease_expires, idempotency_key UNIQUE,
  skill_version(链路 Skill 版本), rule_pack_version(ECC 行业包版本),
  budget_used, created_at/updated_at

pipeline_steps
  id, run_id FK, seq, step_type, status, retry_count,
  input_ref, output_ref, started_at, finished_at, error

step_evidence
  id, step_id FK, tenant_id, claim, evidence_type('platform_id'|'url_check'|
  'screenshot'|'score'|'human_approval'), evidence_ref(对象存储), verified BOOL,
  validator_version, created_at

review_tasks
  id, tenant_id, run_id, step_id, reviewer_id NULL, decision('approved'|
  'rejected'|'revise'), comments, decided_at, sla_due_at   -- 审批图实例
```

关系：`tenants 1─N pipeline_runs 1─N pipeline_steps 1─N step_evidence`；`ai_tasks 1─N pipeline_runs`（一次任务可产生多链路运行）。

---

# 六、阶段计划与验收

| 阶段 | 内容 | 估时 | 验收标准 |
|---|---|---|---|
| S1 框架核心 | 状态机/表/关卡骨架/幂等/lease | 1.5 周 | 一条模拟文章走完 9 状态；重复投递幂等；断点恢复成功 |
| S2 双关卡落地 | CleanseGate+ReviewGate+审批图 | 1.5 周 | 低分内容 100% 拦截进人审；高风险词触发人审；复核三态留痕 |
| S3 四链路接线 | 文章/视频/邮件/多平台接入 | 1.5 周 | 每链路端到端：生成→清洗→复核→分发→证据→计量；发布证据可回放 |
| S4 闭环与灰度 | Metering/Experience 接线、行业规则包（建材首个）、admin 复核台 | 1 周 | 计量对账误差 0；经验条目产生；建材行业包生效且可版本回滚 |

合计 **约 5-6 周**（含联调），其中 S1-S2 完成即交付"两个质量关卡"这一核心诉求。

## 风险与规避
| 风险 | 规避 |
|---|---|
| 关卡拖慢发布吞吐 | 自动复核为主（阈值内秒级过），人审只兜高风险；队列并行 |
| 存量链路回归 | 特性开关 `PIPELINE_GATES_ENABLED` 按链路逐个灰度 |
| 复核规则过严误杀 | 驳回必须给原因+修改建议；阈值经 Canary 调优 |
| 模式提炼失真 | 以 GoodJob 对应模块单测用例为"行为规格"反向验收 |

## 红线复核
- ✅ Control Plane 调度主权：pipeline 全部由优丁创建与裁决
- ✅ Harness 仅 Adapter 桩：本框架不依赖任何外部 Runtime
- ✅ 租户隔离：新表全量 `tenant_id` + RLS 第二批试点
- ✅ Skill 版本化：链路/规则/阈值全部进注册表，变更走 Canary+人审
- ✅ Evidence 机制：发布类步骤必须外部核验留证
- ✅ 零 GoodJob 代码复制：只借鉴模式，代码全原创（许可证零牵连）
