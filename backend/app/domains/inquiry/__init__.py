# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""询盘管理领域 — stub（待从 routes/inquiries.py 迁移）"""
from fastapi import APIRouter
from app.domains.base import DomainModule

router = APIRouter(tags=["询盘管理"])

class InquiryDomain(DomainModule):
    name = "inquiry"
    label = "询盘管理"
    @property
    def router(self):
        """router。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return router

__all__ = ["InquiryDomain"]