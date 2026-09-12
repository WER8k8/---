"""中文片出海 Worker：听写 / 出海（Celery 或后台线程调用）。"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.media_factory import MediaRenderTask
from app.models.tenant import Tenant
from app.models.user import User
from app.services.cross_border.cross_border_job_service import (
    _parse_job_payload,
    append_job_event,
    save_job_result,
    set_job_progress,
)
from app.services.cross_border.whisper_model_pool import warm_whisper_model
from app.services.cross_border.premium_video_dub_service import run_premium_overseas_job
from app.services.cross_border.video_dub_service import (
    run_video_dub_job,
    transcribe_video_task,
)
from app.services.media_factory_service import get_render_task

logger = logging.getLogger(__name__)


def _job_progress_reporter(job_id: str):
    """跨会话上报进度（Worker 线程安全）。"""
    from app.core.database import SessionLocal
    def report(progress: int, hint: str) -> None:
        """实现 报告 的功能。
        
        :param progress: 参数 progress（类型: int）
        :param hint: 参数 hint（类型: str）
        :return: 返回 None 结果
        """
        db = SessionLocal()
        try:
            task = get_render_task(db, job_id)
            if not task:
                return
            set_job_progress(db, task, progress, status="rendering", hint=hint)
        finally:
            db.close()

    return report


def _safe_asyncio_run(coro):
    """实现 safeasyncio执行 的功能。
    
    :param coro: 参数 coro 的说明
    :return: 返回处理结果
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def _load_job_context(db: Session, job_id: str) -> tuple[MediaRenderTask, Tenant, User, dict[str, Any]] | None:
    """实现 加载任务context 的功能。
    
    :param db: 参数 db（类型: Session）
    :param job_id: 参数 job_id（类型: str）
    :return: 返回 tuple[MediaRenderTask, Tenant, User, dict[str, Any]] | None 结果
    """
    task = get_render_task(db, job_id)
    if not task:
        return None
    payload = _parse_job_payload(task)
    tenant = db.query(Tenant).filter(Tenant.id == task.tenant_id).first()
    user = None
    user_id = payload.get("user_id")
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
    if not tenant or not user:
        return None
    return task, tenant, user, payload


def _run_cross_border_job_extracted(payload, task):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param payload, task: 输入参数
    :return: 返回 kind 等计算结果
    """
    kind = payload.get("kind") or "transcribe"
    set_job_progress(db, task, 5, status="rendering", hint="任务开始…")
    warm_whisper_model()
    return kind

def _run_cross_border_job_extracted1():
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param self: 输入参数
    :return: 返回 ctx 等计算结果
    """
    """实现 执行crossborder任务 的功能。

    :param db: 参数 db（类型: Session）
    :param job_id: 参数 job_id（类型: str）
    :return: 返回 dict[str, Any] 结果
    """
    ctx = _load_job_context(db, job_id)
    return ctx

def _run_cross_border_job_extracted2(_run_cross_border_job_extracted1):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted1()
    return ctx

def _run_cross_border_job_extracted3(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted2: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted2(_run_cross_border_job_extracted1)
    return ctx

def _run_cross_border_job_extracted4(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted3(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2)
    return ctx

def _run_cross_border_job_extracted5(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted4(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3)
    return ctx

def _run_cross_border_job_extracted6(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted5(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4)
    return ctx

def _run_cross_border_job_extracted7(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted6(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5)
    return ctx

def _run_cross_border_job_extracted8(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted7(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6)
    return ctx

def _run_cross_border_job_extracted9(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted8(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7)
    return ctx

def _run_cross_border_job_extracted10(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted9(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8)
    return ctx

def _run_cross_border_job_extracted11(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted10(_run_cross_border_job_extracted1, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9)
    return ctx

def _run_cross_border_job_extracted12(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted11(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9)
    return ctx

def _run_cross_border_job_extracted13(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted12(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9)
    return ctx

def _run_cross_border_job_extracted14(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted13(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9)
    return ctx

def _run_cross_border_job_extracted15(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted14, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted14, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted14(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9)
    return ctx

def _run_cross_border_job_extracted16(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted14, _run_cross_border_job_extracted15, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted14, _run_cross_border_job_extracted15, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted15(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted14, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9)
    return ctx

def _run_cross_border_job_extracted17(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted14, _run_cross_border_job_extracted15, _run_cross_border_job_extracted16, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted14, _run_cross_border_job_extracted15, _run_cross_border_job_extracted16, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted16(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted14, _run_cross_border_job_extracted15, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9)
    return ctx

def _run_cross_border_job_extracted18(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted14, _run_cross_border_job_extracted15, _run_cross_border_job_extracted16, _run_cross_border_job_extracted17, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted14, _run_cross_border_job_extracted15, _run_cross_border_job_extracted16, _run_cross_border_job_extracted17, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted17(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted14, _run_cross_border_job_extracted15, _run_cross_border_job_extracted16, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9)
    return ctx

def _run_cross_border_job_extracted19(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted14, _run_cross_border_job_extracted15, _run_cross_border_job_extracted16, _run_cross_border_job_extracted17, _run_cross_border_job_extracted18, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted14, _run_cross_border_job_extracted15, _run_cross_border_job_extracted16, _run_cross_border_job_extracted17, _run_cross_border_job_extracted18, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9: 输入参数
    :return: 返回 ctx 等计算结果
    """
    ctx = _run_cross_border_job_extracted18(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted14, _run_cross_border_job_extracted15, _run_cross_border_job_extracted16, _run_cross_border_job_extracted17, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9)
    return ctx

def _run_and_persist_job_result(db, task, coro, progress_hint, fail_error) -> dict[str, Any]:
    """执行跨境任务协程并保存结果（成功/失败统一处理）。"""
    result = _safe_asyncio_run(coro)
    if progress_hint:
        set_job_progress(db, task, 95, status="rendering", hint=progress_hint)
    else:
        set_job_progress(db, task, 95, status="rendering")
    if result.get("ok"):
        save_job_result(db, task, result, success=True)
    else:
        save_job_result(
            db,
            task,
            result,
            success=False,
            error_message=result.get("hint") or result.get("error") or fail_error,
        )
    return result


def run_cross_border_job(db: Session, job_id: str) -> dict[str, Any]:
    """run_cross_border_job。

    参数说明：
    :param db: 参数 db
    :param job_id: 参数 job_id
    :return: 返回处理结果。
    """
    ctx = _run_cross_border_job_extracted19(_run_cross_border_job_extracted1, _run_cross_border_job_extracted10, _run_cross_border_job_extracted11, _run_cross_border_job_extracted12, _run_cross_border_job_extracted13, _run_cross_border_job_extracted14, _run_cross_border_job_extracted15, _run_cross_border_job_extracted16, _run_cross_border_job_extracted17, _run_cross_border_job_extracted18, _run_cross_border_job_extracted2, _run_cross_border_job_extracted3, _run_cross_border_job_extracted4, _run_cross_border_job_extracted5, _run_cross_border_job_extracted6, _run_cross_border_job_extracted7, _run_cross_border_job_extracted8, _run_cross_border_job_extracted9)
    if not ctx:
        logger.error("cross_border job context missing: %s", job_id)
        return {"ok": False, "error": "job_not_found"}

    task, tenant, user, payload = ctx
    if task.status in ("done", "failed"):
        cfg_result = {}
        try:
            from app.services.media_video_edit_service import load_edit_config
            cfg_result = load_edit_config(task).get("cross_border_result") or {}
        except Exception:
            pass
        return {"ok": task.status == "done", **cfg_result}

    kind = _run_cross_border_job_extracted(payload, task)
    try:
        if kind == "transcribe":
            return _run_and_persist_job_result(
                db,
                task,
                transcribe_video_task(
                    db,
                    tenant,
                    user,
                    media_task_id=str(payload.get("media_task_id") or ""),
                    on_progress=_job_progress_reporter(job_id),
                ),
                "保存结果…",
                "听写失败",
            )

        if kind == "premium":
            return _run_and_persist_job_result(
                db,
                task,
                run_premium_overseas_job(
                    db,
                    tenant,
                    user,
                    media_task_id=str(payload.get("media_task_id") or ""),
                    track=str(payload.get("track") or "opensource_premium"),
                    localization_provider=payload.get("localization_provider"),
                    transcript_zh=payload.get("transcript_zh"),
                    voice_consent=bool(payload.get("voice_consent")),
                    output_mode=str(payload.get("output_mode") or "dub"),
                    dub_voice_gender=str(payload.get("dub_voice_gender") or "auto"),
                    on_progress=_job_progress_reporter(job_id),
                ),
                "保存精品结果…",
                "精品出海失败",
            )

        return _run_and_persist_job_result(
            db,
            task,
            run_video_dub_job(
                db,
                tenant,
                user,
                media_task_id=str(payload.get("media_task_id") or ""),
                transcript_zh=payload.get("transcript_zh"),
                voice_consent=bool(payload.get("voice_consent")),
                output_mode=str(payload.get("output_mode") or "subtitle"),
                auto_asr=bool(payload.get("auto_asr")),
                tts_voice=payload.get("tts_voice"),
                dub_voice_gender=str(payload.get("dub_voice_gender") or "auto"),
                on_progress=_job_progress_reporter(job_id),
            ),
            None,
            "出海版生成失败",
        )
    except Exception as exc:
        logger.exception("cross_border job %s failed", job_id)
        err = {"ok": False, "error": str(exc), "hint": "任务执行异常，请重试"}
        save_job_result(db, task, err, success=False, error_message=str(exc))
        return err
