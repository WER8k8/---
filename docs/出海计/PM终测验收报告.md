# PM 终测验收报告（模板）

> **项目**：UJ 保温建材出海站 / 管理端  
> **环境**：本地 `http://127.0.0.1:8001` + 管理端 `http://127.0.0.1:5173`  
> **验收人**：________ · **日期**：________

## 模块勾选（20 项，与 `module-progress.json` 对齐）

| # | 模块 | L3 浏览器 | 备注 |
|---|------|-----------|------|
| 1 | 登录 / 鉴权 | ☐ | 创始人微信 `qq979072138` |
| 2 | 产品管理 | ☐ | |
| 3 | 询盘 unified | ☐ | 主入口 `/inquiries/unified` |
| 4 | 询盘导出 | ☐ | 非创始人 platform 应 403 |
| 5 | 发布台 / 队列 | ☐ | `run_demo_acceptance` 已绿 |
| 6 | 副驾 Copilot | ☐ | 飞轮柱、导出 CSV |
| 7 | 创始人诊断 | ☐ | `/admin/founder-diagnostics` |
| 8 | UBrain 飞轮 | ☐ | D2–D6 |
| 9 | AI 学习概览 | ☐ | 非空 `self_evolution_log` 或有 sources |
| 10 | 国际抓取 Webhook | ☐ | 需 `CRAWL_WEBHOOK_SECRET` |
| 11 | GEO / 技术雷达 | ☐ | Celery beat 或手动触发 |
| 12 | 财务导出 | ☐ | 创始人门禁 |
| 13 | 租户站 H5 询盘 | ☐ | 11 位手机号 |
| 14 | SEO 关键词 | ☐ | |
| 15 | 内容 / CMS | ☐ | |
| 16 | 支付（沙箱） | ☐ | |
| 17 | 物流轨迹 | ☐ | demo 模式可接受 |
| 18 | 飞书通知 | ☐ | 可选 |
| 19 | 国密诊断 API | ☐ | `founder_ops` |
| 20 | 生产预检 | ☐ | `run_production_preflight.py` |

## 自动化证据（研发填写）

| 命令 | 结果 | 日期 |
|------|------|------|
| `python scripts/run_demo_acceptance.py` | | |
| `python scripts/check_mounted_routes.py` | | |
| `pytest backend/tests/unit -q` | | |

## PM 签字

- [ ] 功能验收通过  
- [ ] 已知 P2 占位已记录（Accio gap / 技术雷达拉源）  
- [ ] 演示域 / HTTPS（若需要）另排期  

签字：________
