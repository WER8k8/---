# 附属协议与出处审计 · AUD-P0-1

> 日期：2026-09-19  
> 分支：`feat/annex-domain-merge`  
> 依据：主理人裁定 — GoodJob/TradeAI 完整能力融入优丁，去掉登录/超管/管理台；功能域菜单无特权；Hermes 驱动。

## 1. GoodJob CRM（`_external/goodjob-crm`）

| 项 | 结论 |
|----|------|
| 包声明 | `backend/package.json` → **Apache-2.0** |
| LICENSES 目录 | 含 Apache-2.0、MIT、GPL-3.0-only、LGPL-3.0-or-later（第三方依赖混合） |
| 融入方式 | 能力域 + 无头引擎；**非**原样分发第二套产品登录 |
| 剥身份 | login/platform/IAM 管理台生产 **410**（`P0-ANNEX-STRIP`） |
| 保留 | `/api/auth/annex-ticket`、`/api/uj-bridge/*`、业务 API |
| 风险 | 若未来把 **GPL/LGPL 依赖**静态链接进优丁主仓发行版，需法务评估隔离；当前 HTTP 桥/任务包模式降低 copyleft 触达主仓的风险 |
| 动作 | 发行前复核 Node 依赖树 license（npm ls / licensee）；GPL 模块保持进程边界 |

## 2. Trade AI Agent（`_external/trade-ai-agent`）

| 项 | 结论 |
|----|------|
| 出处 | README：Gitee `LBones-li/agent_trade_b`；优丁侧 `foreign_trade/osint` 注明改编自 chefroger/smart-trade-ai（MIT） |
| 归属 | 工作区文档：代码复制于 `_external/trade-ai-agent/`；商用合入前书面确认（总纲 §9.4-1 口径） |
| 技术栈 | Python FastAPI — 与 UJ 同栈，服务层可并入 |
| 剥身份 | `annex_identity.py`：login/register/admin → **410**；不默认种超管 |
| 保留 | skills/outreach/whatsapp/workflow 等能力 API + Hermes `trade_ai_agent` executor |
| 动作 | 保留 `THIRD_PARTY_ATTRIBUTION.md`；对外材料标注能力来源与 MIT 改编说明 |

## 3. 身份与特权红线（已实装）

- 唯一 `/login` = 优丁（LOGIN-LOCK-01）
- 菜单：**社媒拓客 / 外贸履约** 功能域，`privileged=false`
- 调度：Hermes L1 默认；DSH 非每单必经
- 真相：优丁 PG；无 Key 诚实 failed

## 4. 本审计范围

- **已做**：包声明/LICENSES 枚举、出处文件核对、剥身份代码门禁  
- **未做**：全量 npm/pip 依赖 license 扫描报告、Gitee 商用书面确认函归档  
- **门禁关联**：`scripts/verify_annex_identity_strip.py`、`annex_work_mode` S7
