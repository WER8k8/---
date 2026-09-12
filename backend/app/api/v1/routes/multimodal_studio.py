"""多模态营销工厂路由。"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.ai_multimodal_studio import AIMultimodalStudio

router = APIRouter(prefix="/multimodal/marketing", tags=["Multimodal Marketing"])

ROUTE_PREFIX = "/multimodal/marketing"
ROUTE_TAGS = ["Multimodal Marketing"]


class ImagePromptRequest(BaseModel):
    product_name: str
    scene: str = "studio"


class SocialPostRequest(BaseModel):
    product_name: str
    platform: str = "linkedin"


@router.post("/image-prompt", summary="生成电商产品图/场景图生图提示词")
def generate_image_prompt(req: ImagePromptRequest) -> dict[str, Any]:
    studio = AIMultimodalStudio()
    return {"code": 0, "msg": "ok", "data": studio.generate_image_prompts(req.product_name, req.scene)}


@router.post("/social-post", summary="生成海外社媒宣发推文文案")
def generate_social_post(req: SocialPostRequest) -> dict[str, Any]:
    studio = AIMultimodalStudio()
    return {"code": 0, "msg": "ok", "data": studio.generate_social_post(req.product_name, req.platform)}
