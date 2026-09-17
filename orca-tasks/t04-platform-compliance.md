## 任务：§3 多平台发帖合规预检

工作目录：$BASE/backend
现有代码：
- backend/app/services/publish_capability_registry.py
- backend/app/services/foreign_trade/publish_preflight_checklist_service.py
产出：outputs/prime-agent/t04-platform-compliance/

### 实现：platform_compliance_checker.py
路径：backend/app/services/platform_compliance_checker.py

平台特化校验规则：
- 微博：字数≤2000，话题标签≤10个
- 小红书：字数≤1000，图片≤9张，禁止外链
- LinkedIn：字数≤3000，话题标签≤5个
- Twitter/X：字数≤280，URL自动缩短
- Facebook：字数≤63206
- Instagram Caption：字数≤2200，话题标签≤30个
- YouTube Title：≤100字符，Description≥100字符

实现 validate_post_content(content, platform) → {valid: bool, violations: [...], suggestions: [...]}
集成到 publish_dispatch_service 发布前调用
