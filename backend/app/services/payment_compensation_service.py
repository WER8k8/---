# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""支付权益发放补偿任务巡检服务

BUG-02 修复配套：定时巡检 payment_compensation_tasks 表，
对 pending/failed 任务重试权益发放，直到成功或达到最大重试次数。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.payment import PaymentCompensationTask, PaymentOrder
from app.services.provisioning_service import ProvisioningService

logger = logging.getLogger("uj-admin.payment_compensation")


class CompensationReprocessService:
    """补偿任务巡检服务。"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    def reprocess_pending_tasks(self, limit: int = 50) -> dict:
        """处理待补偿任务，返回统计信息。"""
        # 查询 pending/failed 且未达到最大重试次数的任务
        tasks = (
            self.db.query(PaymentCompensationTask)
            .filter(
                PaymentCompensationTask.status.in_(["pending", "failed"]),
                PaymentCompensationTask.attempts < PaymentCompensationTask.max_attempts,
            )
            .order_by(PaymentCompensationTask.scheduled_at.asc())
            .limit(limit)
            .all()
        )
        result = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
        }
        for task in tasks:
            result["processed"] += 1
            try:
                # 标记为处理中
                task.status = "processing"
                task.attempts += 1
                self.db.commit()
                self.db.refresh(task)
                # 重新发放权益
                order = (
                    self.db.query(PaymentOrder)
                    .filter(PaymentOrder.order_no == task.order_no)
                    .first()
                )
                if not order:
                    raise ValueError(f"Order not found: {task.order_no}")

                # 复用现有发放逻辑
                ProvisioningService(self.db).provision_after_payment(order)
                # 成功
                task.status = "completed"
                task.completed_at = datetime.now(timezone.utc)
                self.db.commit()
                result["succeeded"] += 1
                logger.info(
                    "Compensation succeeded | order_no=%s attempts=%d",
                    task.order_no,
                    task.attempts,
                )

            except Exception as exc:
                # 失败
                task.status = "failed"
                task.last_error = str(exc)[:1000]  # 限制长度
                self.db.commit()
                result["failed"] += 1
                logger.error(
                    "Compensation failed | order_no=%s attempt=%d err=%s",
                    task.order_no,
                    task.attempts,
                    exc,
                    exc_info=True,
                )

        return result

    def get_stats(self) -> dict:
        """获取补偿任务统计。"""
        pending = (
            self.db.query(PaymentCompensationTask)
            .filter(PaymentCompensationTask.status == "pending")
            .count()
        )
        processing = (
            self.db.query(PaymentCompensationTask)
            .filter(PaymentCompensationTask.status == "processing")
            .count()
        )
        failed = (
            self.db.query(PaymentCompensationTask)
            .filter(
                PaymentCompensationTask.status == "failed",
                PaymentCompensationTask.attempts >= PaymentCompensationTask.max_attempts,
            )
            .count()
        )
        completed = (
            self.db.query(PaymentCompensationTask)
            .filter(PaymentCompensationTask.status == "completed")
            .count()
        )
        return {
            "pending": pending,
            "processing": processing,
            "failed_exhausted": failed,
            "completed": completed,
            "total": pending + processing + failed + completed,
        }


def create_compensation_task(
    db: Session,
    order_no: str,
    source: str = "unknown",
) -> None:
    """创建补偿任务（供 payment_service 调用）。"""
    from datetime import datetime, timezone
    from sqlalchemy.exc import IntegrityError
    task = PaymentCompensationTask(
        order_no=order_no,
        source=source,
        status="pending",
        attempts=0,
        max_attempts=10,
        scheduled_at=datetime.now(timezone.utc),
    )
    try:
        db.add(task)
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning("Duplicate compensation task | order_no=%s", order_no)
