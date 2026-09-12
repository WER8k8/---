# PM-06 · Owner Blocked 书面说明（模板）

> **触发**：HTTPS 演示域无法按 Sprint-R1 截止提供  
> **回填**：Owner/PM 填写后保存为 `docs/compliance/pm-06-blocked-written-{YYYYMMDD}.md`，并在 `mod-08-owner-blockers.json` 将 `pm06-blocked-written` 设为 `done: true`

## 基本信息

| 字段 | 内容 |
|------|------|
| 日期 | YYYY-MM-DD |
| 申请人 | PM |
| 阻塞项 | HTTPS 演示域 / DNS / Certbot |
| 原计划完成日 | 2026-06-14 |
| 新目标完成日 | YYYY-MM-DD |

## 阻塞原因（Owner 确认）

1. 
2. 

## 影响范围

- [ ] ARCH-04 生产 Certbot 无法实跑
- [ ] QA-04 Locust 正式 72h 无法启动
- [ ] MOD-04 七步实机录屏（第 7 步 HTTPS）延期

## 研发侧已就绪（可并行）

- R1 dev gate 24 步全绿
- MOD-04 本地六路由彩排 PASS
- Locust dryrun / smoke 脚本就绪

## Owner 承诺

| 交付物 | 责任人 | 日期 |
|--------|--------|------|
| HTTPS 演示域 + DNS A 记录 | Owner | |
| CERTBOT_EMAIL | 运维 | |

## PM 签字

- 姓名：
- 日期：
