# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""运维定时任务与作业调度路由"""

from fastapi import APIRouter, Depends
from app.core.response import success_response
from app.core.security import get_current_user

ROUTE_PREFIX = "/ops-jobs"
ROUTE_TAGS = ["运维调度"]

router = APIRouter()


@router.get("", include_in_schema=False)
@router.get("/")
def list_ops_jobs(current_user=Depends(get_current_user)):
    """获取系统运维与定时任务调度作业列表"""
    jobs = [
        {"id": "job-1", "name": "SEO 矩阵定时推送", "cron": "0 2 * * *", "status": "running", "type": "定时同步"},
        {"id": "job-2", "name": "询盘智能分发清洗", "cron": "*/30 * * * *", "status": "completed", "type": "数据处理"},
        {"id": "job-3", "name": "租户 Token 余额巡检", "cron": "0 * * * *", "status": "running", "type": "风控巡检"},
        {"id": "job-4", "name": "系统日志归档备份", "cron": "0 3 * * *", "status": "completed", "type": "数据维护"},
    ]
    return success_response(data={"items": jobs, "total": len(jobs)})
