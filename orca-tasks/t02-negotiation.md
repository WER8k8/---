## 任务：§8 自动谈单补全

工作目录：$BASE/backend
现有代码：backend/app/api/v1/routes/negotiation.py (已有对话框架+底价+审批)
产出：outputs/anti-gravity/t02-negotiation/

### 补全缺失部分：
1. **阶梯让步曲线配置化** (negotiation_rules.py)
   - 从硬编码 if/elif 改为可配置规则引擎
   - 支持按行业/产品类别/客户等级设置不同让步斜率
   - 配置项：round_1_discount_pct, round_2_discount_pct, round_3_discount_pct, floor_margin_pct

2. **折扣审批流增强** (approval_flow.py)
   - 多级审批：sales_rep → sales_manager → director (超过阈值时)
   - 审批时效约束（24h/48h超时自动提醒）
   - 审批历史审计日志

3. **议价策略模板** (strategy_templates.py)
   - FOB vs CIF vs DDP 不同报价策略
   - MOQ 联动折扣表
   - 样品单 vs 大货单差异化策略

运行：python -c "from app.services.foreign_trade.negotiation_rules import *; print('OK')"
