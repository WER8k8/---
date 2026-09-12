# Staging 送检环境清单（ARCH-C01 / ARCH-C02）

> **目标**：Postgres + Redis + 生产形态 preflight **0 fail**，支撑 72h 可靠性与 Locust 1000 并发附件。  
> **源码仓**：`C:\Users\97907\Desktop\上线网站`  
> **一键脚本**：`scripts/run-staging-preflight.ps1`

---

## 1. 前置条件

| 项 | 要求 |
|----|------|
| Docker Desktop | 运行中 |
| 端口 | 5433（Postgres）、6379（Redis）未被占用 |
| Python venv | `backend/.venv` 已创建 |
| 磁盘 | ≥ 10GB 空闲（镜像 + 数据卷） |

---

## 2. 调用逻辑（5 步）

```text
run-staging-preflight.ps1
  1/5  docker compose -f docker-compose.dev.yml up -d postgres redis
  2/5  alembic upgrade head（DATABASE_URL=postgresql://…:5433/youding_dev）
  3/5  seed_platforms_full.py
  4/5  run_production_preflight.py --production
         ENVIRONMENT=production
         MVP_LAUNCH=1, PAYMENT_STRICT_VERIFY=1, SSL_PROVIDER=certbot
         REDIS_ENABLED=true, FRONTEND_URL=https://demo.youding.local
  5/5  docker compose --profile ops run publish-worker-once（可选 Celery smoke）
```

**输出**：`docs/production-preflight-latest.json`  
**退出码**：0 = PASS

---

## 3. 环境变量（staging 最小集）

| 变量 | 示例 | 说明 |
|------|------|------|
| `DATABASE_URL` | `postgresql://youding:youding@127.0.0.1:5433/youding_dev` | 送检库 |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | 缓存/队列 |
| `JWT_SECRET_KEY` | ≥32 字符随机 | 禁止弱密钥 |
| `SECRET_KEY` | 同 JWT 或独立强密钥 | preflight 检查 |
| `ENVIRONMENT` | `production` | 触发严格检查 |
| `FRONTEND_URL` | `https://demo.youding.local` | HTTPS 口径 |
| `G4_AI_*` | 真实 Key（送检） | gates-check G4 |

---

## 4. HTTPS 与域名（送检对外）

| 项 | 状态 | 待办 |
|----|------|------|
| 演示域名 | 待 PM 确认 | 1 个 HTTPS 独立域（见 `module-progress` pm_blockers） |
| 证书 | certbot / 云厂商 | `SSL_PROVIDER=certbot` 实跑记录 |
| 反向代理 | Nginx / Caddy | `deploy/production/` 对照 |

---

## 5. 送检附件（Phase C）

| ID | 交付物 | 命令/工具 | 状态 |
|----|--------|-----------|------|
| QA-C04 | Locust 1000 用户 | `backend/load_test.py` + 实环境 | 待跑 |
| 可靠性 | 72h 长跑 | `scripts/run-reliability-smoke.py` 或运维监控 | 待跑 |
| BE-C02 | Postgres pytest + coverage | `pytest --cov` on staging DB | 待跑 |
| ARCH-C03 | G1–G7 gates | `docs/gates-check-latest.json` | G4 待 Key |

---

## 6. 每日验证命令

```powershell
# Staging 全链路（需 Docker）
powershell -ExecutionPolicy Bypass -File scripts/run-staging-preflight.ps1

# 仅工程门禁（无需 Docker）
powershell -ExecutionPolicy Bypass -File scripts/run-provincial-cert-gate.ps1
```

---

## 7. 与 GB25000 审查报告关系

- **工程门禁绿**（SQLite + cert:gate）≠ **staging preflight 绿**  
- 对外声明「生产就绪」须本节 4/5 节附件齐全  
- 详见 `docs/申报材料/GB25000.51-合规审查报告-2026-05-31.md` 第四节 P1 staging

**架构负责人签字**：____________ **日期**：____________
