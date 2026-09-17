# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
try:
    from app.workers.publish_worker import process_pending_tasks
    __all__ = ["process_pending_tasks"]
except ImportError:
    # arq not available
    __all__ = []
