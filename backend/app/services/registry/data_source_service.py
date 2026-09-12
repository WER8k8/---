"""数据源合规评审服务（轮17-6）。

§5.2.4：数据源接入前必须登记四元元数据（name/data_class/license_basis/
tos_verified）并经评审；review_status 默认 pending，approved 才允许实际采集。
裁决权归 Policy Engine（§A.6 轮22）。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.registry import (
    DataSourceProvider,
    DATA_CLASSES,
    LICENSE_BASIS,
    REVIEW_STATUSES,
)
from app.services.registry.common import ensure_in, valid_name


class DataSourceNotFoundError(Exception):
    """指定数据源不存在。"""


class DataSourceConflictError(Exception):
    """数据源 name 已存在。"""


class DataSourceService:
    """数据源合规清单管理。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, provider_id: str) -> DataSourceProvider | None:
        return (
            self.db.query(DataSourceProvider)
            .filter(DataSourceProvider.id == provider_id)
            .first()
        )

    def get_by_name(self, name: str) -> DataSourceProvider | None:
        return (
            self.db.query(DataSourceProvider)
            .filter(DataSourceProvider.name == name)
            .first()
        )

    def list_providers(
        self, *, data_class: str | None = None, review_status: str | None = None
    ) -> list[dict[str, Any]]:
        q = self.db.query(DataSourceProvider)
        if data_class:
            ensure_in(data_class, DATA_CLASSES, "data_class")
            q = q.filter(DataSourceProvider.data_class == data_class)
        if review_status:
            ensure_in(review_status, REVIEW_STATUSES, "review_status")
            q = q.filter(DataSourceProvider.review_status == review_status)
        return [self._to_dict(p) for p in q.order_by(DataSourceProvider.name).all()]

    def register(
        self,
        *,
        name: str,
        data_class: str,
        license_basis: str,
        tos_verified: bool = False,
        gdpr_category: str | None = None,
        review_notes: str | None = None,
    ) -> DataSourceProvider:
        if not valid_name(name):
            raise ValueError(f"非法数据源名: {name!r}")
        ensure_in(data_class, DATA_CLASSES, "data_class")
        ensure_in(license_basis, LICENSE_BASIS, "license_basis")
        if self.get_by_name(name):
            raise DataSourceConflictError(f"已存在数据源: {name}")
        provider = DataSourceProvider(
            name=name,
            data_class=data_class,
            license_basis=license_basis,
            tos_verified=tos_verified,
            gdpr_category=gdpr_category,
            review_status="pending",
            review_notes=review_notes,
        )
        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def review(
        self,
        provider_id: str,
        *,
        decision: str,
        notes: str | None = None,
    ) -> DataSourceProvider:
        """评审裁决：决策者必须是 Policy Engine 授权调用。"""
        provider = self.get(provider_id)
        if not provider:
            raise DataSourceNotFoundError(provider_id)
        ensure_in(decision, REVIEW_STATUSES, "review_status")
        provider.review_status = decision
        provider.review_notes = notes or provider.review_notes
        provider.reviewed_at = datetime.now(timezone.utc)
        provider.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def ensure_approved(self, provider_id: str) -> DataSourceProvider:
        """确认该数据源已获批准；否则抛 ValueError（供采集前门禁调用）。"""
        provider = self.get(provider_id)
        if not provider:
            raise DataSourceNotFoundError(provider_id)
        if provider.review_status != "approved":
            raise PermissionError(
                f"数据源 {provider.name} 未获评审批准（当前: {provider.review_status}）"
            )
        return provider

    def _to_dict(self, p: DataSourceProvider) -> dict[str, Any]:
        return {
            "id": str(p.id),
            "name": p.name,
            "data_class": p.data_class,
            "license_basis": p.license_basis,
            "tos_verified": p.tos_verified,
            "gdpr_category": p.gdpr_category,
            "review_status": p.review_status,
            "review_notes": p.review_notes,
            "reviewed_at": p.reviewed_at,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }


def build_data_source_service(db: Session) -> DataSourceService:
    """build_data_source_service。
    :param db: 会话。
    :return: DataSourceService 实例。
    """
    return DataSourceService(db)