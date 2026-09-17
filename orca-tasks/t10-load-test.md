## 任务：§16 真实压测执行 + 基线报告

工作目录：$BASE/backend
现有代码：
- backend/locustfile.py (骨架，从没跑过)
- k6 scripts in repo root
产出：outputs/trae/t10-load-test/

### 执行计划：
1. 修复 locustfile.py 使其能连上本地 :8001 后端
   - 添加 login → token → authenticated requests 流程
   - 关键 endpoint: /api/v1/auth/login, /api/v1/inquiries, /api/v1/content, /api/v1/products

2. 运行压测（本地）：
   - locust -f backend/locustfile.py --headless -u 50 -r 10 --run-time 60s --host http://127.0.0.1:8001
   - 收集: avg response time, p95, p99, error rate, RPS

3. 产出基线报告：docs/load-test-baseline-2026-09-15.md
   - 表格：每个endpoint的延迟分布
   - 瓶颈标注（DB连接池/内存/CPU）
   - 建议阈值（production-ready < 200ms p95）

4. 同时跑 k6 脚本（如有）对比结果
