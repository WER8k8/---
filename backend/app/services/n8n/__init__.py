# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""n8n 集成服务模块。

提供 n8n 工作流触发、Webhook 接收、工作流注册三大能力：
- webhook.py  : 接收 n8n 回调（HMAC-SHA256 签名验证 + 事件分发）
- trigger.py  : 触发 n8n 工作流（Celery 异步执行 + 指数退避重试）
- workflow_registry.py : 工作流注册表（注册/管理/启用禁用）

典型业务场景：
- 产品创建 → 触发 n8n → 自动建站
- 新内容发布 → 触发 n8n → 自动分发
- 新 Lead → 触发 n8n → 通知销售
"""

from app.services.n8n.trigger import N8nTriggerService, trigger_n8n_workflow
from app.services.n8n.webhook import N8nWebhookService, verify_webhook_signature
from app.services.n8n.workflow_registry import WorkflowRegistry, get_workflow_registry

__all__ = [
    "N8nTriggerService",
    "N8nWebhookService",
    "WorkflowRegistry",
    "trigger_n8n_workflow",
    "verify_webhook_signature",
    "get_workflow_registry",
]
