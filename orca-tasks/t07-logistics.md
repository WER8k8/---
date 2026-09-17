## 任务：§10 物流智能路由规划与多商比价

工作目录：$BASE/backend
现有代码：
- backend/app/services/logistics_provider.py (骨架)
- backend/app/services/logistics_executor.py (占位)
- /api/v1/lbs-routing (返回0的占位)
产出：outputs/devin/t07-logistics/

### 实现：logistics_router_service.py
路径：backend/app/services/logistics_router_service.py

1. 多物流商比价引擎：
   - QueryMultipleProviders(origin, destination, weight, volume, urgency) → List[Quote]
   - 报价字段：carrier, service_type, transit_days, cost, estimated_delivery_date

2. 智能路由选择：
   - 多目标排序：cost(权重0.4) + time(权重0.3) + reliability(权重0.3)
   - 支持自定义偏好（最快/最省/最稳）

3. 时效预测模型（轻量规则引擎）：
   - 基于历史数据 + 航线常识给出范围估计
   - 陆运/空运/海运分别估算

4. 对接 /api/v1/lbs-routing 端点，替换占位返回
