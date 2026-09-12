# 本地 IDE 与网站系统能力对照表

> **原则**：别再把 Cursor/ECC 当成「网站功能」；别把 UBrain/抓取 当成「装 IDE 就有」。

---

## 对照表

| 能力 | 本地编程软件（Cursor/VS Code） | 网站服务器（要部署） |
|------|-------------------------------|----------------------|
| ECC 规则 / 38 门控 | ✅ `.cursor/` | ❌ 不部署 |
| Agency 222 编排 | ✅ 对话时 | ❌ |
| CodeGraph MCP | ✅ 本机索引 | ❌ |
| continuous-learning-v2 自我进化 | ✅ **仅 Cursor 会话 hooks**（`.cursor/hooks` 等）；不写入网站 DB | ❌ 不部署；**不等于**全站 `ai_learning` API |
| 写代码 / pytest | ✅ 终端 | ❌（CI 另说） |
| 管理端 / 租户站页面 | 仅调试 `localhost:5173` | ✅ 生产域名 |
| UBrain 副驾 / 聊天 | — | ✅ `backend` API |
| 商业飞轮（记忆/流水线/反馈） | — | ✅ `UBRAIN_AUTO_PIPELINE` |
| DeerFlow / Accio | — | ✅ |
| 出海参谋 trade-intel | — | ✅ |
| 国际抓取 Webhook | — | ✅ + 外置 Worker |
| GEO 技术雷达 / 竞品定时 | — | ✅ Celery beat 已注册；**MVP 仅计划+Redis 标记**（见 `docs/geo/tech-radar-MVP.md`） |
| 创始人诊断 / 国密 | — | ✅ |
| 神经精神网络 NSN（愿景） | 文档 `NEURAL_SPIRIT_NETWORK.md` | 落地≈UBrain+飞轮，**非** ECC |
| ai_learning「进化」API | — | ✅ 聚合 UBrain 表 + 操作日志（非 RL 训练） |
| 定时运维（冻结/发布队列） | — | ✅ crontab |

---

## 部署清单

**服务器要带**：`backend/`、`frontend` 构建产物、`.env`、数据库、可选 Redis/Celery。

**不必为运行而带**：`.cursor/`、`.lingma/`、`v1.10.0/ECC-*`（文档可留 Git）。

---

## 调试方式（固定）

任意 IDE → 终端 **8001 + 5173** → **内置浏览器** `/login` → 超管后台。

详见 [换机与本地调试清单.md](./换机与本地调试清单.md)。
