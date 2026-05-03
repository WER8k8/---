"""
日志轮转和监控告警配置
"""

import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime


class LogConfig:
    """日志配置类"""
    
    # 日志目录
    LOG_DIR = Path(__file__).parent.parent.parent / "logs"
    LOG_DIR.mkdir(exist_ok=True)
    
    # 日志格式
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # 日志级别
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    
    @classmethod
    def setup_logging(cls, log_level: str = 'INFO', max_bytes: int = 10*1024*1024, backup_count: int = 5):
        """配置日志系统"""
        
        # 根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(cls.LOG_LEVELS.get(log_level, logging.INFO))
        
        # 清除现有处理器
        root_logger.handlers.clear()
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(cls.LOG_FORMAT, datefmt=cls.DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # 主日志文件 - 按大小轮转
        main_log_file = cls.LOG_DIR / "app.log"
        main_handler = RotatingFileHandler(
            main_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.DEBUG)
        main_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt=cls.DATE_FORMAT
        )
        main_handler.setFormatter(main_formatter)
        root_logger.addHandler(main_handler)
        
        # 错误日志文件 - 按时间轮转
        error_log_file = cls.LOG_DIR / "error.log"
        error_handler = TimedRotatingFileHandler(
            error_log_file,
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(main_formatter)
        root_logger.addHandler(error_handler)
        
        # 审计日志文件
        audit_log_file = cls.LOG_DIR / "audit.log"
        audit_handler = RotatingFileHandler(
            audit_log_file,
            maxBytes=max_bytes,
            backupCount=10,
            encoding='utf-8'
        )
        audit_handler.setLevel(logging.INFO)
        audit_formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(message)s',
            datefmt=cls.DATE_FORMAT
        )
        audit_handler.setFormatter(audit_formatter)
        
        # 审计日志器
        audit_logger = logging.getLogger('audit')
        audit_logger.setLevel(logging.INFO)
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False  # 不传播到根日志器
        
        # 性能日志文件
        perf_log_file = cls.LOG_DIR / "performance.log"
        perf_handler = RotatingFileHandler(
            perf_log_file,
            maxBytes=max_bytes,
            backupCount=7,
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        perf_formatter = logging.Formatter(
            '%(asctime)s - PERFORMANCE - %(message)s',
            datefmt=cls.DATE_FORMAT
        )
        perf_handler.setFormatter(perf_formatter)
        
        # 性能日志器
        perf_logger = logging.getLogger('performance')
        perf_logger.setLevel(logging.INFO)
        perf_logger.addHandler(perf_handler)
        perf_logger.propagate = False
        
        return root_logger, audit_logger, perf_logger
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """获取命名日志器"""
        return logging.getLogger(name)


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.alert_handlers = []
        self.alert_count = 0
        self.last_alert_time = None
    
    def add_handler(self, handler):
        """添加告警处理器"""
        self.alert_handlers.append(handler)
    
    def send_alert(self, level: str, message: str, metadata: dict = None):
        """发送告警"""
        self.alert_count += 1
        self.last_alert_time = datetime.now()
        
        alert_data = {
            'level': level,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {},
            'count': self.alert_count
        }
        
        # 记录告警日志
        logger = logging.getLogger('alert')
        log_method = getattr(logger, level.lower(), logger.warning)
        log_method(f"ALERT [{level}]: {message} | {metadata}")
        
        # 触发处理器
        for handler in self.alert_handlers:
            try:
                handler(alert_data)
            except Exception as e:
                logger.error(f"告警处理器执行失败: {e}")
    
    def check_error_rate(self, error_count: int, total_count: int, threshold: float = 0.05):
        """检查错误率是否超过阈值"""
        if total_count == 0:
            return
        
        error_rate = error_count / total_count
        if error_rate > threshold:
            self.send_alert(
                'CRITICAL',
                f'错误率超过阈值: {error_rate:.2%} (阈值: {threshold:.2%})',
                {'error_count': error_count, 'total_count': total_count, 'error_rate': error_rate}
            )
    
    def check_response_time(self, response_time: float, threshold: float = 2.0):
        """检查响应时间是否超过阈值"""
        if response_time > threshold:
            self.send_alert(
                'WARNING',
                f'响应时间超过阈值: {response_time:.2f}s (阈值: {threshold:.2f}s)',
                {'response_time': response_time, 'threshold': threshold}
            )


# 全局告警管理器实例
alert_manager = AlertManager()


def setup_alert_handlers():
    """配置告警处理器"""
    
    # 邮件告警处理器（示例）
    def email_alert_handler(alert_data):
        # 实际项目中应配置邮件发送
        logger = logging.getLogger('alert.email')
        logger.info(f"邮件告警: {alert_data['message']}")
    
    # Webhook告警处理器（示例）
    def webhook_alert_handler(alert_data):
        # 实际项目中应配置Webhook发送
        logger = logging.getLogger('alert.webhook')
        logger.info(f"Webhook告警: {alert_data['message']}")
    
    alert_manager.add_handler(email_alert_handler)
    alert_manager.add_handler(webhook_alert_handler)
    
    return alert_manager
