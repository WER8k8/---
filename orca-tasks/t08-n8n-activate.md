## 任务：§12 编排引擎激活n8n真实工作流

工作目录：$BASE/backend
现有代码：
- backend/app/services/n8n/workflow_registry.py (有注册机制但active:false)
- backend/app/api/v1/n8n.py (webhook endpoint)
产出：outputs/claude-teams/t08-n8n-activate/

### 实现：
1. 激活 site_built_notify 工作流：
   - 在 workflow_registry.py 的 ensure_builtin_workflows() 中
   - 设置默认 enabled=True（开发环境）
   - 添加 webhook payload 构造器

2. 添加内容发布分发工作流：
   - content_publish_dispatch 默认 enabled=True
   - 注册到 publish_dispatch_service 的回调链

3. 创建 n8n_trigger_service.py：
   - trigger_workflow(workflow_id, payload) → {success, response, timing_ms}
   - 超时/重试/错误分类
   - 集成到 Hermes 编排节点

4. 写集成测试：tests/unit/test_n8n_workflow_trigger.py
