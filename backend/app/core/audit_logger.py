# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
全系统安全与脱敏审计日志 (Audit Logger)。
双栈存证：写防篡改日志 (audit.jsonl) 并脱敏高危 PII。
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

# 定义防篡改日志存放位置
LOG_DIR = Path(os.getenv("AUDIT_LOG_DIR", r"C:\Users\Administrator\.gemini\antigravity\logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_LOG_FILE = LOG_DIR / "audit.jsonl"


def mask_pii(text: str) -> str:
    """脱敏：隐藏手机号中间4位、隐藏邮箱用户名"""
    if not isinstance(text, str):
        return text
    # 手机号脱敏 (e.g., +1 555-0199 -> +1 555-****, 13812345678 -> 138****5678)
    text = re.sub(r'(\+?\d{1,3}[-\s]?)?(\d{3})\d{4}(\d{4})', r'\1\2****\3', text)
    # 邮箱脱敏 (e.g., test@example.com -> t***@example.com)
    text = re.sub(r'\b([a-zA-Z0-9])([a-zA-Z0-9._%+-]*)(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', r'\1***\3', text)
    return text


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """递归脱敏字典"""
    sanitized = {}
    for k, v in data.items():
        if isinstance(v, str):
            sanitized[k] = mask_pii(v)
        elif isinstance(v, dict):
            sanitized[k] = sanitize_dict(v)
        elif isinstance(v, list):
            sanitized[k] = [mask_pii(item) if isinstance(item, str) else (sanitize_dict(item) if isinstance(item, dict) else item) for item in v]
        else:
            sanitized[k] = v
    return sanitized


class AuditLogger:
    @staticmethod
    def log_event(event_type: str, actor: str, action: str, details: Dict[str, Any] = None):
        """记录一条脱敏的安全审计日志"""
        safe_details = sanitize_dict(details or {})
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "actor": actor,
            "action": action,
            "details": safe_details
        }
        try:
            with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
