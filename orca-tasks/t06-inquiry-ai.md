## 任务：§7 询盘AI智能分级分类

工作目录：$BASE/backend
现有代码：
- backend/app/services/foreign_trade/inquiry_pipeline_service.py
- backend/app/services/inquiries_unified_service.py
产出：outputs/ante/t06-inquiry-ai/

### 实现：inquiry_ai_classifier.py
路径：backend/app/services/foreign_trade/inquiry_ai_classifier.py

1. 特征提取：
   - 来源渠道（webform/WhatsApp/email/LinkedIn）
   - 买家公司信息（国家/行业/公司规模）
   - 询盘内容语义（用 AIEngine 提取 key intents）
   - 历史交互（是否有之前沟通记录）

2. 多级评分：
   - MQL score (0-100): 基于来源可信度 + 信息完整度
   - SQL score (0-100): 基于购买意图信号（MOQ/规格/交期明确）
   - Priority tier: hot/warm/cold/nuisance

3. 自动标签：
   - industry_tag（建材/五金/装饰等）
   - urgency_tag（urgency keywords detection）
   - language_preference（从语言推断）

4. 集成到 inquiries_unified_service 的 create/update 流程
