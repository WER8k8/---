"""
日志轮转和监控告警配置
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path

import requests

from app.core.config import settings

import json
import re
from app.core.log_context import get_log_context


class ContextEnrichFilter(logging.Filter):
    """上下文变量增强过滤器"""
    def filter(self, record):
        ctx = get_log_context()
        record.tenant_id = ctx.get("tenant_id")
        record.user_id = ctx.get("user_id")
        record.trace_id = ctx.get("trace_id")
        record.request_path = ctx.get("request_path")
        return True


_EMAIL_PATTERN = re.compile(r'([a-zA-Z0-9_.+-])[a-zA-Z0-9_.+-]+@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')
_PHONE_PATTERN = re.compile(r'(1[3-9]\d)\d{4}(\d{4})')
_PASSWORD_PATTERN = re.compile(r'(password|passwd|pwd|secret|token)["\']?\s*[:=]\s*["\']?([^"\'\s,]+)', re.IGNORECASE)

def mask_pii(text: str) -> str:
    """脱敏日志中的个人敏感隐私信息（PII）。"""
    if not isinstance(text, str):
        return text
    text = _EMAIL_PATTERN.sub(r'\1***@\2', text)
    text = _PHONE_PATTERN.sub(r'\1****\2', text)
    text = _PASSWORD_PATTERN.sub(r'\1="******"', text)
    return text


class StructuredJsonFormatter(logging.Formatter):
    """JSON结构化格式器，具备敏感信息脱敏与请求上下文透传能力。"""
    def format(self, record):
        exc_info = self.formatException(record.exc_info) if record.exc_info else None
        env = getattr(settings, "ENVIRONMENT", "unknown")

        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": mask_pii(record.getMessage()),
            "filename": record.filename,
            "lineno": record.lineno,
            "tenant_id": getattr(record, "tenant_id", None),
            "user_id": getattr(record, "user_id", None),
            "trace_id": getattr(record, "trace_id", None),
            "request_path": getattr(record, "request_path", None),
            "environment": env,
        }
        if exc_info:
            log_obj["exc_info"] = mask_pii(exc_info)

        return json.dumps(log_obj, ensure_ascii=False)


class MaskedConsoleFormatter(logging.Formatter):
    """控制台格式器 — 与文件日志同一套 PII 脱敏（邮箱/手机号/密码样式）。"""

    def format(self, record):
        formatted = super().format(record)
        return mask_pii(formatted)


class LogConfig:
    """日志配置类"""
    # 日志目录
    LOG_DIR = Path(__file__).parent.parent.parent / "logs"
    LOG_DIR.mkdir(exist_ok=True)
    # 日志格式
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    # 日志级别
    LOG_LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    @classmethod
    def setup_logging(
            cls,
            log_level: str = "WARNING",
            max_bytes: int = 10 *
            1024 *
            1024,
            backup_count: int = 5):
        """配置日志系统"""
        # 根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(cls.LOG_LEVELS.get(log_level, logging.INFO))
        # 清除现有处理器
        root_logger.handlers.clear()
        
        enrich_filter = ContextEnrichFilter()

        # 控制台处理器（与文件日志同一套 PII 脱敏）
        # enrich filter 必须挂在 handler 上：挂在 root logger 只对 root 自身记录生效，
        # 命名 logger（app.* / 业务模块）的记录传播到 root handler 时会缺 trace_id 导致格式化失败。
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.addFilter(enrich_filter)
        console_formatter = MaskedConsoleFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(trace_id)s] - %(message)s", datefmt=cls.DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        json_formatter = StructuredJsonFormatter()
        
        # 主日志文件 - 按大小轮转
        main_log_file = cls.LOG_DIR / "app.log"
        main_handler = RotatingFileHandler(
            main_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8")
        main_handler.setLevel(logging.DEBUG)
        main_handler.addFilter(enrich_filter)
        main_handler.setFormatter(json_formatter)
        root_logger.addHandler(main_handler)
        
        # 错误日志文件 - 按时间轮转
        error_log_file = cls.LOG_DIR / "error.log"
        error_handler = TimedRotatingFileHandler(
            error_log_file,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8")
        error_handler.setLevel(logging.ERROR)
        error_handler.addFilter(enrich_filter)
        error_handler.setFormatter(json_formatter)
        root_logger.addHandler(error_handler)
        
        # 审计日志文件
        audit_log_file = cls.LOG_DIR / "audit.log"
        audit_handler = RotatingFileHandler(
            audit_log_file,
            maxBytes=max_bytes,
            backupCount=10,
            encoding="utf-8")
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(json_formatter)
        
        # 审计日志器
        audit_logger = logging.getLogger("audit")
        audit_logger.setLevel(logging.INFO)
        audit_logger.addFilter(enrich_filter)
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False  # 不传播到根日志器
        
        # 性能日志文件
        perf_log_file = cls.LOG_DIR / "performance.log"
        perf_handler = RotatingFileHandler(
            perf_log_file,
            maxBytes=max_bytes,
            backupCount=7,
            encoding="utf-8")
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(json_formatter)
        
        # 性能日志器
        perf_logger = logging.getLogger("performance")
        perf_logger.setLevel(logging.INFO)
        perf_logger.addFilter(enrich_filter)
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
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
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
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
            "count": self.alert_count,
        }
        # 记录告警日志
        logger = logging.getLogger("alert")
        log_method = getattr(logger, level.lower(), logger.warning)
        log_method(f"ALERT [{level}]: {message} | {metadata}")
        # 触发处理器
        for handler in self.alert_handlers:
            try:
                handler(alert_data)
            except Exception as e:
                logger.error(f"告警处理器执行失败: {e}")

    def check_error_rate(
            self,
            error_count: int,
            total_count: int,
            threshold: float = 0.05):
        """检查错误率是否超过阈值"""
        if total_count == 0:
            return

        error_rate = error_count / total_count
        if error_rate > threshold:
            self.send_alert(
                "CRITICAL",
                f"错误率超过阈值: {error_rate:.2%} (阈值: {threshold:.2%})",
                {"error_count": error_count, "total_count": total_count, "error_rate": error_rate},
            )

    def check_response_time(
            self,
            response_time: float,
            threshold: float = 2.0):
        """检查响应时间是否超过阈值"""
        if response_time > threshold:
            self.send_alert(
                "WARNING",
                f"响应时间超过阈值: {response_time:.2f}s (阈值: {threshold:.2f}s)",
                {"response_time": response_time, "threshold": threshold},
            )


# 全局告警管理器实例
alert_manager = AlertManager()


def send_to_feishu_bot(message: str, level: str = "INFO") -> bool:
    """发送消息到飞书机器人（默认渠道）- 永久有效配置"""
    try:
        # 检查飞书通知是否启用
        if not settings.FEISHU_NOTIFICATION_ENABLED:
            logger = logging.getLogger("alert.feishu")
            logger.info("飞书通知已禁用，跳过发送")
            return False

        # 检查飞书配置是否已设置
        if not settings.FEISHU_APP_ID or not settings.FEISHU_APP_SECRET:
            logger = logging.getLogger("alert.feishu")
            logger.warning("飞书AppID或AppSecret未配置，跳过飞书消息发送")
            return False

        # 构建飞书消息卡片
        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": f"🔔 系统通知 [{level}]"},
                "template": "red" if level in ["CRITICAL", "ERROR"] else "blue",
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": f"{message}"}},
                {
                    "tag": "div",
                    "text": {"tag": "plain_text", "content": f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"},
                },
            ],
        }
        # 通过内部API发送
        from app.services.feishu.client import FeishuClient
        feishu_client = FeishuClient()
        feishu_client.send_broadcast_message(message, card)
        logger = logging.getLogger("alert.feishu")
        logger.info(f"飞书消息发送成功: {message[:50]}...")
        return True
    except Exception as e:
        logger = logging.getLogger("alert.feishu")
        logger.error(f"飞书消息发送失败: {e}")
        return False


def send_work_report_to_feishu(
        title: str,
        content: str,
        report_type: str = "工作汇报") -> bool:
    """发送工作汇报到飞书机器人（专用方法）"""
    try:
        if not settings.FEISHU_NOTIFICATION_ENABLED:
            return False

        if not settings.FEISHU_APP_ID or not settings.FEISHU_APP_SECRET:
            logger = logging.getLogger("alert.feishu")
            logger.warning("飞书配置未设置")
            return False

        # 构建汇报卡片
        card = {"config": {"wide_screen_mode": True},
                "header": {"title": {"tag": "plain_text",
                                     "content": f"📋 {title}"},
                           "template": "green"},
                "elements": [{"tag": "div",
                              "text": {"tag": "lark_md",
                                       "content": f"**类型**: {report_type}\n\n{content}"}},
                             {"tag": "div",
                              "text": {"tag": "plain_text",
                                       "content": f"发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                       },
                              },
                             ],
                }

        from app.services.feishu.client import FeishuClient
        feishu_client = FeishuClient()
        feishu_client.send_broadcast_message(content, card)
        return True
    except Exception as e:
        logger = logging.getLogger("alert.feishu")
        logger.error(f"发送工作汇报失败: {e}")
        return False


def setup_alert_handlers():
    """配置告警处理器 - 默认所有告警发送到飞书机器人"""
    # 飞书告警处理器（默认启用）
    def feishu_alert_handler(alert_data):
        """feishu_alert_handler。

        参数说明：
        :param alert_data: 参数 alert_data
        :return: 返回处理结果。
        """
        level = alert_data.get("level", "INFO")
        message = alert_data.get("message", "")
        metadata = alert_data.get("metadata", {})
        # 构建完整消息
        full_message = f"**告警级别**: {level}\n**消息内容**: {message}"
        if metadata:
            full_message += f"\n**详情**: {metadata}"

        # 发送到飞书机器人
        send_to_feishu_bot(full_message, level)

    # 邮件告警处理器（作为备选）
    def email_alert_handler(alert_data):
        """email_alert_handler。

        参数说明：
        :param alert_data: 参数 alert_data
        :return: 返回处理结果。
        """
        logger = logging.getLogger("alert.email")
        logger.info(f"邮件告警: {alert_data['message']}")

    # Webhook告警处理器（作为备选）
    def webhook_alert_handler(alert_data):
        """webhook_alert_handler。

        参数说明：
        :param alert_data: 参数 alert_data
        :return: 返回处理结果。
        """
        logger = logging.getLogger("alert.webhook")
        logger.info(f"Webhook告警: {alert_data['message']}")

    # 默认启用飞书告警（优先级最高）
    alert_manager.add_handler(feishu_alert_handler)
    alert_manager.add_handler(email_alert_handler)
    alert_manager.add_handler(webhook_alert_handler)
    return alert_manager
