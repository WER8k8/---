#!/usr/bin/env python3
"""
import logging

logger = logging.getLogger(__name__)

定时发送TRAE与Lingma沟通记录到飞书
每分钟发送一次
"""

from app.core.logging_config import send_to_feishu_bot
from app.core.config import settings
import json
import os
import sys
import time
import urllib.request
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def send_to_feishu_webhook(webhook_url, message):
    """通过飞书机器人Webhook发送消息"""
    try:
        # 构建飞书消息格式
        data = {"msg_type": "text", "content": {"text": message}}

        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("code") == 0
    except Exception as e:
        logger.info('❌ Webhook发送失败: {e}', e)
        return False


def load_communication_log():
    """加载沟通记录文件"""
    log_path = os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)))),
        "与Lingma工作沟通记录.md")

    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            return f.read()
    return "暂无沟通记录"


def format_communication_summary():
    """格式化沟通记录摘要"""
    log_content = load_communication_log()

    # 提取关键信息
    lines = log_content.split("\n")
    summary_lines = []

    for line in lines[:50]:  # 取前50行作为摘要
        if line.startswith("##") or line.startswith(
                "###") or line.startswith("- ") or line.startswith("| "):
            summary_lines.append(line)

    return "\n".join(summary_lines)


def send_periodically(interval_minutes=1):
    """定时发送沟通记录"""
    interval_seconds = interval_minutes * 60

    # 检查飞书配置状态
    feishu_configured = False
    feishu_webhook_url = ""

    # 优先使用Webhook方式（更简单）
    if hasattr(settings, "FEISHU_WEBHOOK_URL") and settings.FEISHU_WEBHOOK_URL:
        if settings.FEISHU_WEBHOOK_URL != "your-webhook-url-here":
            feishu_configured = True
            feishu_webhook_url = settings.FEISHU_WEBHOOK_URL
    # 其次使用AppID/AppSecret方式
    elif settings.FEISHU_APP_ID and settings.FEISHU_APP_SECRET:
        if (
            settings.FEISHU_APP_ID != "your-feishu-app-id-here"
            and settings.FEISHU_APP_SECRET != "your-feishu-app-secret-here"
        ):
            feishu_configured = True

    logger.info('🚀 启动定时发送任务，每分钟发送一次沟通记录到飞书')
    logger.info("📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logger.info(
        f"🔧 飞书通知状态: {'已启用' if settings.FEISHU_NOTIFICATION_ENABLED else '已禁用'}")
    logger.info("⚙️ 飞书配置状态: {'✅ 已配置' if feishu_configured else '⚠️ 未配置（模拟模式）'}", '✅ 已配置' if feishu_configured else '⚠️ 未配置（模拟模式）')
    logger.info(
        f"🔗 发送方式: {'Webhook' if feishu_webhook_url else 'API' if feishu_configured else '模拟'}")
    logger.info('"=" * 60')

    if not feishu_configured:
        logger.info('💡 提示：飞书配置尚未完成，当前运行在模拟模式')
        logger.info('   最简单方式：在 backend/.env 中配置 FEISHU_WEBHOOK_URL')
        logger.info('   获取方式：飞书群设置 -> 群机器人 -> 添加机器人 -> 复制Webhook地址')
        logger.info('"=" * 60')

    while True:
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 构建消息内容
            summary = format_communication_summary()
            message = f"📨 TRAE与Lingma工作沟通记录\n\n📅 发送时间: {current_time}\n\n{summary[:1500]}"

            if feishu_configured:
                if feishu_webhook_url:
                    # 使用Webhook发送
                    result = send_to_feishu_webhook(
                        feishu_webhook_url, message)
                else:
                    # 使用API发送
                    result = send_to_feishu_bot(message, "INFO")

                if result:
                    logger.info('✅ [{current_time}] 沟通记录发送成功', current_time)
                else:
                    logger.info('⚠️ [{current_time}] 发送失败', current_time)
            else:
                # 模拟发送模式 - 显示要发送的内容
                logger.info('📤 [{current_time}] 模拟发送（配置完成后将发送到飞书）', current_time)
                logger.info('"-" * 40')
                logger.info('发送内容预览:\\n{message[:500]}...', message[:500])
                logger.info('"-" * 40')

            # 等待指定时间
            time.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info('\\n⏹️ 用户终止任务')
            break
        except Exception as e:
            logger.info("❌ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 发送异常: {e}", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e)
            time.sleep(interval_seconds)


if __name__ == "__main__":
    send_periodically(interval_minutes=1)
