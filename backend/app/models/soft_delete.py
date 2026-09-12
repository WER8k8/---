"""软删除 Mixin — 给模型添加 deleted_at 字段和软删除能力"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


class SoftDeleteMixin:
    """Mixin: 给模型添加 deleted_at 字段

    用法:
        class Product(SoftDeleteMixin, Base):
            __tablename__ = "products"
            ...
    """
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, index=True
    )
    @property
    def is_deleted(self) -> bool:
        """is_deleted。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.deleted_at is not None

    def soft_delete(self):
        """soft_delete。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self):
        """restore。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.deleted_at = None
