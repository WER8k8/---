# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from app.services.platforms.wechat import WeChatPublisher, WeChatPublisherAdapter
from app.services.platforms.zhihu import ZhihuPublisher, ZhihuPublisherAdapter
from app.services.platforms.toutiao import ToutiaoPublisher, ToutiaoPublisherAdapter
from app.services.platforms.baijiahao import BaijiahaoPublisher, BaijiahaoPublisherAdapter
from app.services.platforms.csdn import CSDNPublisher, CSDNPublisherAdapter
from app.services.platforms.weibo import WeiboPublisher, WeiboPublisherAdapter
from app.services.platforms.xiaohongshu import XiaohongshuPublisher, XiaohongshuPublisherAdapter
from app.services.platforms.b2b_platform_inbox_hub import B2BPlatformInboxHub

__all__ = [
    "WeChatPublisher", "WeChatPublisherAdapter",
    "ZhihuPublisher", "ZhihuPublisherAdapter",
    "ToutiaoPublisher", "ToutiaoPublisherAdapter",
    "BaijiahaoPublisher", "BaijiahaoPublisherAdapter",
    "CSDNPublisher", "CSDNPublisherAdapter",
    "WeiboPublisher", "WeiboPublisherAdapter",
    "XiaohongshuPublisher", "XiaohongshuPublisherAdapter",
    "B2BPlatformInboxHub",
]
