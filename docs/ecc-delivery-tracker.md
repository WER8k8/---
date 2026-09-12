# ECC 交付看板 · Sprint-R1 执行

> **进度条（未完成开发任务）**：[`pm-dev-progress-bars.md`](./pm-dev-progress-bars.md)  
> **分配表**：[`pm-task-allocation-20260602.md`](./pm-task-allocation-20260602.md) · **COMM-1（当前）**：[`pm-task-allocation-20260613.md`](./pm-task-allocation-20260613.md) · [`pm-dispatch-latest.json`](./pm-dispatch-latest.json)  
> **蜂群宪章（永久）**：[`pm-swarm-parallel-charter.md`](./pm-swarm-parallel-charter.md)  
> **商用作战图**：[`商用上线-跨部门作战图-2026-06-13.md`](./商用上线-跨部门作战图-2026-06-13.md)  
> **更新**：2026-06-13

---

## Sprint-COMM-1 · 鉴定面商用 W1（当前）

> **PM-07 已签发** · standup 只报任务 ID

| Lane | 本周 ID | 状态 |
|------|---------|------|
| H | COMM-PM-01~03 | PM-01 ✅ |
| PD | COMM-PD-01~03 | 产品并行 |
| A | COMM-ARCH-01~02 | 并行 |
| F | COMM-QA-01~03 | **QA-01 P0 红** |
| E | COMM-BE-01~03 | **三条 FAIL P0** |
| B | COMM-FE-01~02 | FE-01 近完成 |
| SRE | COMM-SRE-01 | **P0 红** |
| GR | COMM-GR-01 | 待修 |
| APP | COMM-APP-01 | 并行 |

站会调度：[`docs/ops/pm-standup-dispatch-latest.md`](./ops/pm-standup-dispatch-latest.md)

---

## 蜂群泳道 · 并行状态（Sprint-R1 · 已收口）

> **永久标准**：代码质量高 · 思路清晰 · 逻辑严谨 · 边界清  
> standup 按 **Lane** 报进度，8 泳道默认 **同时开工**

| Lane | 主责 | ID | 状态 | 边界 Out |
|------|------|-----|------|----------|
| **A** | 架构 | ARCH-01, ARCH-04 | ✅ ARCH-01 · 🔄 ARCH-04 | 不改 Vue 业务页 |
| **B** | 前端 | BJ-01 | ✅ 95% | 不扩全局路由 |
| **C/D** | 页面搭建 | BJ-02, BJ-03 | ✅ 100% | 不碰 Formily / 不新建 API |
| **E** | 后端 | BE-06 | 🔄 并行 | 不改 Admin UI |
| **F** | QA | QA-04, QA-02 | 🔄 并行 | 不修功能 |
| **G** | IP/专利 | PAT-02, COMP-06 | 🔄 并行 | 不写代码 |
| **H** | PM/文档 | PM-07, DOC-02 | 🔄 并行 | 不代写实现 |
| **I** | 后端+前端 | **MOD-09** | 🔄 开工 | 四层贯通；不新建支付 API |

> MOD-09 依据：[`pm-hierarchy-l1-l4-bridge-summary-20260602.md`](./pm-hierarchy-l1-l4-bridge-summary-20260602.md)

---

## 出海增长 GW 泳道（Sprint-GW · 与 R1 并行）

> **全文**：[`global-overseas-growth-agent-backlog.md`](./global-overseas-growth-agent-backlog.md) · **登记册**：[`global-overseas-growth-task-register.json`](./global-overseas-growth-task-register.json)  
> **前提**：出海 B2B 比国内推广更难、细节更多；先 P0 再社媒爆款。

| Lane | 范围 | P0 代表 | 状态 |
|------|------|---------|------|
| **GW-L** | 开发信/Outbound | OB-01~07 质量分+时区 | 🔄 代码已落地，前台待接 |
| **GW-P** | 归因/投放 | TR-01 UTM 全链路 | ⏳ |
| **GW-G** | 内容/SEO/AEO | CC-02 一源多态、AEO-01 事实审计 | ⏳ |
| **GW-S** | 社媒/视频 | TT/YT/LI Playbook | ⏳ P1 |
| **GW-PM** | 专家角色库 | b2b_trade_experts.json | ✅ JSON 已入库 |
| **GW-R** | 研究员 | GW-R-AGENT-01/02 持续迭代闭环 | ✅ Brief+ECC+Inbox；UI 批准待 S2 |

---

## 全量数字

| 层级 | 条数 | ✅ | 进行中 |
|------|------|-----|--------|
| L1 PM ID | 79 | 54 | 25 |
| L3 百家 BJ | 3 | 0 | 3 |
| L4 业务 MOD | 8 | 0 | 8 |
| L5 人类 H | 17 | — | S2 批次 |
| **研发 Sprint-R1** | **13 项** | 1 | **12** |

---

<!-- DEV-PROGRESS-BARS:START -->
## 开发进度条（横向 · 未完成）


<style>
.yd-progress-wrap { font-family: ui-sans-serif, system-ui, sans-serif; font-size: 13px; max-width: 100%; }
.yd-progress-row {
  display: flex; align-items: center; gap: 10px;
  margin: 8px 0; width: 100%; flex-wrap: nowrap;
}
.yd-progress-row .id { flex: 0 0 72px; font-weight: 600; color: #0f172a; }
.yd-progress-row .name { flex: 0 0 160px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.yd-progress-row .track {
  flex: 1 1 auto; min-width: 80px; height: 12px;
  background: #e2e8f0; border-radius: 6px; overflow: hidden;
}
.yd-progress-row .fill {
  height: 100%; border-radius: 6px;
  background: linear-gradient(90deg, #2563eb, #60a5fa);
}
.yd-progress-row .pct { flex: 0 0 44px; text-align: right; font-weight: 700; color: #1e40af; }
.yd-progress-row .owner { flex: 0 0 52px; font-size: 12px; color: #94a3b8; text-align: right; }
.yd-progress-summary {
  display: flex; align-items: center; gap: 10px; margin: 12px 0 4px;
  padding-top: 8px; border-top: 1px dashed #cbd5e1;
}
.yd-progress-summary .label { flex: 0 0 232px; font-weight: 600; color: #475569; }
.yd-progress-summary .track { flex: 1; height: 14px; background: #e2e8f0; border-radius: 7px; overflow: hidden; }
.yd-progress-summary .fill { height: 100%; background: linear-gradient(90deg, #059669, #34d399); border-radius: 7px; }
.yd-progress-summary .pct { flex: 0 0 44px; text-align: right; font-weight: 700; }
</style>

<div class="yd-progress-wrap">
<div class="yd-progress-row"><span class="id">ARCH-04</span><span class="name">HTTPS + compose 实跑</span><div class="track"><div class="fill" style="width:99%"></div></div><span class="pct">99%</span><span class="owner">架构</span></div>
<div class="yd-progress-row"><span class="id">QA-04</span><span class="name">Locust 冒烟→72h</span><div class="track"><div class="fill" style="width:96%"></div></div><span class="pct">96%</span><span class="owner">QA</span></div>
<div class="yd-progress-row"><span class="id">BJ-01</span><span class="name">Formily site-editor</span><div class="track"><div class="fill" style="width:99%"></div></div><span class="pct">99%</span><span class="owner">前端</span></div>
<div class="yd-progress-row"><span class="id">PAT-02</span><span class="name">新颖性检索 memo</span><div class="track"><div class="fill" style="width:92%"></div></div><span class="pct">92%</span><span class="owner">IP/专利</span></div>
<div class="yd-progress-row"><span class="id">COMP-06</span><span class="name">律师复审表</span><div class="track"><div class="fill" style="width:93%"></div></div><span class="pct">93%</span><span class="owner">IP</span></div>
<div class="yd-progress-summary"><span class="label">Sprint-R1 平均</span><div class="track"><div class="fill" style="width:95%"></div></div><span class="pct">95%</span></div>
</div>

<details><summary>纯文本横向</summary>

```text
ARCH-04    HTTPS + compose 实跑     ████████████████████████████████████████████████   99%  架构
QA-04      Locust 冒烟→72h          ██████████████████████████████████████████████░░   96%  QA
BJ-01      Formily site-editor    ████████████████████████████████████████████████   99%  前端
PAT-02     新颖性检索 memo             ████████████████████████████████████████████░░░░   92%  IP/专利
COMP-06    律师复审表                  █████████████████████████████████████████████░░░   93%  IP
—平均—                              ██████████████████████████████████████████████░░   95%
```
</details>

完整：[`pm-dev-progress-bars.md`](./pm-dev-progress-bars.md)
<!-- DEV-PROGRESS-BARS:END -->

## Sprint-R1 · 本周分配（6/3–6/16）

| 主责 | ID | 交付 | DDL |
|------|-----|------|-----|
| **架构** | ARCH-01 | preflight 0 fail | 6/10 |
| **架构** | ARCH-04 | HTTPS compose 记录 | 6/14 |
| **QA** | QA-04 | Locust 冒烟→72h | 6/16 |
| **QA** | QA-02 | 周五 cert:gate | 每周五 |
| **前端** | BJ-01 | Formily site-editor | 6/12 |
| **页面搭建** | BJ-02 | Art table 734 | 6/14 |
| **页面搭建** | BJ-03 | CRUD Top12×3 | 6/14 |
| **后端** | BE-06 | 60 页导出终验 | 6/8 |
| **IP/专利** | PAT-02 | 检索 memo | 6/18 |
| **IP** | COMP-06 | 律师表草稿 | 6/20 |
| **PM** | PM-07 | 统计+分配 | 每周一 |
| **文档** | DOC-02 | 文档 sync | 每周一 |

**SaaS 专家**：BJ-01 验收 · 五问抽检  
**视觉/营销**：R1 无编码 · S2 再动

---

## 认领状态（6/3 10:00 前确认 · 按 Lane 并行）

| Lane | 主责 | 认领 |
|------|------|------|
| A | 架构 | ☑ ARCH-01 ☑ ARCH-04(staging) |
| B | 前端 | ☑ BJ-01 |
| C/D | 页面搭建 | ☑ BJ-02 ☑ BJ-03 |
| E | 后端 | ☑ BE-06 |
| F | QA | ☑ QA-04冒烟 ☐ 72h |
| G | IP/专利 | ☑ PAT-02 ☑ COMP-06草稿 |
| H | PM/文档 | ☑ PM-07 ☑ DOC-02 |

---

## 一键

```powershell
cd frontend/admin; npm run cert:gate
powershell -File scripts\run-arch-01-cert-gate.ps1
backend\.venv\Scripts\python.exe scripts\validate-patent-copyright-scope.py
```

---

## 置后 Sprint-S2（7/1 起）

17 项人类/签字 — 见分配表 § Sprint-S2 · **不占本周 standup**

---

## 产品迭代 · ITER-01（2026-06-02）

| 节点 | 交付 | 状态 |
|------|------|------|
| **ITER-01a** | M1 海关 JSON + Comtrade 定时刷新 + 旺财 Trade Q&A | ✅ 代码已落地 |
| **ITER-01b** | Client `/client/dashboard` + App `/app/v1/home` 接入蓝海 Top1「今日一件事」 | ✅ 本迭代 |
| **ITER-01c** | Onboarding 串联：注册 → Hermes 建站 → 旺财预览 → 发布 | ✅ 本迭代 |

**ITER-01c 联调清单（建站/旺财易漏）**

| # | 检查 | 通过标准 |
|---|------|----------|
| 1 | 注册后跳转 | `/client/onboarding?product=…` |
| 2 | Hermes 保存 | `onboarding.site_built=true`，可进 Step 旺财 |
| 3 | Nuxt 公网站 | `:3000/tenant?__tenant={domain}` 可见 TenantSiteCompanion |
| 4 | 旺财同源 | 向导内 `/onboarding-chain/wangcai-preview` 与公开 `/public/tenants/{domain}/wangcai/ask` 同 `ask_wangcai()` |
| 5 | 首篇草稿 | `onboarding.first_publish_draft` 写入 → 多平台分发可继续 |
| **ITER-01d** | 文档 sync（M1/旺财/Comtrade 写入未完成表） | 🔄 本迭代 |
| **ITER-02** | **一键开业 TTV**：`POST /onboarding-autopilot/run` + 注册 autostart + 发布页预填 | ✅ 本迭代 |

---

## 产品迭代 · ITER-03（2026-06-04）

> 全文：[`iter-03-onboarding-sales-channel.md`](./iter-03-onboarding-sales-channel.md)

| ID | 交付 | 状态 | 证据 |
|----|------|------|------|
| **ITER-03a** | 开户五段路线图 + 清单动态刷新 | ✅ | 向导/工作台 + `onboarding_roadmap` API |
| **ITER-03b** | 抖音真实拉评 Worker | 🔄 85% | `POST /client/douyin-comments/pull` · Inbox · AiToEarn · 代码完整+单测全绿 |
| **ITER-03c** | 七步⑤ 5a/5b/5c QA 彩排 | 🔄 70% | `validate-qa-step5-staging.py` · 路由验证PASS · 单测全绿 · 待 staging 截图 |
| **ITER-03d** | 客户/代理手册 | ✅ | [`guides/customer-wecom-push-5min.md`](./guides/customer-wecom-push-5min.md) · [`guides/agent-onboarding-roadmap-onepage.md`](./guides/agent-onboarding-roadmap-onepage.md) |

**PM 关账附件**：[`pm-r1-closeout-checklist.md`](./pm-r1-closeout-checklist.md) · [`pm-owner-blockers-20260604.md`](./pm-owner-blockers-20260604.md)

---

## PM × 营销 · 全环节联合审查（2026-06-04）

> **任务 ID**：PM-MKT-01 · **不占研发 Lane**

| 交付 | 路径 |
|------|------|
| 审查宪章（2 场×90′） | [`pm-marketing-full-journey-review-charter.md`](./pm-marketing-full-journey-review-charter.md) |
| 全环节矩阵（A～H） | [`pm-marketing-journey-review-matrix.md`](./pm-marketing-journey-review-matrix.md) |
| 签字与缺口 | [`pm-marketing-journey-review-signoff.json`](./pm-marketing-journey-review-signoff.json) |
| 路由清单 | `python scripts/export-admin-route-inventory.py` |

**状态**：🔄 材料就绪，待 PM+营销开会填 signoff

**七步⑤ 子验收（不新增主步）**

| 子步 | 名称 | QA 截图 |
|------|------|---------|
| 5a | 客户能联系到你 | `mod-04-rehearsal/step5/5a-*.png` |
| 5b | 销售收得到通知 | `5b-*.png` |
| 5c | 抖音评论自动抓 | `5c-*.png` |

---

*PM-07 · 按分配表执行*
