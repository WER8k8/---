"""
获客搜索异步任务 —— 后台执行 + 进度推送

实现方式（渐进式）：
- Phase 1: asyncio 后台任务 + 内存状态存储（当前）
- Phase 2: Celery + Redis（生产环境升级）

进度推送方式：
- 方式 A: WebSocket（实时，推荐）
- 方式 B: SSE Server-Sent Events（HTTP 长连接，备选）
- 方式 C: 轮询（当前兜底）
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.database import get_db

logger = logging.getLogger(__name__)


# ── 任务状态 ──

class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class LeadSearchTask:
    """获客搜索任务"""
    task_id: str
    user_id: str
    status: str = TaskStatus.PENDING
    progress: int = 0  # 0-100
    current_step: str = ""
    leads_found: int = 0
    emails_found: int = 0
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=lambda: time.time())
    updated_at: float = field(default_factory=lambda: time.time())


# ── 内存任务存储（Phase 1：开发环境）──
# TODO [P2] 迁移到 Redis（Celery + Redis 任务队列，待 Phase 2 生产部署时实施）
_task_store: dict[str, LeadSearchTask] = {}


def create_task(user_id: str) -> LeadSearchTask:
    """创建新任务。"""
    import secrets
    task_id = secrets.token_urlsafe(16)
    task = LeadSearchTask(task_id=task_id, user_id=user_id)
    _task_store[task_id] = task
    return task


def get_task(task_id: str) -> Optional[LeadSearchTask]:
    """获取任务状态。"""
    return _task_store.get(task_id)


def update_task(
    task_id: str,
    *,
    status: Optional[str] = None,
    progress: Optional[int] = None,
    current_step: Optional[str] = None,
    leads_found: Optional[int] = None,
    emails_found: Optional[int] = None,
    result: Optional[dict] = None,
    error: Optional[str] = None,
) -> None:
    """更新任务状态。"""
    task = _task_store.get(task_id)
    if not task:
        return
    if status is not None:
        task.status = status
    if progress is not None:
        task.progress = progress
    if current_step is not None:
        task.current_step = current_step
    if leads_found is not None:
        task.leads_found = leads_found
    if emails_found is not None:
        task.emails_found = emails_found
    if result is not None:
        task.result = result
    if error is not None:
        task.error = error
    task.updated_at = time.time()


def cleanup_old_tasks(max_age_seconds: float = 3600) -> int:
    """清理超过 max_age_seconds 的旧任务。"""
    now = time.time()
    to_remove = [
        tid for tid, t in _task_store.items()
        if now - t.created_at > max_age_seconds
    ]
    for tid in to_remove:
        del _task_store[tid]
    return len(to_remove)


# ── 异步搜索执行 ──

async def execute_lead_search(
    task_id: str,
    keywords: str,
    country: Optional[str] = None,
    industry: Optional[str] = None,
    max_results: int = 10,
    verify_emails: bool = True,
    min_confidence: float = 0.3,
) -> None:
    """在后台执行获客搜索，更新任务进度。

    这是 asyncio 版本，不阻塞主线程。
    """
    from app.api.v1.routes.lead_generation import _google_cse_search, _process_lead
    update_task(task_id, status=TaskStatus.RUNNING, current_step="正在搜索 Google...", progress=10)
    try:
        # Step 1: Google CSE 搜索
        search_results = await _google_cse_search(keywords, num=max_results)
        total_sites = len(search_results)
        if not search_results:
            update_task(
                task_id,
                status=TaskStatus.COMPLETED,
                progress=100,
                current_step="搜索完成（无结果）",
                result={"leads": [], "total_found": 0, "emails_found": 0},
            )
            return

        update_task(task_id, current_step=f"找到 {total_sites} 个网站，开始抓取邮箱...", progress=30)
        # Step 2: 逐个处理（带进度更新）
        leads = []
        for idx, item in enumerate(search_results[:max_results]):
            progress = 30 + int((idx / total_sites) * 60)
            update_task(
                task_id,
                progress=progress,
                current_step=f"正在分析 {item.get('displayLink', item.get('link', ''))}... ({idx + 1}/{total_sites})",
            )
            lead = await _process_lead(
                url=item["link"],
                snippet=item.get("snippet", ""),
                title=item.get("title", ""),
                verify_emails=verify_emails,
                min_confidence=min_confidence,
            )
            leads.append(lead)
            # 小延迟避免进度更新太频繁
            await asyncio.sleep(0.1)

        # Step 3: 汇总结果
        leads_with_emails = [l for l in leads if l.emails]
        total_emails = sum(len(l.emails) for l in leads)
        verified_count = sum(1 for l in leads for e in l.emails if getattr(e, 'verified', None) is True)
        result = {
            "leads": [
                {
                    "company_name": l.company_name,
                    "domain": l.domain,
                    "website": l.website,
                    "snippet": l.snippet,
                    "emails": [
                        {
                            "email": e.email,
                            "confidence": e.confidence,
                            "verified": getattr(e, 'verified', None),
                            "verification_status": getattr(e, 'verification_status', None),
                            "source_page": getattr(e, 'source_page', None),
                        }
                        for e in l.emails
                    ],
                    "source": l.source,
                }
                for l in leads
            ],
            "total_found": len(leads),
            "emails_found": total_emails,
            "verified_emails": verified_count,
            "search_time_ms": int((time.time() - _task_store[task_id].created_at) * 1000),
            "method": "free_pipeline_async",
        }
        update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            current_step="搜索完成",
            leads_found=len(leads_with_emails),
            emails_found=total_emails,
            result=result,
        )

    except Exception as e:
        logger.error(f"异步搜索失败 {task_id}: {e}")
        update_task(
            task_id,
            status=TaskStatus.FAILED,
            progress=100,
            current_step="搜索失败",
            error=str(e),
        )
