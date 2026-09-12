"""租户级 AI 配置路由"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.response import success_response, error_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.ai_config import TenantAiProviderConfig, AIModelProvider
from app.core.field_crypto import encrypt_field, decrypt_field


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/tenant-ai-config"
ROUTE_TAGS = ["租户AI配置"]

router = APIRouter(prefix="/ai-config", tags=["租户AI配置"])


@router.get("/my-configs")
def get_my_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前租户的AI配置列表"""
    tenant_id = current_user.tenant_id
    if not tenant_id:
        return error_response(400, "用户未关联租户")

    configs = (
        db.query(TenantAiProviderConfig)
        .filter(
            TenantAiProviderConfig.tenant_id == tenant_id,
            TenantAiProviderConfig.user_id == current_user.id
        )
        .order_by(TenantAiProviderConfig.created_at.desc())
        .all()
    )
    items = []
    for c in configs:
        items.append({
            "id": str(c.id),
            "name": c.name,
            "providerId": c.provider_id,
            "protocol": c.protocol,
            "modelName": c.model_name,
            "baseUrl": c.base_url,
            "apiKey": "***" if c.api_key_encrypted else "",
            "enabled": c.enabled,
            "temperature": float(c.temperature or 0.1),
            "scopes": c.scopes or [],
            "testStatus": c.test_status,
            "lastTestTime": c.last_test_time.isoformat() if c.last_test_time else None,
        })

    return success_response(data={"items": items, "total": len(items)})


@router.post("/my-configs")
def create_config(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建租户AI配置"""
    tenant_id = current_user.tenant_id
    if not tenant_id:
        return error_response(400, "用户未关联租户")

    api_key = req.get("apiKey", "")
    config = TenantAiProviderConfig(
        tenant_id=tenant_id,
        user_id=current_user.id,
        name=req.get("name", ""),
        provider_id=req.get("providerId", ""),
        protocol=req.get("protocol", "openai_compatible"),
        model_name=req.get("modelName", ""),
        base_url=req.get("baseUrl"),
        api_key_encrypted=encrypt_field(api_key) if api_key else None,
        enabled=req.get("enabled", False),
        temperature=str(req.get("temperature", 0.1)),
        scopes=req.get("scopes", []),
        test_status="pending",
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return success_response(
        data={"id": str(config.id)},
        message="配置创建成功"
    )


@router.put("/my-configs/{config_id}")
def update_config(
    config_id: str,
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新租户AI配置"""
    config = (
        db.query(TenantAiProviderConfig)
        .filter(
            TenantAiProviderConfig.id == config_id,
            TenantAiProviderConfig.tenant_id == current_user.tenant_id,
            TenantAiProviderConfig.user_id == current_user.id
        )
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    if "name" in req:
        config.name = req["name"]
    if "providerId" in req:
        config.provider_id = req["providerId"]
    if "protocol" in req:
        config.protocol = req["protocol"]
    if "modelName" in req:
        config.model_name = req["modelName"]
    if "baseUrl" in req:
        config.base_url = req["baseUrl"]
    if "enabled" in req:
        config.enabled = req["enabled"]
    if "apiKey" in req and req["apiKey"]:
        config.api_key_encrypted = encrypt_field(req["apiKey"])
    if "temperature" in req:
        config.temperature = str(req["temperature"])
    if "scopes" in req:
        config.scopes = req["scopes"]

    db.commit()
    return success_response(message="配置更新成功")


@router.delete("/my-configs/{config_id}")
def delete_config(
    config_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除租户AI配置"""
    config = (
        db.query(TenantAiProviderConfig)
        .filter(
            TenantAiProviderConfig.id == config_id,
            TenantAiProviderConfig.tenant_id == current_user.tenant_id,
            TenantAiProviderConfig.user_id == current_user.id
        )
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    db.delete(config)
    db.commit()
    return success_response(message="配置删除成功")


@router.post("/test-config/{config_id}")
def test_config(
    config_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """测试租户AI配置连接"""
    config = (
        db.query(TenantAiProviderConfig)
        .filter(
            TenantAiProviderConfig.id == config_id,
            TenantAiProviderConfig.tenant_id == current_user.tenant_id,
            TenantAiProviderConfig.user_id == current_user.id
        )
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 真实连接测试
    import httpx
    try:
        api_key = decrypt_field(config.api_key_encrypted) if config.api_key_encrypted else ""
        base_url = (config.base_url or "").rstrip("/")
        if not api_key or not base_url:
            config.test_status = "failed"
            config.last_test_time = datetime.now(timezone.utc)
            db.commit()
            return error_response(400, "API Key 或 Base URL 未配置")

        # 发送最小测试请求
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": config.model_name, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1}
        resp = httpx.post(f"{base_url}/chat/completions", json=payload, headers=headers, timeout=10)
        config.test_status = "success" if resp.status_code < 400 else "failed"
        config.last_test_time = datetime.now(timezone.utc)
        db.commit()
        if resp.status_code < 400:
            return success_response(message="连接测试成功")
        else:
            return error_response(resp.status_code, f"测试失败: HTTP {resp.status_code}")
    except Exception as e:
        config.test_status = "failed"
        config.last_test_time = datetime.now(timezone.utc)
        db.commit()
        return error_response(500, f"测试失败: {str(e)}")


@router.get("/providers")
def list_providers(
    current_user: User = Depends(get_current_user),
):
    """获取支持的AI供应商列表"""
    providers = [
        {
            "id": "openai",
            "name": "OpenAI",
            "icon": "SearchOutlined",
            "defaultBaseUrl": "https://api.openai.com/v1",
            "defaultModel": "gpt-4o-mini"
        },
        {
            "id": "deepseek",
            "name": "DeepSeek",
            "icon": "CodeOutlined",
            "defaultBaseUrl": "https://api.deepseek.com/v1",
            "defaultModel": "deepseek-chat"
        },
        {
            "id": "qwen",
            "name": "通义千问",
            "icon": "GlobalOutlined",
            "defaultBaseUrl": "https://dashscope.aliyuncs.com/api/v1",
            "defaultModel": "qwen-turbo"
        },
        {
            "id": "claude",
            "name": "Claude",
            "icon": "RobotOutlined",
            "defaultBaseUrl": "https://api.anthropic.com",
            "defaultModel": "claude-3-haiku-20240307"
        },
        {
            "id": "gemini",
            "name": "Google Gemini",
            "icon": "MailOutlined",
            "defaultBaseUrl": "https://generativelanguage.googleapis.com",
            "defaultModel": "gemini-pro"
        },
        {
            "id": "moonshot",
            "name": "Moonshot Kimi",
            "icon": "RocketOutlined",
            "defaultBaseUrl": "https://api.moonshot.cn/v1",
            "defaultModel": "moonshot-v1-8k"
        },
        {
            "id": "zhipu",
            "name": "智谱 GLM",
            "icon": "ThunderboltOutlined",
            "defaultBaseUrl": "https://open.bigmodel.cn/api/paas/v4",
            "defaultModel": "glm-4-flash"
        },
        {
            "id": "baidu",
            "name": "百度千帆",
            "icon": "CloudOutlined",
            "defaultBaseUrl": "https://aip.baidubce.com",
            "defaultModel": "ernie-3.5-8k"
        },
        {
            "id": "volcano",
            "name": "火山豆包",
            "icon": "FireOutlined",
            "defaultBaseUrl": "https://ark.cn-beijing.volces.com/api/v3",
            "defaultModel": "doubao-lite-32k"
        },
        {
            "id": "ollama",
            "name": "Ollama / 本地",
            "icon": "DesktopOutlined",
            "defaultBaseUrl": "http://localhost:11434",
            "defaultModel": "llama3"
        }
    ]
    return success_response(data={"items": providers, "total": len(providers)})
