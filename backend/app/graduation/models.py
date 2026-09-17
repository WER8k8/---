# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
功能开关（Feature Flag）模型
支持灰度发布、A/B测试、紧急回滚
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from enum import Enum


class FeatureStatus(str, Enum):
    """功能状态"""
    ACTIVE = "active"  # 已启用
    INACTIVE = "inactive"  # 已禁用
    GRADUATED = "graduated"  # 已毕业（完全发布）


class RolloutStrategy(str, Enum):
    """灰度策略"""
    PERCENTAGE = "percentage"  # 按百分比灰度
    USER_ID = "user_id"  # 按用户ID哈希
    REGION = "region"  # 按地区
    WHITELIST = "whitelist"  # 白名单


@dataclass
class FeatureFlag:
    """功能开关"""
    id: str  # 唯一标识
    name: str  # 显示名称
    description: str  # 描述
    status: FeatureStatus = FeatureStatus.INACTIVE
    # 灰度策略
    strategy: RolloutStrategy = RolloutStrategy.PERCENTAGE
    percentage: int = 0  # 灰度百分比（0-100）
    whitelist: List[str] = field(default_factory=list)  # 白名单（用户ID列表）
    regions: List[str] = field(default_factory=list)  # 地区列表
    # 监控指标
    monitor_metrics: List[str] = field(default_factory=list)  # 监控指标（如 "error_rate", "response_time"）
    auto_rollback: bool = True  # 是否启用自动回滚
    rollback_threshold: float = 0.05  # 回滚阈值（错误率上升5%触发回滚）
    # 时间戳
    created_at: str = ""  # 创建时间
    updated_at: str = ""  # 更新时间
    activated_at: Optional[str] = None  # 激活时间
    graduated_at: Optional[str] = None  # 毕业时间
    def __post_init__(self):
        """__post_init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
    
    def is_enabled_for_user(self, user_id: str, region: str = "") -> bool:
        """
        检查功能是否对用户启用
        
        Args:
            user_id: 用户ID
            region: 用户地区
            
        Returns:
            是否启用
        """
        if self.status == FeatureStatus.INACTIVE:
            return False
        
        if self.status == FeatureStatus.GRADUATED:
            return True
        
        # 按策略判断
        if self.strategy == RolloutStrategy.WHITELIST:
            return user_id in self.whitelist
        
        elif self.strategy == RolloutStrategy.REGION:
            return region in self.regions
        
        elif self.strategy == RolloutStrategy.USER_ID:
            # 基于用户ID哈希的灰度
            import hashlib
            hash_obj = hashlib.md5(user_id.encode())
            hash_int = int(hash_obj.hexdigest(), 16)
            return (hash_int % 100) < self.percentage
        
        else:  # PERCENTAGE
            # 随机灰度（简化版：基于用户ID）
            return self.is_enabled_for_user(user_id, region)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "strategy": self.strategy.value,
            "percentage": self.percentage,
            "whitelist": self.whitelist,
            "regions": self.regions,
            "monitor_metrics": self.monitor_metrics,
            "auto_rollback": self.auto_rollback,
            "rollback_threshold": self.rollback_threshold,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "activated_at": self.activated_at,
            "graduated_at": self.graduated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureFlag":
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            status=FeatureStatus(data["status"]),
            strategy=RolloutStrategy(data["strategy"]),
            percentage=data["percentage"],
            whitelist=data.get("whitelist", []),
            regions=data.get("regions", []),
            monitor_metrics=data.get("monitor_metrics", []),
            auto_rollback=data.get("auto_rollback", True),
            rollback_threshold=data.get("rollback_threshold", 0.05),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            activated_at=data.get("activated_at"),
            graduated_at=data.get("graduated_at"),
        )


# 导出
__all__ = ["FeatureFlag", "FeatureStatus", "RolloutStrategy"]
