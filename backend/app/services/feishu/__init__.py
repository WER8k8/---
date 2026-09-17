# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from app.services.feishu.cards import FeishuCardBuilder
from app.services.feishu.client import FeishuClient
from app.services.feishu.handlers import FeishuMessageHandler

feishu_client = FeishuClient()
card_builder = FeishuCardBuilder()
message_handler = FeishuMessageHandler(feishu_client, card_builder)

__all__ = [
    "FeishuClient",
    "FeishuCardBuilder",
    "FeishuMessageHandler",
    "feishu_client",
    "card_builder",
    "message_handler",
]
