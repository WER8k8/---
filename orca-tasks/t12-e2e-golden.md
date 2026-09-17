## 任务：§18 E2E黄金链路跑通

工作目录：$BASE/backend
现有代码：backend/tests/e2e/ (骨架), playwright scripts
产出：outputs/trae/t12-e2e-golden/

### 黄金链路（优先级①）：
1. tenant注册 → 官网搭建 → 发布内容 → 收到询盘 → AI分级 → 自动谈单 → 成交制单 → 物流下单
2. 编写 tests/e2e/test_golden_chain.py：
   - 使用 test client fixture，不依赖真实外部API
   - 每一步断言状态转换正确
   - 预计时长：3-5分钟完整跑通

3. CI接入：.github/workflows/e2e-golden.yml（如有 GitHub Actions）
   - 或在 CI 配置中增加 e2e 步骤
