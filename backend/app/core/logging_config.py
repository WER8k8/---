"""日志配置 - 配置结构化日志输出"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

from pydantic_settings import BaseSettings


class LoggingSettings(BaseSettings):
    """日志配置设置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = "logs/app.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


def setup_logging(settings: Optional[LoggingSettings] = None):
    """设置日志配置"""
    if settings is None:
        settings = LoggingSettings()
    
    # 创建根日志记录器
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.level.upper()))
    
    # 清除默认处理器
    logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(settings.format)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 创建文件处理器（如果配置了文件路径）
    if settings.file_path:
        file_handler = RotatingFileHandler(
            settings.file_path,
            maxBytes=settings.max_file_size,
            backupCount=settings.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class AppLogger:
    """应用日志记录器"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exc_info=False, **kwargs):
        self.logger.error(message, exc_info=exc_info, extra=kwargs)
    
    def critical(self, message: str, exc_info=True, **kwargs):
        self.logger.critical(message, exc_info=exc_info, extra=kwargs)
