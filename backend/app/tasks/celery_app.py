# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "uj_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.seo_tasks",
        "app.tasks.geo_tasks",
        "app.tasks.ubrain_tasks",
        "app.tasks.trade_intel_tasks",
        "app.tasks.cross_border_tasks",
        "app.tasks.billing_tasks",
        "app.tasks.churn_tasks",
        "app.tasks.sla_tasks",
        "app.tasks.quote_wake_tasks",
        "app.tasks.company_autofill_tasks",
        "app.tasks.deerflow_tasks",
        "app.tasks.orchestration_tasks",
        "app.tasks.ops_scheduler_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "check-keyword-rankings": {
            "task": "app.tasks.seo_tasks.check_all_keyword_rankings",
            "schedule": 86400.0,
        },
        "run-periodic-site-audit": {
            "task": "app.tasks.seo_tasks.run_site_audit",
            "schedule": 604800.0,
        },
        "geo-tech-radar-daily": {
            "task": "geo_tech_radar_daily",
            "schedule": crontab(hour=8, minute=0),
        },
        "geo-rank-guard-check": {
            "task": "geo_rank_guard_check",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        "geo-competitor-monitor": {
            "task": "geo_competitor_monitor",
            "schedule": crontab(hour=9, minute=0),
        },
        "deerflow-scheduled-daily": {
            "task": "deerflow_scheduled_daily",
            "schedule": crontab(hour=7, minute=30),
        },
        "deerflow-run-pending-tenant": {
            "task": "deerflow_run_pending",
            "schedule": 180.0,
            "kwargs": {"limit": 8, "lane": "tenant"},
            "options": {"max_instances": 1},  # ORCH-02: 防止Beat模式压缩堆积（180秒interval在Beat下可能被合并为每小时）
        },
        "seo-inclusion-recheck-daily": {
            "task": "app.tasks.seo_tasks.recheck_inclusion_daily",
            "schedule": crontab(hour=5, minute=30),
            "kwargs": {"limit": 200},
        },
        "flywheel-feedback-sync-daily": {
            "task": "flywheel_feedback_sync_daily",
            "schedule": crontab(hour=6, minute=0),
        },
        "seo-research-hints-sync": {
            "task": "seo_research_hints_sync",
            "schedule": crontab(hour=4, minute=0),
        },
        "trade-intel-refresh-weekly": {
            "task": "trade_intel_refresh_weekly",
            "schedule": crontab(hour=3, minute=30, day_of_week=1),
        },
        "meter-events-aggregate-hourly": {
            "task": "app.tasks.billing_tasks.aggregate_meter_events",
            "schedule": crontab(minute=5),
        },
        # P1-1：租户到期催续提醒（每日 09:00 低峰；幂等按到期日去重，不重发）
        "subscription-dunning-daily": {
            "task": "app.tasks.billing_tasks.subscription_dunning_daily",
            "schedule": crontab(hour=9, minute=0),
            "kwargs": {"within_days": 14},
            "options": {"max_instances": 1},
        },
        # P1-3: 流失预警自动动作（每日 09:30 扫描高风险租户，建跟进任务 + 飞书/邮件通知）。
        "churn-auto-action-daily": {
            "task": "app.tasks.churn_tasks.churn_auto_action_daily",
            "schedule": crontab(hour=9, minute=30),
            "kwargs": {"min_risk": "high", "dry_run": False},
            "options": {"max_instances": 1},
        },
        # P1-7: 跟进 SLA 逾期主动告警（每日 10:00 扫全量跟单卡，逾期建任务+通知，按日幂等）。
        "sla-overdue-alert-daily": {
            "task": "app.tasks.sla_tasks.sla_overdue_alert_daily",
            "schedule": crontab(hour=10, minute=0),
            "kwargs": {"dry_run": False},
            "options": {"max_instances": 1},
        },
        # P1-6: 报价未回访唤醒（每日 10:30；报价≥3天无跟进或已过期 → 建任务+通知）。
        "quote-followup-wake-daily": {
            "task": "app.tasks.quote_wake_tasks.quote_followup_wake_daily",
            "schedule": crontab(hour=10, minute=30),
            "kwargs": {"idle_days": 3, "dry_run": False},
            "options": {"max_instances": 1},
        },
        # P1-8 收尾: 询盘域名→公司档案 兜底回填（每日 11:00；创建钩子是 best-effort，需要每日补齐）。
        "company-autofill-backfill-daily": {
            "task": "app.tasks.company_autofill_tasks.company_autofill_backfill_daily",
            "schedule": crontab(hour=11, minute=0),
            "kwargs": {"limit": 5000},
            "options": {"max_instances": 1},
        },
        # PC-04: 平台账号会话巡检（每日一次，低峰时段）。纯 DB 判定，不触网。
        "platform-session-patrol-daily": {
            "task": "app.tasks.seo_tasks.patrol_platform_sessions_daily",
            "schedule": crontab(
                hour=settings.PLATFORM_SESSION_PATROL_HOUR,
                minute=settings.PLATFORM_SESSION_PATROL_MINUTE,
            ),
            "options": {"max_instances": 1},
        },
    },
    task_routes={
        "deerflow_scheduled_daily": {"queue": "deerflow"},
        "deerflow_run_pending": {"queue": "deerflow"},
        "trade_intel_refresh_weekly": {"queue": "default"},
        "cross_border.run_job": {"queue": "cross_border"},
    },
)
