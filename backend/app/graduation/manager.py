"""
灰度发布管理服务
管理功能开关、灰度流量分配、自动回滚
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from app.graduation.models import FeatureFlag, FeatureStatus, RolloutStrategy
from app.core.cache import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class GraduationManager:
    """
    灰度发布管理器
    管理功能开关、灰度流量分配、自动回滚
    """
    def __init__(self):
        """初始化灰度管理器"""
        self.flags: Dict[str, FeatureFlag] = {}
        self._load_flags()
        logger.info(f"✅ GraduationManager initialized with {len(self.flags)} flags")
    
    def _load_flags(self):
        """从Redis加载功能开关"""
        if not redis_client:
            logger.warning("⚠️ Redis未连接，使用内存存储")
            return
        
        try:
            # 加载所有功能开关
            keys = redis_client.scan_iter(match="flag:*", count=100)
            for key in keys:
                data = redis_client.get(key)
                if data:
                    flag = FeatureFlag.from_dict(json.loads(data))
                    self.flags[flag.id] = flag
            
            logger.info(f"✅ 加载了{len(self.flags)}个功能开关")
        except Exception as e:
            logger.error(f"❌ 加载功能开关失败: {e}", exc_info=True)
    
    def _save_flag(self, flag: FeatureFlag):
        """保存功能开关到Redis"""
        if not redis_client:
            return
        
        try:
            key = f"flag:{flag.id}"
            redis_client.set(key, json.dumps(flag.to_dict()))
        except Exception as e:
            logger.error(f"❌ 保存功能开关失败: {e}", exc_info=True)
    
    def create_flag(
        self,
        flag_id: str,
        name: str,
        description: str,
        strategy: RolloutStrategy = RolloutStrategy.PERCENTAGE,
        percentage: int = 0
    ) -> FeatureFlag:
        """
        创建功能开关
        
        Args:
            flag_id: 功能ID
            name: 显示名称
            description: 描述
            strategy: 灰度策略
            percentage: 灰度百分比
            
        Returns:
            创建的功能开关
        """
        if flag_id in self.flags:
            raise ValueError(f"功能开关已存在: {flag_id}")
        
        flag = FeatureFlag(
            id=flag_id,
            name=name,
            description=description,
            status=FeatureStatus.INACTIVE,
            strategy=strategy,
            percentage=percentage
        )
        self.flags[flag_id] = flag
        self._save_flag(flag)
        logger.info(f"✅ 创建功能开关: {flag_id}")
        return flag
    
    def activate_flag(self, flag_id: str) -> bool:
        """
        激活功能开关（开始灰度）
        
        Args:
            flag_id: 功能ID
            
        Returns:
            是否成功
        """
        if flag_id not in self.flags:
            logger.error(f"❌ 功能开关不存在: {flag_id}")
            return False
        
        flag = self.flags[flag_id]
        flag.status = FeatureStatus.ACTIVE
        flag.activated_at = datetime.now(timezone.utc).isoformat()
        flag.updated_at = flag.activated_at
        self._save_flag(flag)
        logger.info(f"✅ 激活功能开关: {flag_id}")
        return True
    
    def graduate_flag(self, flag_id: str) -> bool:
        """
        毕业功能开关（完全发布）
        
        Args:
            flag_id: 功能ID
            
        Returns:
            是否成功
        """
        if flag_id not in self.flags:
            logger.error(f"❌ 功能开关不存在: {flag_id}")
            return False
        
        flag = self.flags[flag_id]
        flag.status = FeatureStatus.GRADUATED
        flag.graduated_at = datetime.now(timezone.utc).isoformat()
        flag.updated_at = flag.graduated_at
        self._save_flag(flag)
        logger.info(f"✅ 毕业功能开关: {flag_id}")
        return True
    
    def deactivate_flag(self, flag_id: str) -> bool:
        """
        停用功能开关（回滚）
        
        Args:
            flag_id: 功能ID
            
        Returns:
            是否成功
        """
        if flag_id not in self.flags:
            logger.error(f"❌ 功能开关不存在: {flag_id}")
            return False
        
        flag = self.flags[flag_id]
        flag.status = FeatureStatus.INACTIVE
        flag.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_flag(flag)
        logger.info(f"✅ 停用功能开关: {flag_id}")
        return True
    
    def update_percentage(self, flag_id: str, percentage: int) -> bool:
        """
        更新灰度百分比
        
        Args:
            flag_id: 功能ID
            percentage: 新百分比（0-100）
            
        Returns:
            是否成功
        """
        if flag_id not in self.flags:
            logger.error(f"❌ 功能开关不存在: {flag_id}")
            return False
        
        if not 0 <= percentage <= 100:
            raise ValueError(f"百分比必须在0-100之间: {percentage}")
        
        flag = self.flags[flag_id]
        flag.percentage = percentage
        flag.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_flag(flag)
        logger.info(f"✅ 更新灰度百分比: {flag_id} -> {percentage}%")
        return True
    
    def is_enabled(self, flag_id: str, user_id: str, region: str = "") -> bool:
        """
        检查功能是否对用户启用
        
        Args:
            flag_id: 功能ID
            user_id: 用户ID
            region: 用户地区
            
        Returns:
            是否启用
        """
        if flag_id not in self.flags:
            return False
        
        flag = self.flags[flag_id]
        return flag.is_enabled_for_user(user_id, region)
    
    def get_flag(self, flag_id: str) -> Optional[FeatureFlag]:
        """获取功能开关"""
        return self.flags.get(flag_id)
    
    def list_flags(self) -> List[FeatureFlag]:
        """列出所有功能开关"""
        return list(self.flags.values())
    
    async def check_rollback(self, flag_id: str) -> tuple[bool, str]:
        """
        检查是否需要自动回滚
        
        Args:
            flag_id: 功能ID
            
        Returns:
            (是否需要回滚, 原因)
        """
        if flag_id not in self.flags:
            return False, "功能开关不存在"
        
        flag = self.flags[flag_id]
        if not flag.auto_rollback:
            return False, "自动回滚未启用"
        
        # 自动回滚检查逻辑
        # 检查监控指标（错误率、响应时间等），超过阈值则触发回滚
        from app.core.database import get_redis
        redis_client = get_redis()
        if redis_client:
            metrics_key = f"graduation:metrics:{flag_id}"
            raw = redis_client.get(metrics_key)
            if raw:
                import json
                metrics = json.loads(raw)
                error_rate = metrics.get("error_rate", 0)
                avg_response_time = metrics.get("avg_response_time", 0)
                if error_rate > 0.05:  # 错误率 > 5%
                    return True, f"错误率过高: {error_rate:.1%}"
                if avg_response_time > 3000:  # 响应时间 > 3s
                    return True, f"响应时间过长: {avg_response_time}ms"

        return False, "检查通过"


# 全局管理器实例
_manager: Optional[GraduationManager] = None


def get_graduation_manager() -> GraduationManager:
    """获取全局灰度管理器"""
    global _manager
    if _manager is None:
        _manager = GraduationManager()
    return _manager


# 导出
__all__ = ["GraduationManager", "get_graduation_manager"]
