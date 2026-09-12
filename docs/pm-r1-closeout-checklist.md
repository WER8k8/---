# Sprint-R1 关账清单

> **签发**：PM-07 · **目标日**：2026-06-16  
> **规则**：代码完成 ≠ 关账；须满足「交付物 + 验收证据」列

---

## 代码完成（可标 ✅）

| ID | 交付物 | 证据 |
|----|--------|------|
| ARCH-01 | preflight 0 fail | `docs/staging-preflight-auto-latest.json` |
| BJ-02 | useYoudingTable 734 | 三队列页 + 单测 |
| BJ-03 | CRUD Top12×3 | `views/_generated` + 路由 |
| BE-06 | 60 页导出 | `export-rz-60-pages.py` 绿 |
| PM-07 | 分配表+tracker | 本文 + `ecc-delivery-tracker.md` |
| DOC-02 | 索引 sync | 三文档一致 |

---

## 待关账（Owner / 签字依赖）

| ID | 剩什么 | 谁推动 | DDL |
|----|--------|--------|-----|
| ARCH-04 | 生产 HTTPS 真证书 | Owner O-1 | 6/14 |
| QA-04 | Locust 72h 正式域 | QA + ARCH | 6/16 |
| BJ-01 | SaaS 专家五问签字 | PM 约验收 | 6/12 |
| PAT-02 | 代理检索号回填 | IP | 6/18 |
| COMP-06 | 律师表 S2 | IP | 6/20 |

---

## 划入 Sprint-S2（不占 R1 研发带宽）

- 40 平台 PM 正式表（MOD-03）  
- 贸易情报矩阵签字（MOD-07）  
- 5+5 试点名单（MOD-08 部分）  
- 律师/专利人类签字链  

---

## ITER-03 并入关账（销售通知链）

| ID | 内容 | 状态 | 证据 |
|----|------|------|------|
| ITER-03a | 开户路线图 + 清单刷新 | ✅ 代码 | `onboarding_progress_service` + 向导 UI |
| ITER-03b | 抖音真实拉评对接 | ☐ | SAU/AiToEarn Worker |
| ITER-03c | Step5 截图验收 | ☐ | `qa-step5-inquiry-im-acceptance.md` |
| ITER-03d | 客户/代理手册 | ✅ 文档 | `guides/customer-wecom-push-5min.md` 等 |

---

## 周五门禁（每周）

```powershell
cd frontend/admin; npm run cert:gate
```

- QA-02：P0/P1/P2 = 0 方可宣称 R1 可送检

---

## PM 关账动作

1. 更新 `pm-dev-task-progress.json` 各 ID `pct` / `next`  
2. 更新 `module-progress.json` · `loop-inquiry` 10/10（MOD-02 实机后）  
3. 召开 30min：**R1 复盘** — 未关项进 S2 或 ITER-04  
4. SaaS 专家签字后 · `admin-overhaul` → 10/10  

---

*2026-06-04 初版*
