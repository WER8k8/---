# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""代理层级关系树

代理组织树模型：定义 L1-L5 五级代理层级结构，
支持逐级向上汇总和向下钻取的数据聚合查询。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import UUID_TYPE, Base


class AgentNode(Base):
    """代理节点 - 组织树中的每个节点

    层级说明:
        L1: 超管
        L2: 省级代理
        L3: 市级代理
        L4: 官网租户

    通过 parent_id 自引用形成树形结构，root_id 标记整棵树的根节点。
    """
    __tablename__ = "agent_nodes"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    level = Column(String(10), nullable=False, index=True)  # l1/l2/l3/l4
    parent_id = Column(
        UUID_TYPE, ForeignKey("agent_nodes.id"), index=True, nullable=True
    )
    root_id = Column(UUID_TYPE, index=True)
    agent_user_id = Column(
        UUID_TYPE, ForeignKey("users.id"), nullable=True
    )  # 关联的代理用户
    status = Column(String(20), default="active")  # active / frozen / closed
    data_scope = Column(Text)  # JSON: 数据范围配置（城市、行业等）
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    # 自引用关系
    children = relationship(
        "AgentNode",
        backref="parent",
        remote_side=[id],
        foreign_keys=[parent_id],
        lazy="selectin",
    )
    def __repr__(self):
        """__repr__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return f"<AgentNode(id={self.id}, name={self.name}, level={self.level})>"

    def to_dict(self, include_children: bool = False) -> dict:
        """序列化为字典，可选包含子节点"""
        data = {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "parent_id": self.parent_id,
            "root_id": self.root_id,
            "agent_user_id": self.agent_user_id,
            "status": self.status,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_children and self.children:
            data["children"] = [c.to_dict(include_children=True) for c in self.children]
        return data
