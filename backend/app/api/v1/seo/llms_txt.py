# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.security import get_current_user, optional_auth
from app.models.seo import LlmsConfig
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter()

# 2026-09-25: 已保存 llms.txt 内容的存储键（复用既有 Tenant.settings JSON 列，无需迁移）。
LLMS_TXT_SAVED_KEY = "llms_txt_saved"


def _read_saved_llms_txt(tenant: Tenant) -> dict[str, Any]:
    """从租户 settings JSON 读取已保存的 llms.txt 内容。"""
    if not tenant.settings:
        return {}
    try:
        data = json.loads(tenant.settings)
    except (json.JSONDecodeError, TypeError):
        return {}
    return data.get(LLMS_TXT_SAVED_KEY, {}) or {}


def _write_saved_llms_txt(tenant: Tenant, payload: dict[str, Any]) -> None:
    """写入已保存的 llms.txt 内容到租户 settings JSON。"""
    try:
        data: Any = json.loads(tenant.settings) if tenant.settings else {}
    except (json.JSONDecodeError, TypeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    data[LLMS_TXT_SAVED_KEY] = payload
    tenant.settings = json.dumps(data, ensure_ascii=False)

SECTION_TEMPLATES = {
    "brand": "## {title}\n\n{content}\n\n",
    "product": "- [{title}]({url}): {description}\n",
    "faq": "- {question}: {answer}\n",
    "contact": "## {title}\n\n{content}\n\n",
}


class GenerateRequest(BaseModel):
    """管理端「生成」表单与结构化请求共用；未使用字段忽略。"""
    sections: list[dict] = Field(default_factory=list)
    include_ai_instructions: bool = True
    company_name: str = ""
    business: str = ""
    products: list[str] = Field(default_factory=list)
    # 管理端 llms-txt.vue 传入
    business_type: str = ""
    keywords: list[str] = Field(default_factory=list)
    ai_model: str = ""
    temperature: float = 0.3
    max_tokens: int = 2000


class ValidateRequest(BaseModel):
    content: str


class LlmsTxtSavedUpdate(BaseModel):
    """`PUT /api/v1/seo/llms-txt` 的保存负载（前端 saveContent 发送）。"""
    content: str = ""
    config: dict[str, Any] = Field(default_factory=dict)


@router.post("/generate")
def generate_llms_txt(req: GenerateRequest, db: Session = Depends(get_db)):
    """generate_llms_txt。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :return: 返回处理结果。
    """
    # 移除认证要求,作为公开API
    # current_user: User = Depends(optional_auth)
    lines = []
    lines.append("# LLMs.txt\n")
    biz = (req.business_type or req.business or req.company_name or "轻集料混凝土与保温建材").strip()
    lines.append(f"> 此文件帮助 AI 了解本站业务：{biz}\n")
    db_configs = db.query(LlmsConfig).filter(
        LlmsConfig.is_active).order_by(
        LlmsConfig.section).all()

    if req.keywords:
        lines.append("\n## 核心关键词\n\n")
        for kw in req.keywords:
            k = (kw or "").strip()
            if k:
                lines.append(f"- {k}\n")

    if req.sections:
        for section in req.sections:
            stype = section.get("type", "brand")
            template = SECTION_TEMPLATES.get(
                stype, "## {title}\n\n{content}\n\n")
            lines.append(template.format(**section))

    seen_sections: set[str] = set()
    if db_configs:
        for config in db_configs:
            key = (config.section or "").strip()
            if not key or key in seen_sections:
                continue
            seen_sections.add(key)
            lines.append(f"\n## {key}\n\n{config.content}\n")

    if req.include_ai_instructions:
        lines.append("""
## AI Instructions

This website is Youding Construction Materials Co., Ltd. (优丁建材).
We specialize in lightweight aggregate concrete (轻集料混凝土) products.
Technical specifications must be quoted as-is from our official documentation.
Key products: LC5.0-LC50 lightweight aggregate concrete, density range 800-1950 kg/m³.
For pricing inquiries, please direct users to our contact page.
""")

    result = "".join(lines)
    return {
        "content": result,
        "line_count": len(lines),
        "size_bytes": len(result.encode("utf-8")),
        "token_usage": 0,
        "cost": 0.0,
        "version": "1.0.0",
    }


@router.post("/validate-llms-txt")
def validate_llms_txt(
        req: ValidateRequest,
        current_user: User = Depends(optional_auth)):
    """validate_llms_txt。

    参数说明：
    :param req: 参数 req
    :param current_user: 参数 current_user
    :return: 返回处理结果。
    """
    issues = []
    content = req.content
    if not content.startswith("# LLMs.txt"):
        issues.append({"severity": "error", "message": "文件必须以# LLMs.txt开头"})

    section_count = content.count("## ")
    if section_count < 2:
        issues.append({"severity": "warning",
                       "message": f"sections数量过少({section_count}个)"})

    if len(content) < 200:
        issues.append({"severity": "warning", "message": "内容过短，建议至少200字符"})

    if "优丁" not in content and "youding" not in content.lower():
        issues.append({"severity": "warning",
                       "message": "未包含品牌名称(优丁/Youding)"})

    if "kg/m³" not in content and "kg/m3" not in content:
        issues.append({"severity": "info", "message": "未包含密度参数(kg/m³)"})

    return {
        "is_valid": len([i for i in issues if i["severity"] == "error"]) == 0,
        "issues": issues,
        "section_count": section_count,
    }


@router.get("/llms-txt-template")
def get_llms_txt_template():
    """get_llms_txt_template。
    :return: 返回处理结果。
    """
    return {
        "template": """# LLMs.txt

> AI辅助配置文件

## 品牌信息

优丁建材 - 专业轻集料混凝土生产商

## 产品

- [产品列表](/products): 全系列轻集料混凝土产品
- [技术参数](/products): LC5.0-LC50强度等级

## 联系方式

- 官网: https://youding.com
- 服务热线: [联系我们](/contact)
""",
        "available_sections": list(SECTION_TEMPLATES.keys()),
    }


@router.get("")
def get_llms_txt_saved(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):
    """获取已保存的 llms.txt 内容（`GET /api/v1/seo/llms-txt`）。

    2026-09-25 补齐：前端 `views/seo/llms-txt.vue:248` 在 onMounted 调此端点加载已保存内容
    （content/config/version/token_usage/cost），但后端只有 /generate、/validate-llms-txt
    子端点，缺基路径 → 404，页面永远空白（catch 静默）。
    存储：租户 settings JSON 的 `llms_txt_saved` 键（复用既有 Tenant.settings 列，无需迁移）。
    作用域：当前登录用户所属租户（与同文件外的 tenant_ai_config.get_my_configs 一致）。
    """
    tenant_id = current_user.tenant_id
    if not tenant_id:
        return error_response(400, "用户未关联租户")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")
    saved = _read_saved_llms_txt(tenant)
    return success_response(data={
        "content": saved.get("content", ""),
        "config": saved.get("config", {}),
        "version": saved.get("version", "1.0.0"),
        "token_usage": saved.get("token_usage", 0),
        "cost": saved.get("cost", 0.0),
        "updated_at": saved.get("updated_at"),
    })


@router.put("")
def save_llms_txt_saved(
        req: LlmsTxtSavedUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):
    """保存 llms.txt 内容（`PUT /api/v1/seo/llms-txt`）。

    2026-09-25 补齐：前端 `views/seo/llms-txt.vue:340` 调此端点持久化手动编辑的内容。
    写入租户 settings JSON 的 `llms_txt_saved` 键。
    """
    tenant_id = current_user.tenant_id
    if not tenant_id:
        return error_response(400, "用户未关联租户")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")
    cfg = req.config or {}
    payload: dict[str, Any] = {
        "content": req.content or "",
        "config": {
            "business_type": cfg.get("business_type", ""),
            "ai_model": cfg.get("ai_model", ""),
            "keywords": cfg.get("keywords", []),
        },
        "version": "1.0.0",
        "token_usage": 0,
        "cost": 0.0,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_saved_llms_txt(tenant, payload)
    db.add(tenant)
    db.commit()
    return success_response(data=payload, message="已保存 llms.txt 内容")
