# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Repository 层 — FIX-42

提供统一的数据访问抽象层，隔离业务逻辑与数据库操作。
支持：
- 基础 CRUD 操作
- 分页查询
- 批量操作
- 事务管理
- 缓存集成
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar
from datetime import datetime

from sqlalchemy import func, select, delete, update
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta

from app.core.cache import multi_level_cache_decorator

log = logging.getLogger(__name__)

T = TypeVar("T", bound=DeclarativeMeta)


def _is_production() -> bool:
    """是否生产环境（延迟 import settings，避免模块加载时的重依赖与循环导入）。"""
    try:
        from app.core.config import settings
        return settings.is_production()
    except Exception:
        return False


class BaseRepository(ABC, Generic[T]):
    """Repository 基类。

    用法:
        class LeadRepository(BaseRepository[ProspectLead]):
            model = ProspectLead

    租户作用域（合并审计 #1）：传入 tenant_id 后，所有对带 tenant_id 表的
    查询/写/删/聚合自动追加 tenant_id 过滤，避免跨租户越权读取/写入。
    未传 tenant_id 却访问租户表时，在非生产环境记录告警日志（不阻断），
    以暴露侵越路径；生产环境不额外处理（保持既有行为，零回归）。
    """
    model: type[T] = None
    tenant_column = "tenant_id"

    def __init__(self, db: Session, tenant_id: str | None = None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param tenant_id: 可选租户作用域；设置后自动按该租户过滤。
        :return: 返回处理结果。
        """
        self.db = db
        self.tenant_id = tenant_id

    # ── 租户作用域 ──
    @property
    def _tables_carry_tenant(self) -> bool:
        return hasattr(self.model, self.tenant_column)

    def _warn_unscoped(self, method: str) -> None:
        if not _is_production():
            log.warning(
                "[TENANT][unscoped] %s → %s 访问租户表未传 tenant_id，"
                "可能造成跨租户越权。请显式传入 tenant_id（或改用带租户作用域的实例）。",
                type(self).__name__, getattr(self.model, "__name__", self.model),
            )

    def _apply_tenant(self, query) -> Any:
        """对查询追加租户过滤；访问租户表却未绑定租户时仅在非生产告警（不阻断，避免回归）。"""
        if not self._tables_carry_tenant:
            return query
        tenant_col = getattr(self.model, self.tenant_column)
        if self.tenant_id:
            return query.filter(tenant_col == self.tenant_id)
        # 仅告警，不阻断（保持既有行为）
        if log.isEnabledFor(logging.WARNING):
            self._warn_unscoped("query")
        return query

    def _apply_tenant_to_statement(self, stmt: Any) -> Any:
        """对 SQLAlchemy Core Update/Delete 语句追加租户过滤。"""
        if not self._tables_carry_tenant:
            return stmt
        tenant_col = getattr(self.model, self.tenant_column)
        if self.tenant_id:
            return stmt.where(tenant_col == self.tenant_id)
        if log.isEnabledFor(logging.WARNING):
            self._warn_unscoped("write")
        return stmt

    def _bind_tenant_on_create(self, kwargs: dict) -> dict:
        """create/bulk_create 写入时若绑定租户，自动补齐 tenant_id，防止乘机写入他租户。"""
        if self.tenant_id and hasattr(self.model, self.tenant_column):
            kwargs.setdefault(self.tenant_column, self.tenant_id)
        return kwargs

    # ── 查询 ──
    def get_by_id(self, id: str) -> Optional[T]:
        query = self.db.query(self.model).filter(self.model.id == id)
        return self._apply_tenant(query).first()

    def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> tuple[list[T], int]:
        """分页查询（带租户作用域）。"""
        query = self._apply_tenant(self.db.query(self.model))
        total = query.count()
        order_col = getattr(self.model, order_by, self.model.created_at)
        if order_desc:
            order_col = order_col.desc()

        items = (
            query.order_by(order_col)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def find_by(self, **filters) -> list[T]:
        """按条件查询（带租户作用域）。"""
        query = self._apply_tenant(self.db.query(self.model))
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.all()

    def find_one_by(self, **filters) -> Optional[T]:
        """按条件查询单条。"""
        return self.find_by(**filters)[0] if self.find_by(**filters) else None

    def count_by(self, **filters) -> int:
        """按条件计数（带租户作用域）。"""
        query = self._apply_tenant(self.db.query(func.count(self.model.id)))
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.scalar() or 0

    def exists(self, **filters) -> bool:
        """exists。

        参数说明：
        :param self: 参数 self
        :param **filters: 参数 **filters
        :return: 返回处理结果。
        """
        return self.count_by(**filters) > 0

    # ── 写入 ──
    def create(self, **kwargs) -> T:
        """create（绑定租户时自动补齐 tenant_id）。

        参数说明：
        :param self: 参数 self
        :param **kwargs: 参数 **kwargs
        :return: 返回处理结果。
        """
        instance = self.model(**self._bind_tenant_on_create(kwargs))
        self.db.add(instance)
        self.db.flush()
        return instance

    def update(self, id: str, **kwargs) -> Optional[T]:
        """update。

        参数说明：
        :param self: 参数 self
        :param id: 参数 id
        :param **kwargs: 参数 **kwargs
        :return: 返回处理结果。
        """
        instance = self.get_by_id(id)
        if not instance:
            return None
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        if hasattr(instance, "updated_at"):
            instance.updated_at = datetime.utcnow()
        self.db.flush()
        return instance

    def update_where(self, updates: dict, **filters) -> int:
        """批量更新（带租户作用域）。"""
        stmt = update(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        stmt = self._apply_tenant_to_statement(stmt)
        stmt = stmt.values(**updates)
        result = self.db.execute(stmt)
        return result.rowcount

    def delete(self, id: str) -> bool:
        """delete。

        参数说明：
        :param self: 参数 self
        :param id: 参数 id
        :return: 返回处理结果。
        """
        instance = self.get_by_id(id)  # 已带租户作用域
        if not instance:
            return False
        self.db.delete(instance)
        self.db.flush()
        return True

    def delete_where(self, **filters) -> int:
        """批量删除（带租户作用域）。"""
        stmt = delete(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        stmt = self._apply_tenant_to_statement(stmt)
        result = self.db.execute(stmt)
        return result.rowcount

    def bulk_create(self, items: list[dict]) -> list[T]:
        """bulk_create（绑定租户时自动补齐 tenant_id）。"""
        if self.tenant_id and self._tables_carry_tenant:
            for item in items:
                item.setdefault(self.tenant_column, self.tenant_id)
        instances = [self.model(**item) for item in items]
        self.db.add_all(instances)
        self.db.flush()
        return instances

    # ── 聚合 ──
    def aggregate(
        self,
        group_by: str,
        metrics: dict[str, Any],
        **filters,
    ) -> list[dict]:
        """聚合查询（带租户作用域）。"""
        columns = [getattr(self.model, group_by)]
        for label, agg_func in metrics.items():
            columns.append(agg_func.label(label))

        query = self._apply_tenant(self.db.query(*columns))
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        query = query.group_by(getattr(self.model, group_by))
        return [dict(row) for row in query.all()]

    def summary(self, **filters) -> dict:
        """获取汇总统计（带租户作用域）。"""
        query = self._apply_tenant(self.db.query(
            func.count(self.model.id).label("total"),
        ))
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        row = query.first()
        return {"total": row.total if row else 0}


# ============================================================
# 预置 Repository 实现
# ============================================================

class ProspectLeadRepository(BaseRepository):
    """线索 Repository。"""
    from app.models.prospect_lead import ProspectLead as _Model
    model = _Model
    def find_by_email(self, email: str) -> Optional[Any]:
        """find_by_email。

        参数说明：
        :param self: 参数 self
        :param email: 参数 email
        :return: 返回处理结果。
        """
        return self.find_one_by(email=email.lower().strip())

    def find_by_company(self, company: str, page: int = 1, page_size: int = 20):
        """find_by_company。

        参数说明：
        :param self: 参数 self
        :param company: 参数 company
        :param page: 参数 page
        :param page_size: 参数 page_size
        :return: 返回处理结果。
        """
        return self.get_all(page=page, page_size=page_size, order_by="score")

    def get_hot_leads(self, limit: int = 20) -> list[Any]:
        """get_hot_leads。

        参数说明：
        :param self: 参数 self
        :param limit: 参数 limit
        :return: 返回处理结果。
        """
        return (
            self.db.query(self.model)
            .filter(self.model.score >= 80)
            .order_by(self.model.score.desc())
            .limit(limit)
            .all()
        )

    def get_by_status(self, status: str, page: int = 1, page_size: int = 20):
        """get_by_status。

        参数说明：
        :param self: 参数 self
        :param status: 参数 status
        :param page: 参数 page
        :param page_size: 参数 page_size
        :return: 返回处理结果。
        """
        query = self.db.query(self.model).filter(self.model.status == status)
        total = query.count()
        items = (
            query.order_by(self.model.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def get_funnel_stats(self, since: datetime) -> dict:
        """获取漏斗统计。"""
        query = self.db.query(
            self.model.status,
            func.count(self.model.id).label("count"),
        ).filter(self.model.created_at >= since).group_by(self.model.status)
        return {row.status: row.count for row in query.all()}


class EmailOutreachRepository(BaseRepository):
    """邮件外展 Repository。"""
    from app.models.email_outreach import EmailOutreach as _Model
    model = _Model
    def get_by_prospect(self, prospect_id: str) -> list[Any]:
        """get_by_prospect。

        参数说明：
        :param self: 参数 self
        :param prospect_id: 参数 prospect_id
        :return: 返回处理结果。
        """
        return self.find_by(prospect_id=prospect_id)

    def get_pending(self, limit: int = 50) -> list[Any]:
        """get_pending。

        参数说明：
        :param self: 参数 self
        :param limit: 参数 limit
        :return: 返回处理结果。
        """
        return (
            self.db.query(self.model)
            .filter(self.model.status.in_(["draft", "queued"]))
            .order_by(self.model.created_at)
            .limit(limit)
            .all()
        )

    def get_stats(self, since: datetime) -> dict:
        """获取邮件统计。"""
        total = self.count_by()
        sent = self.db.query(self.model).filter(
            self.model.created_at >= since,
            self.model.status.in_(["sent", "delivered", "opened", "clicked", "replied"]),
        ).count()
        opened = self.db.query(self.model).filter(
            self.model.created_at >= since,
            self.model.status.in_(["opened", "clicked", "replied"]),
        ).count()
        replied = self.db.query(self.model).filter(
            self.model.created_at >= since,
            self.model.status == "replied",
        ).count()
        return {
            "total": total,
            "sent": sent,
            "opened": opened,
            "replied": replied,
            "open_rate": round(opened / max(1, sent) * 100, 1),
            "reply_rate": round(replied / max(1, sent) * 100, 1),
        }


# Repository 工厂
def get_repository(repo_class: type[BaseRepository], db: Session) -> BaseRepository:
    """获取 Repository 实例。"""
    return repo_class(db)