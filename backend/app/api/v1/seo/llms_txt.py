from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.seo import LlmsConfig

router = APIRouter()

SECTION_TEMPLATES = {
    "brand": "## {title}\n\n{content}\n\n",
    "product": "- [{title}]({url}): {description}\n",
    "faq": "- {question}: {answer}\n",
    "contact": "## {title}\n\n{content}\n\n",
}

class GenerateRequest(BaseModel):
    sections: list[dict] = []
    include_ai_instructions: bool = True

class ValidateRequest(BaseModel):
    content: str

@router.post("/generate-llms-txt")
def generate_llms_txt(req: GenerateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lines = []
    lines.append("# LLMs.txt\n")
    lines.append("> 此文件帮助AI大模型了解优丁建材官网内容\n")

    db_configs = db.query(LlmsConfig).filter(LlmsConfig.is_active == True).order_by(LlmsConfig.section).all()
    existing_sections = {c.section for c in db_configs}

    if req.sections:
        for section in req.sections:
            stype = section.get("type", "brand")
            template = SECTION_TEMPLATES.get(stype, "## {title}\n\n{content}\n\n")
            lines.append(template.format(**section))

    if db_configs:
        for config in db_configs:
            if config.section in existing_sections:
                lines.append(f"\n## {config.section}\n\n{config.content}\n")

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
    return {"content": result, "line_count": len(lines), "size_bytes": len(result.encode("utf-8"))}

@router.post("/validate-llms-txt")
def validate_llms_txt(req: ValidateRequest, current_user: User = Depends(get_current_user)):
    issues = []
    content = req.content

    if not content.startswith("# LLMs.txt"):
        issues.append({"severity": "error", "message": "文件必须以# LLMs.txt开头"})

    section_count = content.count("## ")
    if section_count < 2:
        issues.append({"severity": "warning", "message": f"sections数量过少({section_count}个)"})

    if len(content) < 200:
        issues.append({"severity": "warning", "message": "内容过短，建议至少200字符"})

    if "优丁" not in content and "youding" not in content.lower():
        issues.append({"severity": "warning", "message": "未包含品牌名称(优丁/Youding)"})

    if "kg/m³" not in content and "kg/m3" not in content:
        issues.append({"severity": "info", "message": "未包含密度参数(kg/m³)"})

    return {"is_valid": len([i for i in issues if i["severity"] == "error"]) == 0, "issues": issues, "section_count": section_count}

@router.get("/llms-txt-template")
def get_llms_txt_template():
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
