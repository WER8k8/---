# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""应用启动引导模块 — 从 main.py lifespan 中提取调度器启动逻辑，保持行为一致。

所有调度器启动失败不阻塞主进程，仅在日志中记录警告。
每个调度器对应一个注册项，包含：启用条件、工厂函数、启动参数、停止引用。
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger("uj-admin.bootstrap")


# ---------------------------------------------------------------------------
# 调度器注册表（数据驱动，替代 main.py 中散落的 if/else 块）
# ---------------------------------------------------------------------------

class SchedulerSlot:
    """单个调度器的元数据 + 运行时引用"""
    __slots__ = (
        "name", "enabled", "factory",
        "start_kwargs", "post_start",
        "instance", "stopped",
    )
    def __init__(
        self,
        name: str,
        enabled: Callable[[], bool],
        factory: Callable[[], Any],
        start_kwargs: dict[str, Any] | None = None,
        post_start: Callable[[Any], None] | None = None,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param name: 参数 name
        :param enabled: 参数 enabled
        :param factory: 参数 factory
        :param start_kwargs: 参数 start_kwargs
        :param post_start: 参数 post_start
        :return: 返回处理结果。
        """
        self.name = name
        self.enabled = enabled
        self.factory = factory
        self.start_kwargs = start_kwargs or {}
        self.post_start = post_start
        self.instance: Any = None
        self.stopped = False


def _make_scheduler_registry(settings_) -> list[SchedulerSlot]:
    """延迟构造注册表（避免导入期触发 settings 副作用）。"""
    return (
        _make_scheduler_registry_group_a(settings_)
        + _make_scheduler_registry_group_b(settings_)
    )


def _make_scheduler_registry_group_a(settings_) -> list[SchedulerSlot]:
    """注册表分组 A：基础调度器与 Hermes 营收 / 持久化调度器。"""
    return [
        # ── 关键词排名调度 ──
        SchedulerSlot(
            name="rank_scheduler",
            enabled=lambda: bool(settings_.RANK_SCHEDULER_ENABLED),
            factory=lambda: _import_scheduler("app.services.rank_scheduler", "rank_scheduler"),
            start_kwargs={},
            post_start=lambda inst: _post_start_rank_sync(inst, settings_),
        ),
        # ── AI 场景健康检查 ──
        SchedulerSlot(
            name="scenario_health_scheduler",
            enabled=lambda: bool(settings_.AI_SCENARIO_HEALTH_SCHEDULER_ENABLED),
            factory=lambda: _import_scheduler(
                "app.services.scenario_health_scheduler", "scenario_health_scheduler"
            ),
            start_kwargs={
                "check_hour": settings_.AI_SCENARIO_HEALTH_CHECK_HOUR,
                "check_minute": settings_.AI_SCENARIO_HEALTH_CHECK_MINUTE,
                "interval_hours": settings_.AI_SCENARIO_HEALTH_INTERVAL_HOURS,
            },
        ),
        # ── 媒体清理调度 ──
        SchedulerSlot(
            name="media_cleanup_scheduler",
            enabled=lambda: bool(settings_.MEDIA_CLEANUP_SCHEDULER_ENABLED),
            factory=lambda: _import_scheduler(
                "app.services.media_cleanup_scheduler", "media_cleanup_scheduler"
            ),
            start_kwargs={"interval_minutes": settings_.MEDIA_CLEANUP_INTERVAL_MINUTES},
        ),
        # ── NVIDIA 客户探测 ──
        SchedulerSlot(
            name="nvidia_probe_scheduler",
            enabled=lambda: bool(settings_.nvidia_customer_probe_scheduler_active),
            factory=lambda: _import_scheduler(
                "app.services.nvidia_customer_probe_scheduler",
                "nvidia_customer_probe_scheduler",
            ),
            start_kwargs={"bootstrap_probe": True},
        ),
        # ── Hermes 站点巡检 ──
        SchedulerSlot(
            name="hermes_patrol_scheduler",
            enabled=lambda: bool(settings_.hermes_site_patrol_scheduler_active),
            factory=lambda: _import_scheduler(
                "app.services.hermes.site_patrol_scheduler",
                "hermes_site_patrol_scheduler",
            ),
            start_kwargs={"bootstrap": True},
        ),
        # ── Greedy 营收循环 ──
        SchedulerSlot(
            name="greedy_revenue_scheduler",
            enabled=lambda: bool(settings_.greedy_revenue_loop_scheduler_active),
            factory=lambda: _import_scheduler(
                "app.services.hermes.greedy_revenue_loop_scheduler",
                "greedy_revenue_loop_scheduler",
            ),
            start_kwargs={"bootstrap": True},
        ),
        # ── Greedy 持久化 7×24 ──
        SchedulerSlot(
            name="greedy_endurance_scheduler",
            enabled=lambda: bool(settings_.greedy_endurance_scheduler_active),
            factory=lambda: _import_scheduler(
                "app.services.hermes.greedy_endurance_scheduler",
                "greedy_endurance_scheduler",
            ),
            start_kwargs={},
        ),
    ]


def _make_scheduler_registry_group_b(settings_) -> list[SchedulerSlot]:
    """注册表分组 B：Greedy 生存摘要 / Ops 自动驾驶 / Deerflow / 贸易情报 / Paperclip 心跳。"""
    return [
        # ── Greedy 生存摘要 ──
        SchedulerSlot(
            name="greedy_survival_digest_scheduler",
            enabled=lambda: bool(settings_.greedy_survival_digest_scheduler_active),
            factory=lambda: _import_scheduler(
                "app.services.hermes.greedy_survival_digest_scheduler",
                "greedy_survival_digest_scheduler",
            ),
            start_kwargs={},
        ),
        # ── Ops 自动驾驶 ──
        SchedulerSlot(
            name="ops_autopilot_scheduler",
            enabled=lambda: bool(settings_.ops_autopilot_dev_active),
            factory=lambda: _import_scheduler(
                "app.services.ops_autopilot_scheduler",
                "ops_autopilot_scheduler",
            ),
            start_kwargs={},
        ),
        # ── Deerflow ──
        SchedulerSlot(
            name="deerflow_scheduler",
            enabled=lambda: bool(settings_.deerflow_scheduler_active),
            factory=lambda: _import_scheduler(
                "app.services.ubrain.deerflow_scheduler",
                "deerflow_scheduler",
            ),
            start_kwargs={"bootstrap": True},
        ),
        # ── 贸易情报 ──
        SchedulerSlot(
            name="trade_intel_scheduler",
            enabled=lambda: bool(settings_.trade_intel_scheduler_active),
            factory=lambda: _import_scheduler(
                "app.services.trade_intel_scheduler",
                "trade_intel_scheduler",
            ),
            start_kwargs={"bootstrap": True},
        ),
        # ── Paperclip 心跳调度 ──
        SchedulerSlot(
            name="paperclip_heartbeat",
            enabled=lambda: bool(settings_.REDIS_ENABLED or True),
            factory=lambda: _import_scheduler(
                "app.services.paperclip.heartbeat_engine",
                "paperclip_heartbeat_engine",
            ),
            start_kwargs={},
        ),
    ]


# ---------------------------------------------------------------------------
# 内部助手
# ---------------------------------------------------------------------------

def _import_scheduler(module_path: str, attr_name: str) -> Any:
    """动态导入调度器实例（失败不阻塞）。"""
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


def _post_start_rank_sync(inst: Any, settings_) -> None:
    """RankScheduler 启动后同步关键词。"""
    try:
        from app.core.database import SessionLocal
        from app.services.seo.rank_scheduler_ops import sync_keywords_from_db
        db = SessionLocal()
        try:
            sync_report = sync_keywords_from_db(db)
            logger.info(
                "RankScheduler keyword sync: %s items",
                sync_report.get("synced_items", 0),
            )
        finally:
            db.close()
    except Exception as exc:
        logger.warning("RankScheduler keyword sync skipped: %s", exc)


# ---------------------------------------------------------------------------
# 公开 API：启动 / 停止所有调度器
# ---------------------------------------------------------------------------

async def bootstrap_schedulers(settings_) -> dict[str, SchedulerSlot]:
    """按注册表启动所有启用调度器。返回 {name: slot} 供 shutdown 使用。"""
    slots = _make_scheduler_registry(settings_)
    started: dict[str, SchedulerSlot] = {}
    for slot in slots:
        if not slot.enabled():
            continue
        try:
            slot.instance = slot.factory()
            slot.instance.start(**slot.start_kwargs)
            if slot.post_start:
                slot.post_start(slot.instance)
            started[slot.name] = slot
            logger.info("Scheduler started: %s", slot.name)
        except Exception as exc:
            logger.warning("Scheduler '%s' failed to start: %s", slot.name, exc)

    return started


async def shutdown_schedulers(slots: dict[str, SchedulerSlot]) -> None:
    """优雅停止所有已启动的调度器。"""
    for name, slot in slots.items():
        if slot.stopped or slot.instance is None:
            continue
        try:
            slot.instance.stop()
            slot.stopped = True
            logger.info("Scheduler stopped: %s", name)
        except Exception:
            logger.warning("Scheduler '%s' failed to stop gracefully", name)


# ---------------------------------------------------------------------------
# 按需启动的额外引导（非调度器）
# ---------------------------------------------------------------------------

async def bootstrap_seed_data(settings_) -> None:
    """种子数据（幂等写入）。"""
    try:
        from app.db.seed import seed_super_admin
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            seed_super_admin(db)
        finally:
            db.close()
    except Exception:
        pass


async def bootstrap_backup_service(settings_) -> None:
    """自动备份服务。"""
    try:
        from app.services.auto_backup import backup_service
        backup_service.start()
    except Exception:
        pass


async def bootstrap_greedy_publish_tenant(settings_) -> None:
    """Greedy 发布租户自动创建。"""
    if not (settings_.greedy_bootstrap_on_startup and settings_.HERMES_GREEDY_AVATAR_ENABLED):
        return
    if (settings_.HERMES_GREEDY_PUBLISH_TENANT_ID or "").strip():
        return
    try:
        from app.core.database import SessionLocal
        from app.services.hermes.greedy_production_readiness_service import (
            bootstrap_publish_platform_accounts,
            ensure_greedy_publish_tenant,
        )
        sdb = SessionLocal()
        try:
            tenant = ensure_greedy_publish_tenant(sdb)
            if tenant.get("tenant_id"):
                bootstrap_publish_platform_accounts(
                    sdb,
                    tenant_id=str(tenant["tenant_id"]),
                    locale=str(settings_.HERMES_GREEDY_DEFAULT_LOCALE or "global"),
                )
                logger.info("Greedy publish tenant bootstrap: %s", tenant.get("tenant_id"))
        finally:
            sdb.close()
    except Exception as exc:
        logger.warning("Greedy publish tenant bootstrap skipped: %s", exc)


async def bootstrap_storage_check(settings_) -> None:
    """平台存储容量启动检查。"""
    try:
        from app.services.platform_storage_provision_service import (
            production_storage_startup_message,
        )
        storage_warn = production_storage_startup_message()
        if storage_warn:
            logger.warning(storage_warn)
    except Exception as exc:
        logger.debug("Platform storage startup check skipped: %s", exc)
