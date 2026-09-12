"""基础Repository类，提供通用CRUD操作"""

from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar

from sqlalchemy import delete, desc, func, select, update
from sqlalchemy.orm import Session

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """基础数据访问层"""
    def __init__(self, db: Session, model: type[ModelType]):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param model: 参数 model
        :return: 返回处理结果。
        """
        self.db = db
        self.model = model
        self._include_deleted = False

    def with_deleted(self) -> "BaseRepository":
        """链式调用：包含已软删除的记录"""
        self._include_deleted = True
        return self

    def _base_query(self):
        """基础查询，自动排除软删除记录"""
        query = select(self.model)
        if not self._include_deleted and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))
        return query

    def get_by_id(self, id: str) -> Optional[ModelType]:
        """根据ID获取单个对象"""
        query = self._base_query().where(self.model.id == id)
        return self.db.execute(query).scalar_one_or_none()

    def get_all(self) -> List[ModelType]:
        """获取所有对象"""
        return self.db.execute(self._base_query()).scalars().all()

    def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: dict = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> tuple[List[ModelType], int]:
        """分页获取对象"""
        query = self._base_query()
        # 应用过滤条件
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        # 计算总数
        count_query = select(self.model.id)
        if not self._include_deleted and hasattr(self.model, "deleted_at"):
            count_query = count_query.where(self.model.deleted_at.is_(None))
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    count_query = count_query.filter(
                        getattr(self.model, key) == value)
        total = self.db.scalar(select(func.count()).select_from(count_query.subquery()))
        # 排序
        sort_column = getattr(
            self.model, sort_by, getattr(
                self.model, "created_at"))
        if sort_desc:
            query = query.order_by(desc(sort_column))

        # 分页
        query = query.offset((page - 1) * page_size).limit(page_size)
        items = self.db.execute(query).scalars().all()
        return items, total

    def create(self, **kwargs) -> ModelType:
        """创建新对象"""
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(self, id: str, **kwargs) -> Optional[ModelType]:
        """更新对象"""
        instance = self.get_by_id(id)
        if not instance:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, id: str) -> bool:
        """软删除对象（如果模型支持），否则硬删除"""
        instance = self.get_by_id(id)
        if not instance:
            return False

        if hasattr(instance, "soft_delete"):
            instance.soft_delete()
            self.db.commit()
        else:
            self.db.delete(instance)
            self.db.commit()
        return True

    def restore(self, id: str) -> bool:
        """恢复软删除的对象"""
        instance = self.with_deleted().get_by_id(id)
        if not instance or not hasattr(instance, "restore"):
            return False
        instance.restore()
        self.db.commit()
        return True

    def permanent_delete(self, id: str) -> bool:
        """永久删除（跳过软删除）"""
        instance = self.with_deleted().get_by_id(id)
        if not instance:
            return False
        self.db.delete(instance)
        self.db.commit()
        return True

    def get_trashed(self, page: int = 1, page_size: int = 20) -> tuple[List[ModelType], int]:
        """获取已软删除的记录"""
        if not hasattr(self.model, "deleted_at"):
            return [], 0
        query = select(self.model).where(self.model.deleted_at.is_not(None))
        count = self.db.scalar(select(func.count()).select_from(
            select(self.model.id).where(self.model.deleted_at.is_not(None)).subquery()
        ))
        query = query.order_by(desc(self.model.deleted_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        items = self.db.execute(query).scalars().all()
        return items, count

    def bulk_create(self, instances: List[dict]) -> List[ModelType]:
        """批量创建对象"""
        objs = [self.model(**item) for item in instances]
        self.db.add_all(objs)
        self.db.commit()
        for obj in objs:
            self.db.refresh(obj)
        return objs

    def bulk_delete(self, ids: List[str]) -> int:
        """批量删除对象"""
        result = self.db.execute(
            delete(
                self.model).where(
                self.model.id.in_(ids)))
        self.db.commit()
        return result.rowcount

    def exists(self, **kwargs) -> bool:
        """检查对象是否存在"""
        query = select(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return self.db.execute(query).scalar() is not None

    def count(self, filters: dict = None) -> int:
        """统计对象数量"""
        query = self._base_query()
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        return self.db.execute(
            select(
                func.count()).select_from(
                query.subquery())).scalar()
