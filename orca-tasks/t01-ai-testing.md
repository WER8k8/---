## 任务：§14 AI能力测试体系实现

工作目录：$BASE/backend
产出：outputs/ante/t01-ai-testing/

### 1. 意图识别测试集 (intent_test_set.py)
路径：backend/tests/unit/test_ai_intent_recognition.py
内容：
- 定义至少 20 条意图样本（每条含：user_input, expected_intent, confidence_threshold）
- 意图类别：general_qa, content_gen, code_gen, seo_analysis, translation, negotiation, inquiry_classification, video_generation
- 用现有 AIEngine.generate() 调用并验证输出符合预期意图
- 用 pytest 结构编写

### 2. 幻觉检测器 (hallucination_detector.py)
路径：backend/app/services/ai/hallucination_detector.py
核心逻辑：
- fact_check(prompt, response) → 返回 {is_hallucinated: bool, reason: str, confidence: float}
- 基于关键词一致性检测：提取 response 中的专有名词/数字，与 prompt 对比
- 基于自我矛盾检测：检测 response 内部前后矛盾
- 集成到 AIEngine 的 generate 链，作为 post-process 钩子

### 3. Prompt注入防御中间件 (prompt_injection_middleware.py)
路径：backend/app/core/prompt_injection_middleware.py
- 注册为 FastAPI middleware，拦截所有含 AI prompt 的 POST/PUT 请求
- 使用正则+语义规则检测注入模式（与 negotiation.py 中的模式对齐并扩展）
- 返回 403 + 安全事件记录到 audit log
- 写单元测试：至少 10 条攻击样本全部拦截

运行：pytest backend/tests/unit/test_ai_intent_recognition.py backend/tests/unit/test_prompt_injection_middleware.py -v
