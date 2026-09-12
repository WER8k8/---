# PM 演示当天 Checklist（照着打勾即可）

> 依据：`docs/送检演示脚本.md` · 约 30 分钟 · 12 模块  
> 工程前置：**已绿** — preflight 0 fail、层级/数据中心 API 验收 PASS

---

## 出发前（5 分钟）

- [ ] 运行 `scripts/start-dev-admin.ps1`（或确认 :8001 / :5173 已开）
- [ ] 浏览器打开 `http://127.0.0.1:5173`，账号 `admin` / `admin123`
- [ ] 可选：`scripts/run-phase-c-next.ps1` 再跑一遍工程验收

---

## 演示中（按脚本顺序截 12 张图）

截图保存到 `docs/送检截图/`，命名 `01-login.png` … `12-trade-intel.png`

| # | 模块 | 路径提示 |
|---|------|----------|
| 1 | 登录 | `/login` |
| 2 | 数据中心 | `/admin/aggregation` |
| 3 | 层级管理 | `/admin/hierarchy` |
| 4 | 内容/SEO | 按演示脚本 |
| 5 | 销售/询盘 | 按演示脚本 |
| … | … | 见 `docs/送检演示脚本.md` |

---

## 演示后（签字）

- [ ] 12 张截图已放入 `docs/送检截图/`
- [ ] 在 `docs/pm-signoffs/l3-signoff.json` 填写 `pm_signed: true` 与日期
- [ ] 把 `docs/QA-浏览器回归-2026-05-31.md` 底部 PM 确认栏签字

---

## 演示部分（当前跳过）

- [ ] 12 张截图与 30 分钟彩排 — **演示阶段先跳过**
- [x] **G4 真实 AI Key** — 已内置；`scripts/run-g4-real-ai-verify.ps1` 实跑 PASS（见 `docs/g4-ai-key-verify-latest.json`）
- [ ] PM 签字 `l3-signoff.json`

---

## 仍须运维/商务（非 PM 一人能完成）

| 项 | 说明 |
|----|------|
| HTTPS 演示域 | 1 个独立 HTTPS 域名 |
| G4 真实 AI Key | 生产 `.env` + `MVP_LAUNCH=0` 实跑 |
| Locust **1000** 用户 | 需在 staging 服务器跑满指标（本地已做 50 用户 smoke） |
| 72h 长跑 | 生产/staging 环境持续监控（本地已做 5 分钟 smoke PASS） |

**你不需要懂技术**：研发侧 Phase C 工程项已自动化；你只要按本清单截图 + 签字即可推进送检。
