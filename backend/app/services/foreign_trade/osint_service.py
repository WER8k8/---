# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""OSINT 背调 API 封装。"""

from __future__ import annotations

import asyncio
from typing import Any

from app.services.foreign_trade.osint.orchestrator import osint_full_check


def run_osint_check(
    target: str,
    *,
    include_sanctions: bool = True,
    include_tech_stack: bool = True,
    include_linkedin: bool = True,
) -> dict[str, Any]:
    """同步入口：六层 OSINT 尽职调查。"""
    return asyncio.run(
        osint_full_check(
            target,
            include_sanctions=include_sanctions,
            include_tech_stack=include_tech_stack,
            include_linkedin=include_linkedin,
        )
    )
