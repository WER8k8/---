from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, optional_auth
from app.models.seo import LlmsConfig
from app.models.user import User

router = APIRouter()

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
