# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
性能告警触发器
当性能下降超过预算时，触发告警通知
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any

from app.performance.models import PerformanceBudget, BudgetSeverity
from app.performance.monitor import LighthouseResult
from app.core.cache import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class PerformanceAlertTrigger:
    """
    性能告警触发器
    当性能下降超过预算时，触发告警
    """
    def __init__(self):
        """初始化告警触发器"""
        self.enabled = True
        logger.info("✅ PerformanceAlertTrigger initialized")
    
    async def check_and_trigger(
        self,
        url: str,
        device: str,
        result: LighthouseResult,
        warnings: List[str],
        errors: List[str]
    ) -> Dict[str, Any]:
        """
        检查并触发告警
        
        Args:
            url: 审计的URL
            device: 设备类型
            result: Lighthouse结果
            warnings: 警告列表
            errors: 错误列表
            
        Returns:
            告警触发结果
        """
        try:
            logger.info(f"🔔 检查性能告警: {url} ({device})")
            alert_triggered = False
            alert_level = "info"
            alert_message = ""
            # 1. 判断告警级别
            if errors:
                alert_level = "error"
                alert_message = f"性能严重下降：{len(errors)}个指标超过预算"
                alert_triggered = True
            elif warnings:
                alert_level = "warning"
                alert_message = f"性能轻微下降：{len(warnings)}个指标超过预算"
                alert_triggered = True
            
            # 2. 检查趋势（与昨天对比）
            trend_alert = await self._check_trend(url, device, result)
            if trend_alert:
                alert_triggered = True
                alert_level = "warning"
                alert_message += f"；{trend_alert}"
            
            # 3. 发送告警通知
            if alert_triggered:
                await self._send_alert_notification(
                    url, device, result, alert_level, alert_message
                )
            
            result = {
                "alert_triggered": alert_triggered,
                "alert_level": alert_level,
                "alert_message": alert_message,
                "warnings": warnings,
                "errors": errors,
            }
            logger.info(f"✅ 告警检查完成: triggered={alert_triggered}, level={alert_level}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 告警检查失败: {e}", exc_info=True)
            return {
                "alert_triggered": False,
                "alert_level": "error",
                "alert_message": f"告警检查失败: {str(e)}",
                "warnings": [],
                "errors": []
            }
    
    async def _check_trend(
        self,
        url: str,
        device: str,
        current_result: LighthouseResult
    ) -> Optional[str]:
        """
        检查性能趋势（与昨天对比）
        
        Args:
            url: URL
            device: 设备类型
            current_result: 当前结果
            
        Returns:
            趋势告警消息（如果没有问题则返回None）
        """
        if not redis_client:
            return None
        
        try:
            # 获取昨天的性能数据
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
            cache_key = f"perf:{url}:{device}:{yesterday}"
            data = redis_client.get(cache_key)
            if not data:
                return None  # 没有历史数据
            
            yesterday_data = json.loads(data)
            # 比较LCP（最重要的指标）
            yesterday_lcp = yesterday_data.get("lcp", 0)
            current_lcp = current_result.lcp
            if yesterday_lcp > 0 and current_lcp > yesterday_lcp * 1.2:
                # LCP恶化超过20%
                return f"LCP恶化{(current_lcp - yesterday_lcp) / yesterday_lcp * 100:.1f}%"
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 趋势检查失败: {e}", exc_info=True)
            return None
    
    async def _send_alert_notification(
        self,
        url: str,
        device: str,
        result: LighthouseResult,
        level: str,
        message: str
    ) -> bool:
        """
        发送告警通知
        
        Args:
            url: URL
            device: 设备类型
            result: Lighthouse结果
            level: 告警级别
            message: 告警消息
            
        Returns:
            是否发送成功
        """
        try:
            # 1. 记录到日志
            logger.warning(f"🚨 性能告警 [{level.upper()}]: {url} - {message}")
            # 2. 发送到飞书（如果配置了）
            if settings.FEISHU_WEBHOOK_URL:
                await self._send_feishu_notification(
                    url, device, result, level, message
                )
            
            # 3. 保存到数据库（简化：只记录到日志）
            logger.info(f"✅ 告警通知已发送: {url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 告警通知发送失败: {e}", exc_info=True)
            return False
    
    async def _send_feishu_notification(
        self,
        url: str,
        device: str,
        result: LighthouseResult,
        level: str,
        message: str
    ) -> bool:
        """发送飞书通知"""
        import httpx
        color_map = {"info": "blue", "warning": "yellow", "error": "red"}
        color = color_map.get(level, "yellow")
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": f"🚨 性能告警 - {url}"},
                    "template": color,
                },
                "elements": [
                    {"tag": "div", "text": {"tag": "lark_md", "content": f"**设备**: {device}\n**级别**: {level.upper()}\n**消息**: {message}"}},
                    {"tag": "div", "text": {"tag": "lark_md", "content": f"**LCP**: {result.lcp:.0f}ms\n**FCP**: {result.fcp:.0f}ms\n**CLS**: {result.cls:.3f}\n**评分**: {result.score:.1f}"}},
                    {"tag": "hr"},
                    {"tag": "note", "elements": [{"tag": "plain_text", "content": "优丁建材 · 性能监控中心"}]},
                ],
            },
        }
        try:
            with httpx.Client(timeout=10) as client:
                client.post(settings.FEISHU_WEBHOOK_URL, json=payload)
            return True
        except Exception:
            return False


# 导出
__all__ = ["PerformanceAlertTrigger"]
