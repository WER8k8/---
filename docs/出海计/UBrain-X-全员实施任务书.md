# UBrain-X 全员实施任务书

> 版本：2026-05-25  
> 下发角色：产品经理 / 架构指挥 / 前端 / 后端 / AI-DeerFlow / 营销运营 / 测试 / 运维  
> 项目代号：**UBrain-X 卖货副驾**  
> 产品范式：UBrain 业务大脑 + DeerFlow 长任务执行 + Accio Work 工作台形态  
> 北极星：**客户自有网站带来的有效电话 / 询盘数量**

---

## 一、任务判定

本任务属于 **跨模块产品级功能（S13 / M4 级别）**，但第一阶段只做 **P0 获客闭环**，禁止一次性铺满所有 Accio Work 能力。

### 总目标

把 UBrain-X 做成客户能看懂、能使用、能复盘的 **“建材卖货副驾”**：

```text
客户一句话
  → 副驾识别任务
  → 生成获客内容 / GEO 清单 / 发布计划 / 询盘分级 / 线索周报
  → 人工确认敏感动作
  → 电话与询盘写回系统
  → 每周复盘是否带来真实线索
```

### 非目标

- 不承诺“完全复刻阿里国际站私有数据能力”。
- 不做自动报税、自动砍价、自动成交。
- 不绕过平台规则做违规账号规避。
- 不在 P0 做全量 40 平台和全语种。

---

## 二、完成定义

P0 完成不是“功能页面出现”，而是满足以下验收：

| 编号 | 完成定义 | 验收方式 |
|------|----------|----------|
| D1 | `/client/copilot` 能调用 UBrain-X 5 个获客工具 | 手动演示 + API 返回 |
| D2 | 公开询盘手机号必填，来源可追踪 | 提交无手机号失败；有来源入库 |
| D3 | 周报卡片显示有效线索数、手机号数、来源分布 | 前端截图 + API 数据 |
| D4 | `matrix_publish`、回复草稿等敏感动作必须确认 | UI 有确认门 |
| D5 | 租户数据隔离不泄露 | 单测 / 接口测试 |
| D6 | 保温厂试点至少完成 1 次内容包生成并上线 | CMS 草稿或发布记录 |

---

## 三、全员分工

### 1. 产品组

负责人角色：产品经理 / insulation-material-product-manager

| 任务 ID | 任务 | 交付物 |
|---------|------|--------|
| PM-01 | 定义 `/client/copilot` 页面信息架构 | 页面原型说明 |
| PM-02 | 定义任务卡状态：待确认 / 执行中 / 成功 / 失败 | 状态流转表 |
| PM-03 | 定义对外可说与不可说话术 | 销售话术表 |
| PM-04 | 定义 30 天保温厂试点验收表 | 线索复盘模板 |
| PM-05 | 维护本任务书，阻止范围膨胀 | 每周更新 |

产品口径：**先拿电话，再扩能力。**

---

### 2. 架构 / 后端组

负责人角色：architecture-commander / insulation-backend-architect / insulation-backend-developer

| 任务 ID | 任务 | 路径建议 | 优先级 |
|---------|------|----------|--------|
| BE-01 | 稳定 UBrain-X 工具注册表，暴露工具元数据 | `backend/app/services/ubrain/` | P0 |
| BE-02 | 公开询盘手机号必填，拒绝空手机号 | `backend/app/api/v1/routes/inquiries.py` | P0 |
| BE-03 | `source_channel` 全链路入库、序列化、筛选 | `InquiriesUnifiedService` | P0 |
| BE-04 | 新增线索周报接口或复用 UBrain weekly report | `/api/v1/ubrain/chat` 或 `/api/v1/inquiries/report` | P0 |
| BE-05 | 生成 CMS 草稿：`lead_content_pack` → draft | `content_master` / CMS service | P1 |
| BE-06 | DeerFlow job 表：任务、状态、日志、结果 | `deerflow_jobs` | P1 |
| BE-07 | 敏感动作审计：谁确认、何时执行、结果 | `ubrain_action_audit` | P1 |

后端质量门：

- 所有列表与周报必须按 `tenant_id` 过滤。
- 手机号、来源、状态字段必须能导出。
- 异步任务必须有失败原因与重试入口。

---

### 3. 前端组

负责人角色：frontend-architect / fullstack-developer

| 任务 ID | 任务 | 路径建议 | 优先级 |
|---------|------|----------|--------|
| FE-01 | 新增 `/client/copilot` 卖货副驾页面 | `frontend/admin/src/views/client/copilot.vue` | P0 |
| FE-02 | 路由与菜单入口：客户工作台可见 | `frontend/admin/src/router/index.ts` | P0 |
| FE-03 | 对话输入 + 推荐指令 | Copilot 页面 | P0 |
| FE-04 | 任务卡片：内容包、GEO 清单、矩阵发布、询盘分级、周报 | Copilot 页面 | P0 |
| FE-05 | 确认弹窗：发布/回复/对外动作必须确认 | 通用组件或页面内 | P0 |
| FE-06 | 周报卡片：有效线索、手机号数、来源分布 | Copilot 页面 | P0 |
| FE-07 | 后续支持任务轮询与 DeerFlow job 状态 | Copilot 页面 | P1 |

前端体验原则：

- 客户只看 **“今天能做什么”**，不要展示复杂智能体术语。
- 按钮文案必须落到卖货：生成获客内容、检查 GEO、分析询盘、看本周线索。
- 失败时给可操作建议，不给技术栈错误。

---

### 4. AI / DeerFlow 组

负责人角色：AI Engineer / Backend Architect / DevOps

| 任务 ID | 任务 | 优先级 |
|---------|------|--------|
| AI-01 | 定义 DeerFlow Skill 包：建材内容、GEO 清单、周报 | P0/P1 |
| AI-02 | Phase 0 本地执行：先不接生产队列，产出可复制草稿 | P0 |
| AI-03 | Phase 1 接 `deerflow_jobs` 异步队列 | P1 |
| AI-04 | Docker 沙箱、文件目录、日志、安全限制 | P1 |
| AI-05 | 长任务状态回写：queued/running/success/failed | P1 |
| AI-06 | Token 成本上限和租户配额 | P1 |

AI 质量门：

- 不自动外发。
- 不跨租户读取上下文。
- 输出必须标注“草稿 / 需人审”。
- 每次长任务保留日志，便于复盘。

---

### 5. 营销运营组

负责人角色：ai-marketing-website-expert / 运营

| 任务 ID | 任务 | 交付物 |
|---------|------|--------|
| MK-01 | 保温厂首批 30 个长尾问题 | 选题表 |
| MK-02 | 3 平台试点清单：抖音 / 视频号 / 百家号等 | 发布 SOP |
| MK-03 | 6980 GEO 对照执行清单 | 勾选表 |
| MK-04 | 对外谦逊话术 | 销售一页纸 |
| MK-05 | 30 天试点复盘文案 | 周报模板 |

营销底线：

- 没有电话数据前，不说“效果超过 GEO”。
- 对外只说“试点中，每周复盘”。
- 所有案例必须脱敏、真实、有来源。

---

### 6. 测试 / 质量组

负责人角色：insulation-backend-testing-expert / code-reviewer / security-reviewer

| 任务 ID | 任务 | 验收 |
|---------|------|------|
| QA-01 | UBrain-X 工具单测 | 覆盖高/中/低意向、GEO 清单、发布确认 |
| QA-02 | 公开询盘手机号必填测试 | 空手机号失败 |
| QA-03 | 租户隔离测试 | A 租户看不到 B 租户周报 |
| QA-04 | Copilot 页面冒烟测试 | 5 个任务能返回 |
| QA-05 | 安全审查 | 敏感动作确认、无越权、无密钥泄露 |

验收命令基线：

```powershell
$env:JWT_SECRET_KEY='test-jwt-secret-key-for-ubrain-phase0-1234567890'
python -m pytest backend/tests/unit/test_ubrain_trade_intel.py
```

后续新增接口后补充 API 测试。

---

### 7. 运维 / 发布组

负责人角色：insulation-devops-engineer

| 任务 ID | 任务 | 优先级 |
|---------|------|--------|
| OPS-01 | 保温厂 HTTPS 演示域 | P0 |
| OPS-02 | 环境变量与测试密钥规范 | P0 |
| OPS-03 | 发布 Worker cron 或人工替代说明 | P0 |
| OPS-04 | DeerFlow 沙箱部署方案 | P1 |
| OPS-05 | 日志与备份 | P1 |

---

## 四、依赖图

```text
BE-02 手机必填
  └─ FE 询盘表单提示

BE-01 UBrain 工具元数据
  └─ FE-01 /client/copilot

BE-04 周报数据
  └─ FE-06 周报卡片

AI-01 Skill 定义
  └─ BE-06 DeerFlow job
      └─ FE-07 job 状态轮询

OPS-01 HTTPS 域
  └─ MK-02 试点发布导流
      └─ D2 / D6 电话验收
```

可并行：

- FE-01 页面壳、BE-02 手机号、MK-01 选题、OPS-01 域名、QA-01 单测。

必须串行：

- DeerFlow job 表 → 后端队列 → 前端轮询。
- 手机号必填接口 → 前端表单联调。
- 周报接口 → 周报卡片。

---

## 五、两周冲刺计划

### Day 1～2

- FE-01 / FE-02 页面入口
- BE-02 手机号必填
- MK-01 保温长尾选题
- OPS-01 HTTPS 域推进

### Day 3～5

- FE-03 / FE-04 任务卡接 `/api/v1/ubrain/chat`
- BE-04 周报数据完善
- QA-01 / QA-02 单测
- MK-02 三平台 SOP

### Day 6～8

- FE-05 确认门
- FE-06 周报卡片
- BE-05 CMS 草稿写入设计或第一版
- AI-01 DeerFlow Skill 定义

### Day 9～10

- 联调彩排：生成保温内容包 → 人审 → 发布导流 → 询盘入库 → 周报
- 修复阻塞
- 输出《第 1 周线索复盘》

---

## 六、第一版页面设计

页面：`/client/copilot`

### 区块 1：今日目标

- 今日要做：生成保温获客内容 / 检查 GEO / 分析询盘 / 看线索周报
- 北极星显示：本周有效手机号数量

### 区块 2：对话输入

推荐指令：

- “今晚生成 10 篇保温长尾 FAQ”
- “按 GEO 清单检查我的独立域”
- “这条询盘意向高不高”
- “把这篇发到抖音、视频号、百家号”
- “生成本周线索复盘”

### 区块 3：任务卡片

字段：

- 类型
- 状态
- 结果摘要
- 需要确认？
- 下一步按钮

### 区块 4：线索周报

- 总线索
- 带手机号线索
- 来源分布
- 待跟进数量

---

## 七、质量硬要求

1. **电话数量导向**：P0 每个任务必须能解释如何帮助电话/询盘。
2. **代码质量导向**：无租户隔离、无确认门、无测试，不准合并。
3. **身体与现金流友好**：P0 不做全量国际站，不做全平台自动化。
4. **对外谦逊**：没有数据前只说试点，不说超越。
5. **文档与代码同步**：每个完成项回写本任务书状态。

---

## 八、当前状态

已完成：

- UBrain Phase 0 后端：`lead_content_pack`、`geo_submit_pack`、`matrix_publish`、`inquiry_score`、`weekly_lead_report`
- 线索数据修复：`source_channel` 序列化、手机号不再污染、周报租户隔离
- 单测：`10 passed`

下一步最高优先级：

1. `/client/copilot` 页面
2. 手机号必填
3. 周报卡片
4. 保温内容包写入 CMS 草稿
5. DeerFlow job 表
