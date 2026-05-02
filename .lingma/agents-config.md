# 智能体技能与工具配置清单

## 📋 配置说明

根据15S规则"整顿(SEITON)"要求，按任务类型明确智能体分工，绑定对应技能和工具，实现"专人专岗、专模专用"。

---

## 🎯 核心智能体配置

### 1. 架构指挥官 (architecture-commander)

**职责**: 全局统筹、技术决策、智能体调度

**绑定模型**: moonshotai/kimi-k2.6 (长上下文能力强)

**配备技能**:
- `agent-commander` - 多智能体指挥调度
- `multi-agent-orchestrator` - 智能体编排
- `compute-booster` - 算力优化调度
- `adaptive-thinking` - 自适应思维框架

**配备工具**:
- Read, Write, Edit - 文件操作
- Glob, Grep - 代码搜索
- Bash - 命令执行
- Task - 子任务分发
- AskUserQuestion - 需求确认

**触发场景**: 架构设计、技术选型、全局统筹、性能优化、智能体调度

---

### 2. 前端架构师 (frontend-architect)

**职责**: 前端架构设计、技术选型、工程化配置

**绑定模型**: qwen/qwen3-next-80b-a3b-instruct

**配备技能**:
- `frontend-architect` - 前端架构设计
- `frontend-design` - 前端设计规范
- `webapp-testing` - 前端测试

**配备工具**:
- Read, Write, Edit - 组件开发
- Glob, Grep - 代码查找
- Bash - 构建命令
- mcp__quest__get_problems - 问题检测

**触发场景**: 前端架构设计、组件库开发、工程化配置、性能优化

---

### 3. 网页开发/UI还原 (web-designer + display-visual-designer)

**职责**: UI设计、页面搭建、视觉还原

**绑定模型**: qwen/qwen3-coder-480b-a35b-instruct

**配备技能**:
- `website-designer` - 网站设计
- `display-visual-designer` - 视觉设计
- `brand-guidelines` - 品牌规范
- `theme-factory` - 主题生成
- `canvas-design` - 画布设计

**配备工具**:
- Read, Write, Edit - 样式编写
- mcp__genui__show_widget - UI预览
- mcp__genui__load_guidelines - 设计规范加载

**触发场景**: 页面设计、UI还原、响应式适配、视觉优化

---

### 4. 全栈开发专家 (fullstack-developer)

**职责**: 全栈功能开发、前后端联调

**绑定模型**: deepseek-ai/deepseek-coder-6.7b-instruct

**配备技能**:
- `fullstack-developer` - 全栈开发
- `api-integration` - API集成
- `code-analysis` - 代码分析
- `auto-fix` - 自动修复

**配备工具**:
- Read, Write, Edit - 代码编写
- Bash - 服务启动
- mcp__quest__search_symbol - 符号搜索
- mcp__quest__search_codebase - 代码库搜索

**触发场景**: 功能开发、API对接、Bug修复、代码重构

---

### 5. 后端架构师 (insulation-backend-architect)

**职责**: 后端架构设计、技术选型

**绑定模型**: meta/llama-3.1-405b-instruct

**配备技能**:
- `insulation-backend-architect` - 后端架构
- `insulation-backend-expert` - 后端专家
- `database-tools` - 数据库工具

**配备工具**:
- Read, Write, Edit - 架构文档
- Bash - 数据库操作
- mcp__supabase__* - 数据库管理

**触发场景**: 后端架构设计、数据库设计、技术方案制定

---

### 6. 后端开发专家 (insulation-backend-developer)

**职责**: 后端API开发、业务逻辑实现

**绑定模型**: deepseek-ai/deepseek-coder-6.7b-instruct

**配备技能**:
- `insulation-backend-developer` - 后端开发
- `insulation-api-developer` - API开发
- `shell-tools` - Shell工具

**配备工具**:
- Read, Write, Edit - API开发
- Bash - 服务运行
- mcp__quest__run_preview - 预览服务器

**触发场景**: API开发、业务逻辑实现、数据库操作

---

### 7. 数据库架构师 (insulation-database-architect)

**职责**: 数据库设计、性能优化、数据迁移

**绑定模型**: meta/llama-3.1-70b-instruct

**配备技能**:
- `insulation-database-architect` - 数据库架构
- `database-tools` - 数据库工具
- `building-materials-database-expert` - 建材数据库专家

**配备工具**:
- Read, Write, Edit - Schema设计
- Bash - 数据库命令
- mcp__supabase__execute_sql_query - SQL执行

**触发场景**: 数据库设计、索引优化、数据迁移

---

### 8. DevOps工程师 (insulation-devops-engineer)

**职责**: CI/CD配置、Docker容器化、自动化部署

**绑定模型**: meta/llama-3.1-70b-instruct

**配备技能**:
- `insulation-devops-engineer` - DevOps工程
- `cloud-deployment` - 云部署
- `mcp-tool-creator` - MCP工具创建

**配备工具**:
- Read, Write, Edit - 配置文件
- Bash - 部署命令
- Docker相关命令

**触发场景**: 部署配置、CI/CD流程、容器化

---

### 9. 代码审查专家 (insulation-code-review-expert)

**职责**: 代码质量审查、安全漏洞检测

**绑定模型**: meta/llama-3.1-70b-instruct

**配备技能**:
- `insulation-code-review-expert` - 代码审查
- `root-cause-analysis` - 根因分析
- `auto-fix` - 自动修复

**配备工具**:
- Read, Grep, Glob - 代码检查
- mcp__quest__get_problems - 问题检测
- Bash - Git diff

**触发场景**: PR审查、代码质量检查、安全审计

---

### 10. 算法解题专家 (algorithm-problem-solver)

**职责**: 算法问题求解、性能优化

**绑定模型**: mistralai/mistral-large-3-675b-instruct-2512

**配备技能**:
- `algorithm-problem-solver` - 算法求解
- `top-algorithm-coach` - 算法指导
- `math-analysis` - 数学分析

**配备工具**:
- Read, Write, Edit - 算法实现
- Bash - 性能测试
- Python执行环境

**触发场景**: 复杂算法、性能瓶颈、数据结构优化

---

### 11. SEO营销专家 (ai-marketing-website-expert)

**职责**: SEO优化、营销策略、获客功能

**绑定模型**: z-ai/glm4.7

**配备技能**:
- `ai-marketing-website-expert` - AI营销网站
- `doc-coauthoring` - 文档协作
- `internal-comms` - 内部沟通

**配备工具**:
- Read, Write, Edit - SEO配置
- WebSearch - 竞品分析
- WebFetch - 页面抓取

**触发场景**: SEO优化、营销页面、转化率优化

---

### 12. Git专家 (git-expert)

**职责**: 版本控制、分支管理、Git工作流

**绑定模型**: minimaxai/minimax-m2.7

**配备技能**:
- `git-expert` - Git专家

**配备工具**:
- Bash - Git命令
- Read - 文件查看
- Glob - 文件查找

**触发场景**: Git操作、分支合并、冲突解决

---

### 13. 产品经理 (insulation-material-product-manager)

**职责**: 产品规划、需求分析、PRD文档

**绑定模型**: z-ai/glm4.7

**配备技能**:
- `insulation-material-product-manager` - 产品经理
- `doc-coauthoring` - 文档协作

**配备工具**:
- Read, Write - 文档编写
- AskUserQuestion - 需求确认

**触发场景**: 需求分析、产品规划、PRD编写

---

### 14. 项目经理 (insulation-digital-project-manager)

**职责**: 项目管理、进度跟踪、资源协调

**绑定模型**: minimaxai/minimax-m2.7

**配备技能**:
- `insulation-digital-project-manager` - 数字项目经理

**配备工具**:
- Read, Write - 进度文档
- AskUserQuestion - 状态确认
- TodoWrite - 任务管理

**触发场景**: 项目规划、进度跟踪、风险管理

---

### 15. 解决方案文档专家 (solution-document-writer)

**职责**: 技术方案文档、架构文档

**绑定模型**: z-ai/glm4.7

**配备技能**:
- `solution-document-writer` - 解决方案文档
- `doc-coauthoring` - 文档协作
- `pdf` - PDF处理
- `docx` - Word文档处理

**配备工具**:
- Read, Write - 文档编写
- Glob - 文件收集

**触发场景**: 技术文档、架构文档、用户手册

---

### 16. 合规开发专家 (insulation-compliance-developer)

**职责**: 广告法合规、内容审查

**绑定模型**: z-ai/glm4.7

**配备技能**:
- `insulation-compliance-developer` - 合规开发

**配备工具**:
- Read, Grep - 内容检查
- Write - 合规报告

**触发场景**: 内容审查、合规检查、敏感词检测

---

### 17. 后端安全专家 (insulation-backend-security-expert)

**职责**: 系统安全、漏洞防护

**绑定模型**: meta/llama-3.1-70b-instruct

**配备技能**:
- `insulation-backend-security-expert` - 后端安全

**配备工具**:
- Read, Grep - 安全检查
- Bash - 安全扫描

**触发场景**: 安全审计、漏洞修复、权限控制

---

### 18. 后端测试专家 (insulation-backend-testing-expert)

**职责**: API测试、集成测试

**绑定模型**: meta/llama-3.1-70b-instruct

**配备技能**:
- `insulation-backend-testing-expert` - 后端测试
- `webapp-testing` - Web应用测试

**配备工具**:
- Read, Write - 测试用例
- Bash - 测试执行

**触发场景**: 单元测试、集成测试、E2E测试

---

### 19. 后端优化专家 (insulation-backend-optimization-expert)

**职责**: 性能优化、缓存策略

**绑定模型**: meta/llama-3.1-70b-instruct

**配备技能**:
- `insulation-backend-optimization` - 后端优化
- `compute-booster` - 计算加速

**配备工具**:
- Read, Edit - 代码优化
- Bash - 性能测试

**触发场景**: 性能瓶颈、缓存优化、查询优化

---

### 20. 运维工程师 (insulation-operations-engineer)

**职责**: 系统监控、日志管理、故障排查

**绑定模型**: meta/llama-3.1-70b-instruct

**配备技能**:
- `insulation-operations-engineer` - 运维工程
- `root-cause-analysis` - 根因分析

**配备工具**:
- Read, Grep - 日志分析
- Bash - 系统命令

**触发场景**: 故障排查、监控告警、日志分析

---

### 21. 数据仓库专家 (insulation-data-warehouse-expert)

**职责**: 数据仓库设计、数据分析

**绑定模型**: meta/llama-3.1-70b-instruct

**配备技能**:
- `insulation-data-warehouse-expert` - 数仓专家
- `xlsx` - Excel处理

**配备工具**:
- Read, Write - 数据脚本
- Bash - 数据处理

**触发场景**: 数据分析、报表开发、ETL流程

---

### 22. 建材数据库专家 (building-materials-database-expert)

**职责**: 建材产品数据管理

**绑定模型**: z-ai/glm4.7

**配备技能**:
- `building-materials-database-expert` - 建材数据库

**配备工具**:
- Read, Write - 数据维护
- xlsx - Excel导入导出

**触发场景**: 产品数据录入、规格参数设计

---

### 23. 移动端网页开发 (mobile-web-developer)

**职责**: 响应式设计、移动端适配

**绑定模型**: qwen/qwen3-coder-480b-a35b-instruct

**配备技能**:
- `mobile-web-developer` - 移动端开发

**配备工具**:
- Read, Write, Edit - 样式编写
- mcp__genui__show_widget - 移动预览

**触发场景**: 移动端适配、响应式设计、PWA开发

---

### 24. 后台页面搭建 (backend-page-builder)

**职责**: 管理后台页面开发

**绑定模型**: qwen/qwen3-next-80b-a3b-instruct

**配备技能**:
- `backend-page-builder` - 后台页面搭建

**配备工具**:
- Read, Write, Edit - 页面开发
- mcp__genui__show_widget - 组件预览

**触发场景**: 后台页面、管理界面、表单开发

---

### 25. 陈列视觉设计师 (display-visual-designer)

**职责**: 网站视觉设计、UI组件设计

**绑定模型**: qwen/qwen3-coder-480b-a35b-instruct

**配备技能**:
- `display-visual-designer` - 视觉设计
- `brand-guidelines` - 品牌规范
- `theme-factory` - 主题工厂

**配备工具**:
- Read, Write - 设计规范
- mcp__genui__show_widget - 视觉预览
- mcp__genui__load_guidelines - 设计指南

**触发场景**: 视觉设计、UI规范、品牌设计

---

### 26. 顶级算法教练 (top-algorithm-coach)

**职责**: 算法指导、性能优化建议

**绑定模型**: mistralai/mistral-large-3-675b-instruct-2512

**配备技能**:
- `top-algorithm-coach` - 算法教练
- `algorithmic-art` - 算法艺术

**配备工具**:
- Read, Write - 算法文档
- Bash - 性能基准测试

**触发场景**: 算法优化、复杂度分析、数据结构选择

---

### 27. 顶级开发环境配置专家 (top-development-environment-expert-auto)

**职责**: 开发环境搭建、工具链配置

**绑定模型**: meta/llama-3.1-70b-instruct

**配备技能**:
- `top-development-environment-expert-auto` - 开发环境专家
- `auto-fix` - 自动修复

**配备工具**:
- Read, Write - 配置文件
- Bash - 环境安装
- CheckRuntime - 运行时检测

**触发场景**: 环境配置、依赖安装、IDE配置

---

### 28. 算法解题专家 (algorithm-problem-solver)

**职责**: 算法问题求解

**绑定模型**: mistralai/mistral-large-3-675b-instruct-2512

**配备技能**:
- `algorithm-problem-solver` - 算法求解
- `math-analysis` - 数学分析

**配备工具**:
- Read, Write - 算法实现
- Bash - 测试执行

**触发场景**: LeetCode题目、算法优化、动态规划

---

### 29. 解决方案文档专家 (solution-document-writer)

**职责**: 技术方案文档编写

**绑定模型**: z-ai/glm4.7

**配备技能**:
- `solution-document-writer` - 解决方案文档
- `doc-coauthoring` - 文档协作

**配备工具**:
- Read, Write - 文档编写
- pdf - PDF生成
- docx - Word文档

**触发场景**: 技术文档、方案书、验收报告

---

### 30. 全栈开发专家 (fullstack-developer)

**职责**: 全栈功能开发

**绑定模型**: deepseek-ai/deepseek-coder-6.7b-instruct

**配备技能**:
- `fullstack-developer` - 全栈开发
- `api-integration` - API集成

**配备工具**:
- Read, Write, Edit - 代码开发
- Bash - 服务运行
- mcp__quest__search_codebase - 代码搜索

**触发场景**: 功能开发、Bug修复、代码重构

---

### 31. 网站设计师 (web-designer)

**职责**: 网站整体设计、用户体验

**绑定模型**: qwen/qwen3-coder-480b-a35b-instruct

**配备技能**:
- `website-designer` - 网站设计
- `frontend-design` - 前端设计

**配备工具**:
- Read, Write - 设计规范
- mcp__genui__show_widget - 原型预览

**触发场景**: 网站设计、UX优化、交互设计

---

## 🔧 通用工具配置

所有智能体均配备以下基础工具：

| 工具 | 用途 |
|------|------|
| Read | 读取文件内容 |
| Write | 写入文件内容 |
| Edit | 编辑文件内容 |
| DeleteFile | 删除文件 |
| Glob | 文件模式匹配 |
| Grep | 内容搜索 |
| Bash | 命令执行 |
| TodoWrite | 任务管理 |
| AskUserQuestion | 用户询问 |
| WebSearch | 网络搜索 |
| WebFetch | 网页抓取 |

---

## 📌 调度规则

1. **优先级机制**:
   - P0: 架构指挥官 > 前端架构师 > 全栈开发
   - P1: 后端开发 > 数据库架构 > DevOps
   - P2: 代码审查 > 测试专家 > 安全专家
   - P3: 文档专家 > 产品经理 > 项目经理

2. **并行作业**:
   - 前端页面 + 后端API 可并行
   - 多个独立组件可并行
   - 文档编写 + 代码开发可并行

3. **串行依赖**:
   - 架构设计 → 技术选型 → 代码开发
   - 数据库设计 → API开发 → 前端对接
   - 开发完成 → 代码审查 → 测试验证

4. **兜底机制**:
   - 接口失败: 重试3次 → 切换内置模型
   - 模型卡顿: 自动切换轻量模型
   - 排队超时: 启用备用智能体

---

## 📝 更新记录

| 日期 | 更新内容 |
|------|----------|
| 2026-05-02 | 初始配置，31个智能体完整技能映射 |
