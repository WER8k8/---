# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""UB-06：飞轮 BFF 层统一脱敏序列化。"""

from __future__ import annotations

from typing import Any

from app.services.hermes.brand_guard import sanitize_public_data
from app.services.ubrain.deerflow_job_service import serialize_job, serialize_job_with_steps


def public_serialize_job(job: Any, *, with_steps: bool = False) -> dict[str, Any]:
    """public_serialize_job。

    参数说明：
    :param job: 参数 job
    :param with_steps: 参数 with_steps
    :return: 返回处理结果。
    """
    raw = serialize_job_with_steps(job) if with_steps else serialize_job(job)
    return sanitize_public_data(raw)
