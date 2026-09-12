# Owner Blocker 清单（MOD-08 · ARCH-04 · QA-04）

> **任务**：MOD-08 / ARCH-04 / QA-04 共用  
> **更新**：2026-06-02

| # | Owner 需提供 | 阻塞任务 | 状态 |
|---|-------------|----------|------|
| 1 | **HTTPS 演示域**（如 `demo.youding.com`） | MOD-01 · ARCH-04 · QA-04 72h | ☐ |
| 2 | **DNS A 记录** 指向 staging 服务器 | ARCH-04 Certbot | ☐ |
| 3 | **Certbot 邮箱**（`CERTBOT_EMAIL`） | Let's Encrypt | ☐ |
| 4 | SaaS 专家 **BJ-01 五问签字** | 百家 10/10 | ☐ |
| 5 | PM-06 **Blocked 书面**（若 1–3 延期） | 滚动 | ☐ |

**可机读跟踪**：`mod-08-owner-blockers.json` · `validate-mod-08-blockers.py`

**研发侧已就绪**

- staging 自签 SSL：`docker/nginx/ssl/*.pem`
- nginx HTTPS 配置：`validate-arch-04-nginx-ssl.py` PASS
- Locust 冒烟 + 干跑脚本：`scripts/qa-locust-*.ps1`
