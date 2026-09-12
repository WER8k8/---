"""Sales Task 模型 — 销售任务/通知（RFQ → 销售任务闭环）"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base, UUID_TYPE
from app.models.soft_delete import SoftDeleteMixin


class SalesTask(SoftDeleteMixin, Base):
    """销售跟进任务。"""
    __tablename__ = "sales_tasks"
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=False, default="followup", index=True)
    # followup / rfq_response / quote_approval / outbound / review
    priority = Column(String(20), nullable=False, default="normal", index=True)  # high / normal / low
    status = Column(String(50), nullable=False, default="open", index=True)  # open / done / cancelled
    due_at = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(String(36), nullable=True, index=True)
    # 关联
    rfq_id = Column(UUID_TYPE, ForeignKey("rfqs.id"), nullable=True, index=True)
    opportunity_id = Column(String(36), nullable=True, index=True)
    company_id = Column(String(36), nullable=True, index=True)
    lead_id = Column(String(36), nullable=True, index=True)
    tenant_id = Column(String(36), nullable=True, index=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<SalesTask(title={self.title}, status={self.status})>"
