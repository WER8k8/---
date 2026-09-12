"""
Talking-Stick Agent 基类
所有Agent的基类，提供通用功能
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime

from ..config import ConfigManager, ModelConfig
from ..file_lock import FileLock

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent 基类"""
    def __init__(self, agent_type: str, config_manager: ConfigManager):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param agent_type: 参数 agent_type
        :param config_manager: 参数 config_manager
        :return: 返回处理结果。
        """
        self.agent_type = agent_type
        self.config_manager = config_manager
        self.model_config: Optional[ModelConfig] = None
        self.file_lock: Optional[FileLock] = None
        # 初始化配置
        self._init_config()
    
    def _init_config(self) -> None:
        """初始化配置"""
        try:
            self.model_config = self.config_manager.get_model_config(self.agent_type)
        except ValueError:
            # 如果没有特定配置，使用默认配置
            self.model_config = ModelConfig(
                provider="openai",
                model="gpt-4",
                max_tokens=4096,
                temperature=0.0
            )
        
        # 初始化文件锁
        file_lock_config = self.config_manager.get('file_lock')
        if file_lock_config:
            self.file_lock = FileLock(
                lock_dir=file_lock_config.lock_dir,
                timeout=file_lock_config.timeout
            )
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """执行Agent任务"""
        pass
    
    async def acquire_file_lock(self, target_path: str) -> str:
        """获取文件锁"""
        if not self.file_lock:
            raise RuntimeError("文件锁未初始化")
        
        return await self.file_lock.acquire(target_path)
    
    async def release_file_lock(self, lock_id: str) -> None:
        """释放文件锁"""
        if self.file_lock:
            await self.file_lock.release(lock_id)
    
    def generate_id(self, prefix: str) -> str:
        """生成唯一ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}_{id(self)}"
    
    def log(self, message: str, level: str = "info") -> None:
        """记录日志"""
        level_map = {"info": logger.info, "warning": logger.warning, "error": logger.error, "debug": logger.debug}
        log_func = level_map.get(level, logger.info)
        log_func("[%s] %s", self.agent_type.upper(), message)

    async def _call_ai_model(self, prompt: str, **kwargs) -> str:
        """调用AI模型"""
        # TODO [P2] 集成现有的AI引擎（待AI服务对接后实现）
        return f"AI模型响应占位符 - {self.agent_type}"
