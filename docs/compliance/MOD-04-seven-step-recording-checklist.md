# MOD-04 · 七步实机录屏清单（HTTPS 域就绪后执行）

> **前置**：MOD-01 Owner HTTPS 演示域 · ARCH-04 Certbot  
> **任务 ID**：MOD-04

| 步 | 场景 | 路由/动作 | 录屏文件名 |
|----|------|-----------|------------|
| 1 | 租户登录 | `/login` → Client | `mod04-01-login.mp4` |
| 2 | 四支柱导航 | `/client/dashboard` | `mod04-02-pillars.mp4` |
| 3 | 询盘队列 | `/client/queues/inquiries` | `mod04-03-inquiry-queue.mp4` |
| 4 | Plan Gate | 未开通能力 → `/client/plan-gate` | `mod04-04-plan-gate.mp4` |
| 5 | 超管 Top12 | `/admin/tenants` | `mod04-05-platform.mp4` |
| 6 | Agent 壳 | `/agent/performance` | `mod04-06-agent.mp4` |
| 7 | HTTPS 证书 | 浏览器锁标 + `curl -I https://{domain}` | `mod04-07-https.txt` |

**归档路径**：`docs/compliance/mod-04-recordings/`（录屏完成后 PM 更新 `module-progress.json`）
