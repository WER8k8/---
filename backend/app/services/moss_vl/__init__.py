# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""OpenMOSS / MOSS-VL 完整多模态开源引擎包。

提供离线视频全景推理、Real-Time 流式会话、XRoPE 时空三维位置编码、
官方权重/量化加载器以及仓库同步工具。
"""

from app.services.moss_vl.realtime_session import MossRealtimeSession, create_realtime_session
from app.services.moss_vl.offline_inference import OfflineInferenceEngine
from app.services.moss_vl.xrope_spatial_temporal import XRoPEEmbedding
from app.services.moss_vl.model_loader import MossVLModelLoader
from app.services.moss_vl.repo_syncer import MossRepoSyncer

__all__ = [
    "MossRealtimeSession",
    "create_realtime_session",
    "OfflineInferenceEngine",
    "XRoPEEmbedding",
    "MossVLModelLoader",
    "MossRepoSyncer",
]
