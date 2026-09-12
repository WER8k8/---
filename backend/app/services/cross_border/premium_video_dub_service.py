"""精品出海轨编排 — 开源 sidecar / Vozo / 回退禁止假成功。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.user import User
from app.services.cross_border.opensource_localization_registry import (
    pick_active_opensource_provider,
)
from app.services.cross_border.opensource_localization_service import run_opensource_premium_job
from app.services.cross_border.vozo_localization_service import (
    is_vozo_configured,
    run_vozo_premium_job,
)
from app.services.cross_border.video_dub_service import run_video_dub_job
from app.services.media_factory_service import get_render_task_for_user
from app.services.media_video_edit_service import load_edit_config, save_edit_config

ProgressFn = Callable[[int, str], None] | None

TrackId = str  # standard | opensource_premium | vozo


def _run_premium_overseas_job_extracted(result, task, track_norm):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param result, task, track_norm: 输入参数
    :return: 无返回（仅副作用）
    """
    cfg = load_edit_config(task)
    cfg["cross_border_premium"] = {
        **result,
        "track": track_norm,
        "media_task_id": str(task.id),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    save_edit_config(db, task, cfg)
    result["media_task_id"] = str(task.id)
    result["track"] = track_norm

def _run_premium_overseas_job_extracted1():
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param self: 输入参数
    :return: 返回 task 等计算结果
    """
    """精品轨：仅在上游真实成功时 ok=true；禁止静默回退标准轨冒充精品。"""
    task = get_render_task_for_user(db, media_task_id, user)
    return task

def _run_premium_overseas_job_extracted2(_run_premium_overseas_job_extracted1):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted1()
    return task

def _run_premium_overseas_job_extracted3(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted2(_run_premium_overseas_job_extracted1)
    return task

def _run_premium_overseas_job_extracted4(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted3(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2)
    return task

def _run_premium_overseas_job_extracted5(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted4(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3)
    return task

def _run_premium_overseas_job_extracted6(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted5(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4)
    return task

def _run_premium_overseas_job_extracted7(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted6(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5)
    return task

def _run_premium_overseas_job_extracted8(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted7(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6)
    return task

def _run_premium_overseas_job_extracted9(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted8(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7)
    return task

def _run_premium_overseas_job_extracted10(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted9(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8)
    return task

def _run_premium_overseas_job_extracted11(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted10(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9)
    return task

def _run_premium_overseas_job_extracted12(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted11(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9)
    return task

def _run_premium_overseas_job_extracted13(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted12(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9)
    return task

def _run_premium_overseas_job_extracted14(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted13(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9)
    return task

def _run_premium_overseas_job_extracted15(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted14, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted14, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted14(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9)
    return task

def _run_premium_overseas_job_extracted16(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted14, _run_premium_overseas_job_extracted15, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted14, _run_premium_overseas_job_extracted15, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted15(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted14, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9)
    return task

def _run_premium_overseas_job_extracted17(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted14, _run_premium_overseas_job_extracted15, _run_premium_overseas_job_extracted16, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted14, _run_premium_overseas_job_extracted15, _run_premium_overseas_job_extracted16, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted16(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted14, _run_premium_overseas_job_extracted15, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9)
    return task

def _run_premium_overseas_job_extracted18(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted14, _run_premium_overseas_job_extracted15, _run_premium_overseas_job_extracted16, _run_premium_overseas_job_extracted17, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted14, _run_premium_overseas_job_extracted15, _run_premium_overseas_job_extracted16, _run_premium_overseas_job_extracted17, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted17(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted14, _run_premium_overseas_job_extracted15, _run_premium_overseas_job_extracted16, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9)
    return task

def _run_premium_overseas_job_extracted19(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted14, _run_premium_overseas_job_extracted15, _run_premium_overseas_job_extracted16, _run_premium_overseas_job_extracted17, _run_premium_overseas_job_extracted18, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted14, _run_premium_overseas_job_extracted15, _run_premium_overseas_job_extracted16, _run_premium_overseas_job_extracted17, _run_premium_overseas_job_extracted18, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_premium_overseas_job_extracted18(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted14, _run_premium_overseas_job_extracted15, _run_premium_overseas_job_extracted16, _run_premium_overseas_job_extracted17, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9)
    return task

async def _run_premium_opensource_track(
    db, tenant, user, media_task_id, transcript_zh, voice_consent,
    output_mode, dub_voice_gender, localization_provider, track_norm, task, on_progress,
) -> dict[str, Any]:
    """开源精品轨：选择可用 provider 并执行配音/字幕生成。"""
    active = pick_active_opensource_provider(localization_provider)
    if not active:
        return {
            "ok": False,
            "error_code": "OPENSOURCE_NOT_CONFIGURED",
            "hint": (
                "无可用的真实本地化上游。请配置听写+ffmpeg+edge-tts，"
                "或部署通过健康探测的 Linly/YouDub sidecar。"
            ),
        }
    if active["id"] == "youding_self_hosted":
        result = await run_video_dub_job(
            db,
            tenant,
            user,
            media_task_id=media_task_id,
            transcript_zh=transcript_zh,
            voice_consent=voice_consent,
            output_mode=output_mode,
            auto_asr=not (transcript_zh or "").strip(),
            dub_voice_gender=dub_voice_gender,
            on_progress=on_progress,
        )
        if result.get("ok"):
            result["localization_provider"] = "youding_self_hosted"
            result["localization_mode"] = "self_hosted_real"
            result["lip_sync"] = False
            result["track"] = track_norm
            result.setdefault(
                "hint",
                "已通过内置真实链生成英文配音/字幕（无口型克隆），发送前请人工听看核对。",
            )
        return result
    else:
        return await run_opensource_premium_job(
            result_url=task.result_url,
            provider_id=localization_provider or active["id"],
            on_progress=on_progress,
        )


async def run_premium_overseas_job(
    db: Session,
    tenant: Tenant,
    user: User,
    *,
    media_task_id: str,
    track: TrackId = "opensource_premium",
    localization_provider: str | None = None,
    transcript_zh: str | None = None,
    voice_consent: bool = False,
    output_mode: str = "dub",
    dub_voice_gender: str = "auto",
    on_progress: ProgressFn = None,
) -> dict[str, Any]:
    """run_premium_overseas_job。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param user: 参数 user
    :param media_task_id: 参数 media_task_id
    :param track: 参数 track
    :param localization_provider: 参数 localization_provider
    :param transcript_zh: 参数 transcript_zh
    :param voice_consent: 参数 voice_consent
    :param output_mode: 参数 output_mode
    :param dub_voice_gender: 参数 dub_voice_gender
    :param on_progress: 参数 on_progress
    :return: 返回处理结果。
    """
    task = _run_premium_overseas_job_extracted19(_run_premium_overseas_job_extracted1, _run_premium_overseas_job_extracted10, _run_premium_overseas_job_extracted11, _run_premium_overseas_job_extracted12, _run_premium_overseas_job_extracted13, _run_premium_overseas_job_extracted14, _run_premium_overseas_job_extracted15, _run_premium_overseas_job_extracted16, _run_premium_overseas_job_extracted17, _run_premium_overseas_job_extracted18, _run_premium_overseas_job_extracted2, _run_premium_overseas_job_extracted3, _run_premium_overseas_job_extracted4, _run_premium_overseas_job_extracted5, _run_premium_overseas_job_extracted6, _run_premium_overseas_job_extracted7, _run_premium_overseas_job_extracted8, _run_premium_overseas_job_extracted9)
    if not task or str(task.tenant_id or "") != str(tenant.id):
        return {"ok": False, "error": "找不到该视频，请先上传中文产品片"}

    if output_mode == "dub" and not voice_consent:
        return {
            "ok": False,
            "error": "未勾选配音确认",
            "hint": "精品出海生成配音前请勾选确认框",
        }

    track_norm = (track or "opensource_premium").strip().lower()
    if track_norm == "vozo":
        if not is_vozo_configured():
            return {
                "ok": False,
                "error_code": "VOZO_NOT_CONFIGURED",
                "hint": "Vozo 商业精品轨未配置 VOZO_API_KEY",
            }
        result = await run_vozo_premium_job(
            result_url=task.result_url,
            on_progress=on_progress,
        )
    elif track_norm in ("opensource_premium", "opensource", "premium"):
        result = await _run_premium_opensource_track(
            db, tenant, user, media_task_id, transcript_zh, voice_consent,
            output_mode, dub_voice_gender, localization_provider, track_norm, task, on_progress,
        )
    elif track_norm == "standard":
        return await run_video_dub_job(
            db,
            tenant,
            user,
            media_task_id=media_task_id,
            transcript_zh=transcript_zh,
            voice_consent=voice_consent,
            output_mode=output_mode,
            auto_asr=not (transcript_zh or "").strip(),
            dub_voice_gender=dub_voice_gender,
            on_progress=on_progress,
        )
    else:
        return {
            "ok": False,
            "error_code": "UNKNOWN_TRACK",
            "hint": f"未知 track: {track}",
        }

    if not result.get("ok"):
        result.setdefault("media_task_id", str(task.id))
        result.setdefault("track", track_norm)
        return result

    _run_premium_overseas_job_extracted(result, task, track_norm)
    return result
