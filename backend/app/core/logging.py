# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""日志模块 — app.core.logging_config 的兼容层。"""

from app.core.logging_config import LogConfig

def get_logger(name: str):
    """获取日志实例 — 兼容性封装。"""
    return LogConfig.get_logger(name)

import logging
logger = logging.getLogger("app")
