# 开发进度与 BUG 汇总（出海计 · 同步版）

> **同步时间**：2026-05-25  
> **仓库**：`website CodeBuddy`  
> **权威细表**：[开发进度统计-未完成清单.md](./开发进度统计-未完成清单.md)  
> **产品权重**：`docs/module-progress.json`（约 **156/200，78%**）

---

## 一、一句话状态

| 维度 | 状态 |
|------|------|
| **后端单元测试** | **`tests/unit` 299/299 passed**（2026-05-28，约 3m12s） |
| **飞轮 P0 代码** | D2–D7 单测 ✅；**D1 + D2–D6 生产/UI 实机** 仍待人工 |
| **Accio 20 技能** | 14 全实现 + 2 部分 + 4 gap（501 占位）≈ **75%** |
| **演讲/录屏** | **刻意后置**（见未完成清单 §八） |

```text
本轮 BUG 战役：统一 API 契约 { code, data, message } + 测试基建 + 产品/认证/AI 引擎真修复
下一刀：生产迁移 D1 → e2e 飞轮脚本 → H5 询盘真机 → 副驾 UI 实点
```

---

## 二、BUG 修复清单（已关闭）

### 2.1 测试基建（Q1–Q2 契约漂移）

| 项 | 路径 | 说明 |
|----|------|------|
| T-API-01 | `backend/tests/api_helpers.py` | `api_code` / `api_data` / `assert_api_code` / `login_json` / `extract_access_token` |
| T-API-02 | `backend/tests/conftest.py` | 双路径 `get_db` override；测试跳过重中间件；`authenticated_client` + `get_current_user` override |
| T-API-03 | `backend/tests/unit/test_auth.py` | **13 passed** — `username_or_email`、业务 `code` 断言 |
| T-API-04 | `backend/tests/unit/test_products.py` | **30 passed** — 统一响应 + `category_id` fixture |
| T-API-05 | `backend/tests/unit/test_sprint_r_p0_p1.py` | IM / 公开询盘改用 `api_helpers` |
| T-API-06 | `backend/tests/unit/test_p1_remaining_batch.py` | 移动端 IM / referral 改用 `api_helpers` |

### 2.2 后端真 BUG（非仅改测试）

| ID | 模块 | 问题 | 修复 |
|----|------|------|------|
| B-PROD-01 | `products.py` | `current_user is None` 访问 `.role` → 500 | `_guard_product_user()` |
| B-PROD-02 | `products.py` | 单测路径 `/by-slug/...` 与路由不一致 | 路由 `GET /slug/{slug}`；单测对齐 |
| B-PROD-03 | `products.py` | 缺少浏览量接口 | `POST /{product_id}/increment-view` |
| B-AI-01 | `ai_engine.py` | `generate_code` / `analyze_seo` 多传 `None` → mock 解包失败 | 去掉多余 `None` 参数 |
| B-AI-02 | `test_ai_engine.py` | optimize 重试用例参数不足；`_create_llm` 与真实 env 初始化冲突 | 补全三元组；mock settings |

### 2.3 前端（部分）

| ID | 模块 | 说明 | 状态 |
|----|------|------|------|
| B-UI-01 | `frontend/admin/.../copilot.vue` | `parseApiBody` 用于 jobs/chat/flywheel/pipelines | ✅ 部分 |
| B-UI-02 | 同上 | ops-snapshot / action-audit / gaps / brief / feedback | ✅ 已统一 `parseApiBody`（gap 详情单次读 body） |
| B-MIG-01 | `029_add_ai_template_table.py` | 文件头垃圾行导致 IndentationError | ✅ 已删 |
| B-MIG-02 | `032_add_ssl_certificates_table.py` | `down_revision` 与 031 revision id 不一致 | ✅ 已改为 `031_add_publish_task` |

---

## 三、验收命令（可复制）

```powershell
cd backend
python -m pytest tests/unit -q
# 期望：237 passed

# 主链快验（约 1 分钟内，不含全量加载）
python -m pytest tests/unit/test_auth.py tests/unit/test_products.py tests/unit/test_flywheel_d2_d6_api.py -q

# 路由挂载（仓库根目录）
python scripts/check_mounted_routes.py
```

**最近全量结果**：`237 passed, 86 warnings in 219.64s`（2026-05-25）

---

## 四、仍开放问题（非单测 · 按优先级）

### P0 · 阻塞上线验真

| ID | 类别 | 说明 | 负责动作 |
|----|------|------|----------|
| O-D1 | 运维 | 生产库 Alembic `025`–`028` `upgrade head` | `scripts/run-flywheel-migrations.ps1` / `check-flywheel-migration.ps1` |
| O-D2–D6 | 飞轮 | 副驾 UI 实点：状态柱、简报、跑飞轮、pipeline、反馈同步 | 租户登录 + `e2e-flywheel-validation.ps1`（`SMOKE_TOKEN`） |
| O-T1 | 验真 | HTTPS 演示独立域 | DNS + 真证书 |
| O-T2 | 验真 | 询盘手机号 H5 真机点一次 | `StickyImBar` 已校验 API |

### P1 · 架构/质量债（不挡 237 单测）

| ID | 说明 |
|----|------|
| Q5 | 询盘三入口并存：`/inquiries`、`/inquiries-v2`、unified — 需产品裁定主入口 |
| Q4 | 部分路由 HTTP 200 + `body.code`；裸 `fetch` 须 `parseApiBody`（副驾未全覆盖） |
| INT | `tests/` 下 integration/e2e 可能仍用旧 `access_token` 顶层字段 — **未纳入本轮 237** |
| PM | `module-progress.json` → `pm_blockers`（演示域、40 平台表、套餐金额等 7 项） |

### P2 · 刻意后置

| 项 | 说明 |
|----|------|
| 演讲/录屏/30 分钟彩排 | 见 [开发进度统计-未完成清单.md](./开发进度统计-未完成清单.md) §八 |
| Accio 4 gap | image_sourcing、auto_shopify、paid_ads_creative、supplier_rfq（501 占位保留） |
| GraphRAG 实装 | 仅占位文档 + `integrations.graphrag` 状态位 |

---

## 五、开发进度快照（与飞轮并行）

### 5.1 商业飞轮 OS（D/T）

| ID | 代码/单测 | 环境/人工 |
|----|-----------|-----------|
| D1 | ✅ 迁移文件在仓 | ⬜ 生产执行 |
| D2–D6 | ✅ 服务层 + 单测 | ⬜ UI 实机未签字 |
| D7 | ✅ **237 unit passed** | ⬜ `e2e-flywheel-validation.ps1` |
| T2–T5 | ✅ 代码/文档 | T2 ⬜ H5 真机；T1 ⬜ HTTPS |
| T6 | ✅ 接最新询盘上下文 | ⬜ LLM 生成正文 |

### 5.2 Accio / Phase A

- **20 技能覆盖率**：75%（14 + 2×0.5）
- **Phase A1–A5**：代码层 ✅；副驾与生产验真见 D2–D6

### 5.3 夜间队列

`night-autodev-queue.yaml`：**N1–N5 全部 done**

---

## 六、变更与同步记录

| 时间 | 动作 |
|------|------|
| 2026-05-25 | 全量 `tests/unit` **237 passed**；写入本文件 |
| 2026-05-25 | 更新 [开发进度统计-未完成清单.md](./开发进度统计-未完成清单.md) D7 / 变更记录 |
| 2026-05-25 | 可执行 `scripts/sync-to-chuhaiji-kb.ps1` → 桌面「出海计」知识库 |

**维护约定**：每轮 BUG 或 D/T 验收后，先改「未完成清单」再刷新**本文件**一节「仍开放问题」，并跑 `sync-to-chuhaiji-kb.ps1`。

---

## 七、相关文档索引

| 文档 | 用途 |
|------|------|
| [商业飞轮OS-开发总文档.md](./商业飞轮OS-开发总文档.md) | 飞轮 API / 迁移 / 副驾路径 |
| [接下来怎么做-产品营销技术联合行动.md](./接下来怎么做-产品营销技术联合行动.md) | T1–T6 验真分工 |
| [DeerFlow-Accio-本系统-验真话术与30天指标.md](./DeerFlow-Accio-本系统-验真话术与30天指标.md) | 对外话术（后置彩排） |
| `docs/未完成开发任务表.md` | 全仓任务表（与 module-progress 联动） |
| `docs/多IDE开发进度与配置索引.md` | 灵码 / Trae / Cursor 镜像 |
