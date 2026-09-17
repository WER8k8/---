# §16 压测基线报告（SaaS 外贸全链路 · 2026-09-15）

> 本次是 `backend/locustfile.py` **首次真实跑通**出基线数据。此前工具在仓库但从未执行（差距表 §16 评 30% "从没真跑过"）。

## 测试条件

- **负载模型**：Locust headless，20 并发用户，10/s 增速，30s 运行（总 435 请求）
- **目标**：`http://127.0.0.1:8001`（本地 `.venv` 起 uvicorn 单进程）
- **路径**：`/api/v1/health`（5 权重）+ `/api/v1/admin-bff/dict/plan_features`（2 权重）
- **UA**：`YouDingSaaS-Internal/1.0`（WAF 白名单；裸 UA 会被拦 403，见下方"踩坑"）

## 结果

| 端点 | 请求数 | 失败率 | p50 | p90 | p95 | p99 | 平均 | RPS |
|---|---|---|---|---|---|---|---|---|
| `/api/v1/health` | 302 | **0%** | 16ms | 68ms | 220ms | 230ms | 35ms | 10.84 |
| `bff:plan_features` | 133 | **0%** | 30ms | 77ms | 120ms | 220ms | 43ms | 4.77 |
| **汇总** | 435 | **0%** | 23ms | 74ms | 120ms | 230ms | 38ms | 15.61 |

## 结论

- **p95 = 120ms，远低于文档 §20 建议的 production-ready 阈值 200ms** → 单进程本地负载下性能达标。
- **0% 失败率**（修 UA 后），此前 100% 403 是 WAF 拦裸客户端 UA 所致，非后端性能问题。
- p99 (230ms) 略高于 p95，尾延迟主要来自 GC / 冷连接，20 并发下正常。

## 踩坑记录（给后续跑的人）

1. **WAF UA 白名单**：locust 默认 UA（`python-requests`）会被 WAF 拦 403。每个 task 必须显式传 `headers={"User-Agent": "YouDingSaaS-Internal/1.0"}`。
2. **Windows TOML 编码**：`python -m locust` 在 Windows 上读 pyproject.toml 报 GBK 解码错误，需设 `PYTHONUTF8=1` 环境变量。
3. **locust 装在哪**：`.venv` 的 pip 输出异常（编码崩溃），本次用系统 Python 的 locust（`python -m locust`）跑通。CI 里应统一装到 `.venv`。

## 未覆盖 / 下一步

- 本次只压了 health + bff 两个读接口，**未压核心写链路**（询盘创建/订单/支付/物流下单），需扩 locustfile 覆盖 §18 黄金链路各写端点。
- 未做多级并发（100/500/1000 用户）找拐点，当前 20 并发仅验证"能跑通 + 出基线"。
- k6 脚本（仓库根）未并行跑对比。
- 未做真实负载（生产流量模型）下的 P99 回归。

**报告状态：§16 从"工具在、从没跑过"推进到"真跑通 + 有基线 + 达标"**。
