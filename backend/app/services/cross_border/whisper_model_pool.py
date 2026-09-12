"""Whisper 模型单例预热（Worker 启动后复用）。"""

from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)

_model: Any = None
_lock = threading.Lock()
_warmed = False


def get_faster_whisper_model():
    """进程内单例；多任务共享，避免重复加载。"""
    global _model
    with _lock:
        if _model is None:
            from faster_whisper import WhisperModel
            logger.info("loading faster-whisper base model (singleton)")
            _model = WhisperModel("base", device="cpu", compute_type="int8")
        return _model


def warm_whisper_model() -> bool:
    """可选预热；失败不阻断。"""
    global _warmed
    try:
        get_faster_whisper_model()
        _warmed = True
        return True
    except Exception as exc:
        logger.warning("whisper warm failed: %s", exc)
        return False


def whisper_warmed() -> bool:
    """实现 whisperwarmed 的功能。
    
    :return: 返回 bool 结果
    """
    return _warmed
