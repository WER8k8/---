# R1 → Owner 交接包（研发侧已就绪）

> **门禁**：`powershell -File scripts/run-r1-dev-gate.ps1`  
> **Blocker 跟踪**：`docs/compliance/mod-08-owner-blockers.json`

## Owner 需提供（按优先级）

| # | 项 | 解锁 |
|---|-----|------|
| 1 | HTTPS 演示域 + DNS | ARCH-04 Certbot · QA-04 72h · MOD-04 录屏 |
| 2 | `CERTBOT_EMAIL` | Let's Encrypt |
| 3 | SaaS 专家签字 | `docs/bj-01-saas-signoff-record.json` |
| 4 | 专利代理检索号 | `docs/专利/PAT-02-report-number.json` |
| 5 | MOD-02 生产密钥 | `deploy/production/env.template` 中 IM 段 |

## Owner 就绪后一键命令

```powershell
# Certbot 彩排（需 PILOT_TENANT_ID / DEMO_HTTPS_DOMAIN / AUTH_TOKEN）
powershell -File scripts\pilot-acme-ssl-issue.ps1

# Locust 正式 72h
$env:LOCUST_HOST = "https://你的演示域"
powershell -File scripts\qa-locust-72h-production.ps1

# 本地录屏彩排（无需 HTTPS）
powershell -File scripts\run-mod-04-recording-rehearsal.ps1

# Android AAB（需 JDK + Android SDK）
powershell -File scripts\run-mod-06-aab-build.ps1

# 专利检索号回填（代理返回后）
python scripts\apply-pat-02-report-number.py --number CN2026XXXX --agency "代理机构名"

# PM-06 域延期书面（模板）
# docs/compliance/pm-06-blocked-written-template.md

# MOD-04 第 7 步 HTTPS（域就绪后）
$env:MOD04_HTTPS_DOMAIN = "你的演示域"
python scripts\validate-mod-04-https-step.py

# Owner 域就绪彩排包
powershell -File scripts\run-owner-unblock-rehearsal.ps1

# 律师签字回填（S2）
python scripts\apply-comp-06-lawyer-signoff.py --name 律师姓名 --firm 律所名

# 完整 staging preflight 重跑
powershell -File scripts\run-arch-01-cert-gate.ps1
```

## 研发维持

- 每周五：`powershell -File scripts\qa-weekly-cert-gate.ps1`
- 签字回填后：`python scripts/sync-owner-blockers-from-records.py`
