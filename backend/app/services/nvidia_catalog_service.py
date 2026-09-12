"""NVIDIA NIM 模型目录：按业务场景分类（推理 / 文章 / 视频等）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings

# Cosmos 等视频 NIM 走 /v1/infer，通常不在 /v1/models 聊天列表中
VIDEO_NIM_MODELS: list[dict[str, Any]] = [
    {
        "id": "nvidia/cosmos-predict1-5b",
        "name": "Cosmos Predict 1 5B",
        "endpoint": "/v1/infer",
        "input": "text",
        "description": "文生视频：根据文本描述生成物理世界感知的短视频帧序列",
        "catalog_url": "https://build.nvidia.com/nvidia/cosmos-predict1-5b",
    },
    {
        "id": "nvidia/cosmos-predict1-7b",
        "name": "Cosmos Predict 1 7B",
        "endpoint": "/v1/infer",
        "input": "text",
        "description": "文生视频（更大模型）：高质量文本到视频世界状态生成",
        "catalog_url": "https://build.nvidia.com/nvidia/cosmos-predict1-7b",
    },
    {
        "id": "nvidia/cosmos-predict1-7b-video2world",
        "name": "Cosmos Predict 1 7B Video2World",
        "endpoint": "/v1/infer",
        "input": "image",
        "description": "图生视频：上传图片 + 文本提示，预测后续视频帧（Image/Video to World）",
        "catalog_url": "https://build.nvidia.com/nvidia/cosmos-predict1-7b-video2world",
    },
    {
        "id": "nvidia/cosmos-transfer1-7b",
        "name": "Cosmos Transfer 1 7B",
        "endpoint": "/v1/infer",
        "input": "video",
        "description": "视频风格/环境转换：基于控制图与文本，将仿真或原始视频转为写实风格",
        "catalog_url": "https://build.nvidia.com/nvidia/cosmos-transfer1-7b",
    },
    {
        "id": "nvidia/cosmos-transfer2.5-2b",
        "name": "Cosmos Transfer 2.5 2B",
        "endpoint": "/v1/infer",
        "input": "video",
        "description": "视频转换 2.5：多控制输入，物理 AI 合成数据与场景迁移",
        "catalog_url": "https://build.nvidia.com/nvidia/cosmos-transfer2_5-2b",
    },
]

CATEGORY_META: list[dict[str, str]] = [
    {
        "id": "inference",
        "label": "AI 推理 / 对话",
        "description": "通用大模型对话、问答、摘要、结构化输出（/v1/chat/completions）",
    },
    {
        "id": "article",
        "label": "文章 / 长文生成",
        "description": "SEO 文章、营销文案、新闻稿、产品描述等长文本创作",
    },
    {
        "id": "code",
        "label": "代码生成",
        "description": "编程辅助、代码补全、代码审查",
    },
    {
        "id": "vision",
        "label": "图像理解（多模态）",
        "description": "读图问答、OCR、图表理解（输入图片 + 文本）",
    },
    {
        "id": "text_to_video",
        "label": "文生视频",
        "description": "纯文本提示生成视频（Cosmos Predict，/v1/infer）",
    },
    {
        "id": "image_to_video",
        "label": "图生视频",
        "description": "以图片为起点，结合文本生成后续视频画面",
    },
    {
        "id": "video_to_video",
        "label": "视频生视频 / 续帧",
        "description": "以短视频为条件，生成后续世界状态或延长镜头",
    },
    {
        "id": "video_transfer",
        "label": "视频风格转换",
        "description": "光照、环境、风格迁移（Cosmos Transfer）",
    },
    {
        "id": "article_to_video",
        "label": "文章 / 脚本生视频",
        "description": "先用 LLM 将文章转为分镜脚本，再调用 Cosmos Predict 生成视频（组合工作流）",
    },
    {
        "id": "video_understanding",
        "label": "视频理解",
        "description": "视频/图像内容理解、结构化推理、质检",
    },
    {
        "id": "embedding",
        "label": "向量嵌入 / RAG",
        "description": "语义检索、知识库向量化（非对话生成）",
    },
    {
        "id": "guardrail",
        "label": "安全护栏",
        "description": "内容安全、主题控制、PII 检测",
    },
]

ARTICLE_MODEL_HINTS = (
    "glm",
    "qwen",
    "deepseek-v4",
    "kimi",
    "mistral-large",
    "llama-3.3",
    "llama-3.1-70b",
    "nemotron",
    "palmyra-creative",
    "palmyra-fin",
    "yi-large",
    "step-3",
    "minimax",
    "seed-oss",
)

ARTICLE_TO_VIDEO_SCRIPT_MODELS = (
    "z-ai/glm-5.1",
    "qwen/qwen3.5-397b-a17b",
    "deepseek-ai/deepseek-v4-pro",
    "moonshotai/kimi-k2.6",
    "mistralai/mistral-large-3-675b-instruct-2512",
    "meta/llama-3.3-70b-instruct",
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "writer/palmyra-creative-122b",
)


@dataclass
class ModelEntry:
    id: str
    owned_by: str = ""
    endpoint: str = "/v1/chat/completions"
    input_modes: list[str] | None = None
    description: str = ""
    catalog_url: str = ""
    def to_dict(self) -> dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "id": self.id,
            "owned_by": self.owned_by,
            "endpoint": self.endpoint,
            "input_modes": self.input_modes or ["text"],
            "description": self.description,
            "catalog_url": self.catalog_url or f"https://build.nvidia.com/{self.id}",
        }


def _match_any(text: str, patterns: tuple[str, ...]) -> bool:
    """_match_any。

    参数说明：
    :param text: 参数 text
    :param patterns: 参数 patterns
    :return: 返回处理结果。
    """
    t = text.lower()
    return any(p in t for p in patterns)


def classify_chat_model(model_id: str) -> set[str]:
    """classify_chat_model。

    参数说明：
    :param model_id: 参数 model_id
    :return: 返回处理结果。
    """
    s = model_id.lower()
    cats: set[str] = set()
    if _match_any(s, ("embed", "rerank", "retriever", "bge", "arctic-embed", "e5", "nv-embed", "nvclip")):
        cats.add("embedding")
        return cats

    if _match_any(s, ("guard", "safety", "topic-control", "content-safety", "gliner-pii", "nemotron-3-content")):
        cats.add("guardrail")
        return cats

    if _match_any(s, ("cosmos-reason", "video-detector", "synthetic-video-detector")):
        cats.add("video_understanding")
        return cats

    if _match_any(s, ("vision", "-vl", "vl-", "vila", "neva", "fuyu", "paligemma", "phi-3-vision", "kosmos", "multimodal", "deplot")):
        cats.add("vision")
        return cats

    if _match_any(s, ("coder", "codegemma", "starcoder", "codestral", "qwen3-coder", "granite-34b-code", "granite-8b-code", "codellama")):
        cats.add("code")
        cats.add("inference")
        return cats

    cats.add("inference")
    if _match_any(s, ARTICLE_MODEL_HINTS) or "instruct" in s or "creative" in s:
        cats.add("article")

    if _match_any(s, ("reason", "nemotron-ultra", "nemotron-super", "deepseek-v4-pro")):
        cats.add("article")

    return cats


def fetch_live_model_ids(api_key: str | None = None) -> list[dict[str, Any]]:
    """fetch_live_model_ids。

    参数说明：
    :param api_key: 参数 api_key
    :return: 返回处理结果。
    """
    key = (api_key or settings.AI_NVIDIA_API_KEY or "").strip()
    if not key:
        return []
    base = (settings.AI_NVIDIA_BASE_URL or "https://integrate.api.nvidia.com/v1").rstrip("/")
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(f"{base}/models", headers={"Authorization": f"Bearer {key}"})
        resp.raise_for_status()
        payload = resp.json()
    rows = payload.get("data", payload if isinstance(payload, list) else [])
    return rows if isinstance(rows, list) else []


def build_nvidia_catalog(api_key: str | None = None) -> dict[str, Any]:
    """build_nvidia_catalog。

    参数说明：
    :param api_key: 参数 api_key
    :return: 返回处理结果。
    """
    live_rows = fetch_live_model_ids(api_key)
    by_category: dict[str, list[dict[str, Any]]] = {c["id"]: [] for c in CATEGORY_META}
    seen: dict[str, dict[str, Any]] = {}
    for row in live_rows:
        model_id = str(row.get("id", "")).strip()
        if not model_id:
            continue
        owned_by = str(row.get("owned_by", model_id.split("/")[0] if "/" in model_id else ""))
        entry = ModelEntry(
            id=model_id,
            owned_by=owned_by,
            endpoint="/v1/chat/completions",
            input_modes=["text"] if "vision" not in model_id.lower() and "-vl" not in model_id.lower() else ["text", "image"],
        )
        seen[model_id] = entry.to_dict()
        for cat in classify_chat_model(model_id):
            by_category.setdefault(cat, []).append(entry.to_dict())

    for vm in VIDEO_NIM_MODELS:
        entry = {
            "id": vm["id"],
            "owned_by": "nvidia",
            "endpoint": vm["endpoint"],
            "input_modes": [vm["input"]] if vm["input"] != "video" else ["video", "text"],
            "description": vm["description"],
            "catalog_url": vm["catalog_url"],
        }
        seen[vm["id"]] = entry
        if vm["input"] == "text":
            by_category["text_to_video"].append(entry)
        elif vm["input"] == "image":
            by_category["image_to_video"].append(entry)
            if "video2world" in vm["id"]:
                by_category["video_to_video"].append({**entry, "description": entry["description"] + "（亦支持短视频续帧）"})
        elif "transfer" in vm["id"]:
            by_category["video_transfer"].append(entry)
        else:
            by_category["video_to_video"].append(entry)

    article_to_video_entries: list[dict[str, Any]] = []
    for script_model in ARTICLE_TO_VIDEO_SCRIPT_MODELS:
        if script_model in seen:
            article_to_video_entries.append(
                {
                    **seen[script_model],
                    "role": "script",
                    "description": "将文章/大纲转为分镜脚本与镜头描述",
                }
            )
    for vm in VIDEO_NIM_MODELS:
        if vm["input"] in ("text", "image"):
            article_to_video_entries.append(
                {
                    **seen[vm["id"]],
                    "role": "video",
                    "description": f"分镜脚本 → 视频：{vm['description']}",
                }
            )
    by_category["article_to_video"] = article_to_video_entries
    for cat_id in by_category:
        by_category[cat_id] = sorted(by_category[cat_id], key=lambda x: x["id"])

    categories = []
    for meta in CATEGORY_META:
        models = by_category.get(meta["id"], [])
        categories.append({**meta, "count": len(models), "models": models})

    return {
        "provider": "nvidia",
        "base_url": settings.AI_NVIDIA_BASE_URL,
        "total_models": len(seen),
        "live_chat_models": len(live_rows),
        "note": "nvapi Key 永久有效；免费额度与模型上下架以 build.nvidia.com 为准。视频类模型使用 /v1/infer，其余对话类使用 /v1/chat/completions。",
        "categories": categories,
        "defaults": {
            "inference": "meta/llama-3.1-8b-instruct",
            "article": "z-ai/glm-5.1",
            "code": "deepseek-ai/deepseek-coder-6.7b-instruct",
            "vision": "meta/llama-3.2-11b-vision-instruct",
            "text_to_video": "nvidia/cosmos-predict1-5b",
            "image_to_video": "nvidia/cosmos-predict1-7b-video2world",
            "video_transfer": "nvidia/cosmos-transfer2.5-2b",
            "article_to_video_script": "z-ai/glm-5.1",
            "article_to_video_render": "nvidia/cosmos-predict1-5b",
        },
    }
