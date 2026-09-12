"""MOSS-VL AI 剪辑、一键分发、热更新/回滚及官方整仓管理路由。"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.moss_auto_clip_pipeline import MossAutoClipPipeline
from app.services.moss_clip_and_publish_workflow import MossClipAndPublishWorkflow
from app.services.moss_vl.hot_reload_manager import MossHotReloadManager
from app.services.moss_vl.repo_syncer import MossRepoSyncer
from app.services.moss_vl_service import MossVLService

router = APIRouter(prefix="/moss-vl", tags=["MOSS-VL 智能剪辑与官方全仓管理"])

ROUTE_PREFIX = "/moss-vl"
ROUTE_TAGS = ["MOSS-VL 智能剪辑与官方全仓管理"]


class MossAnalyzeRequest(BaseModel):
    video_source: str = Field(..., description="视频本地绝对路径或远程URL")
    duration_sec: float | None = Field(default=None, description="视频总时长，若未知由系统自探测")
    prompt: str | None = Field(default="", description="剪辑偏好，例如'重点保留人物操作特写'")


class MossAutoClipRequest(BaseModel):
    video_source: str
    duration_sec: float | None = None
    target_aspect_ratio: str = Field(default="9:16", description="输出画幅比例，短视频推荐 9:16")
    min_clip_duration: float = Field(default=15.0, description="切片最短秒数")
    max_clip_duration: float = Field(default=60.0, description="切片最长秒数")
    target_platforms: list[str] = Field(default_factory=lambda: ["douyin", "xhs", "tiktok", "youtube"])


class MossClipAndPublishRequest(BaseModel):
    tenant_id: str = "default_tenant"
    video_source: str
    duration_sec: float | None = None
    target_platforms: list[str] = Field(default_factory=lambda: ["douyin", "xhs", "tiktok", "youtube"])
    auto_dispatch: bool = Field(default=True, description="是否在剪辑完成后直接提交发布队列")


class MossHotReloadRequest(BaseModel):
    commit_hash: str | None = Field(default=None, description="目标官方 commit 标识")
    release_tag: str | None = Field(default=None, description="目标 release tag，如 v1.2.0")
    quantization: str = Field(default="bfloat16", description="量化模式: bfloat16 / fp8 / nf4")


class MossRollbackRequest(BaseModel):
    target_version_id: str | None = Field(default=None, description="指定回滚版本 ID，留空则自动回退至上一稳定版")


@router.post("/analyze", summary="MOSS-VL 时空多模态视频解析")
def analyze_video(req: MossAnalyzeRequest) -> dict[str, Any]:
    service = MossVLService()
    result = service.analyze_video_spatiotemporal(
        video_path_or_url=req.video_source,
        duration_sec=req.duration_sec,
    )
    return {"code": 0, "msg": "视频时空解析完成", "data": result}


@router.post("/auto-clip", summary="MOSS-VL AI 智能高光剪辑切片")
def auto_clip(req: MossAutoClipRequest) -> dict[str, Any]:
    pipeline = MossAutoClipPipeline()
    result = pipeline.execute_auto_clip_pipeline(
        video_path_or_url=req.video_source,
        video_duration_sec=req.duration_sec,
        min_clip_duration=req.min_clip_duration,
        max_clip_duration=req.max_clip_duration,
        target_aspect_ratio=req.target_aspect_ratio,
        target_platforms=req.target_platforms,
    )
    return {"code": 0, "msg": "视频高光智能切片生成成功", "data": result}


@router.post("/clip-and-publish", summary="端到端：MOSS 智能剪辑 + 全平台一键矩阵分发")
def clip_and_publish(req: MossClipAndPublishRequest) -> dict[str, Any]:
    workflow = MossClipAndPublishWorkflow()
    result = workflow.run_clip_and_publish_workflow(
        video_path_or_url=req.video_source,
        target_platforms=req.target_platforms,
        tenant_id=req.tenant_id,
        video_duration_sec=req.duration_sec,
        auto_dispatch=req.auto_dispatch,
    )
    return {"code": 0, "msg": "智能剪辑与矩阵分发流水线已成功触发", "data": result}


# ================== MOSS-VL 热更新与回滚运维管理接口 ==================

@router.get("/version/status", summary="查询 MOSS-VL 当前运行版本与健康状态")
def get_version_status() -> dict[str, Any]:
    manager = MossHotReloadManager()
    return {"code": 0, "msg": "查询成功", "data": manager.get_runtime_status()}


@router.post("/version/check-upstream", summary="检查 OpenMOSS 官方仓库最新更新")
def check_upstream() -> dict[str, Any]:
    manager = MossHotReloadManager()
    return {"code": 0, "msg": "上游检查完成", "data": manager.check_upstream_updates()}


@router.post("/version/hot-reload", summary="执行零停机双缓冲热更新")
def hot_reload_model(req: MossHotReloadRequest) -> dict[str, Any]:
    manager = MossHotReloadManager()
    res = manager.hot_reload(
        new_commit_hash=req.commit_hash,
        new_release_tag=req.release_tag,
        quantization=req.quantization,
    )
    code = 0 if res.get("success") else 1
    return {"code": code, "msg": res.get("msg"), "data": res}


@router.post("/version/rollback", summary="一键秒级回滚至稳定版本")
def rollback_model(req: MossRollbackRequest) -> dict[str, Any]:
    manager = MossHotReloadManager()
    res = manager.rollback_to_version(target_version_id=req.target_version_id)
    code = 0 if res.get("success") else 1
    return {"code": code, "msg": res.get("msg"), "data": res}


@router.get("/version/history", summary="查询 MOSS-VL 历史快照清单")
def get_version_history() -> dict[str, Any]:
    manager = MossHotReloadManager()
    return {"code": 0, "msg": "查询成功", "data": manager.get_version_history()}


# ================== MOSS-VL 官方物理整仓状态与诊断接口 ==================

@router.get("/repo/status", summary="查询 MOSS-VL 官方开源整仓本地挂载与完整度状态")
def get_repo_status() -> dict[str, Any]:
    syncer = MossRepoSyncer()
    report = syncer.get_repo_inspection_report()
    return {"code": 0, "msg": "官方整仓状态就绪", "data": report}
