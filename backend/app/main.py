"""FastAPI主应用"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.api import router as api_router
from app.core.config import settings

# 延迟注册全部业务路由：必须在整条 app 包导入完成后触发，
# 规避 app/api/v1/routes/__init__ 执行期的循环 import，否则 146 个业务路由全部丢失。
from app.api import register_routes as _register_api_routes
_register_api_routes()
from app.core.performance_middleware import PerformanceMiddleware
from app.core.no_fake_delivery import FakeDeliveryViolation, NotConfiguredError
from app.core.no_fake_delivery_middleware import NoFakeDeliveryResponseMiddleware
from app.core.response import APIResponse
from app.core.security_headers import (APISecurityHeadersMiddleware,
                                       SecurityHeadersMiddleware)
from app.core.security_middleware import (RateLimitMiddleware,
                                          SecurityMiddleware)
from app.core.csrf_middleware import CSRFMiddleware
from app.core.tenant_middleware import TenantMiddleware
from app.core.request_id_middleware import RequestIdMiddleware
from app.core.unify_response_middleware import UnifyV1ApiResponseMiddleware
from app.core.brand_guard_middleware import BrandGuardResponseMiddleware
from app.core.waf import setup_waf
from app.db.session import init_db
from app.api.v1.routes.metrics import router as metrics_router

# 注册领域事件处理器
import app.core.events  # noqa: F401

logger = logging.getLogger("uj-admin")

# Sentry 异常监控（可选，通过环境变量 SENTRY_DSN 启用）
try:
    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    if SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=os.getenv("ENVIRONMENT", "production"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_RATE", "0.1")),
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        )
        logger.info(f"Sentry initialized: env={os.getenv('ENVIRONMENT', 'production')}")
except ImportError:
    pass  # sentry_sdk 未安装时静默跳过


def _lifespan_init_core():
    """启动前基础初始化：CLI 路径、数据库、安全校验、种子、备份。"""
    # Windows 开发：补全 ffmpeg 等 CLI 路径（避免 WinGet symlink 对 uvicorn 不可见）
    try:
        from app.core.executable_resolver import bootstrap_executable_env
        bootstrap_executable_env()
    except Exception:
        pass

    # 启动时初始化数据库
    init_db()
    # RLS 试点表挂载（默认关；仅在 PG + RLS_PILOT_ENABLED 时生效）
    try:
        from app.core.database import mount_rls_pilot_if_enabled
        mount_rls_pilot_if_enabled()
    except Exception:
        pass
    # SECURITY: 生产环境 DEBUG=True 时阻止启动
    if settings.ENVIRONMENT == "production" and settings.DEBUG:
        logger.error(
            "[SECURITY] 生产环境禁止 DEBUG=True！"
            "限流中间件已跳过、Swagger 文档已暴露！"
            "请设置 DEBUG=False 后重启。"
        )
        raise RuntimeError("生产环境禁止 DEBUG=True")

    # 自动运行种子数据（幂等）
    try:
        from app.db.seed import seed_super_admin
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            seed_super_admin(db)
        finally:
            db.close()
    except Exception:
        pass  # 种子失败不阻塞启动

    # 自动启动数据库备份（每日凌晨3点）
    try:
        from app.services.auto_backup import backup_service
        backup_service.start()
    except Exception:
        pass


def _lifespan_start_basic_schedulers():
    """启动基础调度器：关键词排名 / 场景健康 / 媒体清理。"""
    rank_scheduler = None
    scenario_health_scheduler = None
    media_cleanup_scheduler = None
    if settings.RANK_SCHEDULER_ENABLED:
        try:
            from app.services.rank_scheduler import rank_scheduler as _rank_scheduler
            rank_scheduler = _rank_scheduler
            rank_scheduler.start()
            try:
                from app.core.database import SessionLocal
                from app.services.seo.rank_scheduler_ops import sync_keywords_from_db
                _db = SessionLocal()
                try:
                    sync_report = sync_keywords_from_db(_db)
                    logger.info(
                        "RankScheduler keyword sync: %s items",
                        sync_report.get("synced_items", 0),
                    )
                finally:
                    _db.close()
            except Exception as sync_exc:
                logger.warning("RankScheduler keyword sync skipped: %s", sync_exc)
            logger.info("RankScheduler started (RANK_SCHEDULER_ENABLED=true)")
        except Exception as exc:
            logger.warning("RankScheduler failed to start: %s", exc)

    if settings.AI_SCENARIO_HEALTH_SCHEDULER_ENABLED:
        try:
            from app.services.scenario_health_scheduler import scenario_health_scheduler as _sh
            scenario_health_scheduler = _sh
            scenario_health_scheduler.start(
                check_hour=settings.AI_SCENARIO_HEALTH_CHECK_HOUR,
                check_minute=settings.AI_SCENARIO_HEALTH_CHECK_MINUTE,
                interval_hours=settings.AI_SCENARIO_HEALTH_INTERVAL_HOURS,
            )
            logger.info("ScenarioHealthScheduler started")
        except Exception as exc:
            logger.warning("ScenarioHealthScheduler failed to start: %s", exc)

    if settings.MEDIA_CLEANUP_SCHEDULER_ENABLED:
        try:
            from app.services.media_cleanup_scheduler import media_cleanup_scheduler as _mc
            media_cleanup_scheduler = _mc
            media_cleanup_scheduler.start(
                interval_minutes=settings.MEDIA_CLEANUP_INTERVAL_MINUTES,
            )
            logger.info("MediaCleanupScheduler started")
        except Exception as exc:
            logger.warning("MediaCleanupScheduler failed to start: %s", exc)

    return rank_scheduler, scenario_health_scheduler, media_cleanup_scheduler


def _lifespan_start_hermes_schedulers():
    """启动 Hermes / Nvidia 相关调度器。"""
    nvidia_probe_scheduler = None
    hermes_patrol_scheduler = None
    greedy_revenue_scheduler = None
    greedy_endurance_scheduler = None
    greedy_survival_digest_scheduler = None
    if settings.nvidia_customer_probe_scheduler_active:
        try:
            from app.services.nvidia_customer_probe_scheduler import (
                nvidia_customer_probe_scheduler as _np,
            )
            nvidia_probe_scheduler = _np
            nvidia_probe_scheduler.start(bootstrap_probe=True)
            logger.info(
                "NvidiaCustomerProbeScheduler started (auto=%s env=%s)",
                settings.NVIDIA_CUSTOMER_PROBE_SCHEDULER_ENABLED is None,
                settings.ENVIRONMENT,
            )
        except Exception as exc:
            logger.warning("NvidiaCustomerProbeScheduler failed to start: %s", exc)

    if settings.hermes_site_patrol_scheduler_active:
        try:
            from app.services.hermes.site_patrol_scheduler import (
                hermes_site_patrol_scheduler as _hp,
            )
            hermes_patrol_scheduler = _hp
            hermes_patrol_scheduler.start(bootstrap=True)
            logger.info(
                "HermesSitePatrolScheduler started (auto=%s env=%s interval=%sm)",
                settings.HERMES_SITE_PATROL_SCHEDULER_ENABLED is None,
                settings.ENVIRONMENT,
                settings.HERMES_SITE_PATROL_INTERVAL_MINUTES,
            )
        except Exception as exc:
            logger.warning("HermesSitePatrolScheduler failed to start: %s", exc)

    if settings.greedy_revenue_loop_scheduler_active:
        try:
            from app.services.hermes.greedy_revenue_loop_scheduler import (
                greedy_revenue_loop_scheduler as _gr,
            )
            greedy_revenue_scheduler = _gr
            greedy_revenue_scheduler.start(bootstrap=True)
            logger.info(
                "GreedyRevenueLoopScheduler started (auto=%s env=%s interval=%sh)",
                settings.HERMES_GREEDY_REVENUE_LOOP_SCHEDULER_ENABLED is None,
                settings.ENVIRONMENT,
                settings.HERMES_GREEDY_REVENUE_LOOP_INTERVAL_HOURS,
            )
        except Exception as exc:
            logger.warning("GreedyRevenueLoopScheduler failed to start: %s", exc)

    if settings.greedy_endurance_scheduler_active:
        try:
            from app.services.hermes.greedy_endurance_scheduler import (
                greedy_endurance_scheduler as _ge,
            )
            greedy_endurance_scheduler = _ge
            greedy_endurance_scheduler.start()
            logger.info(
                "GreedyEnduranceScheduler started 7x24 tick=%sm",
                settings.HERMES_GREEDY_ENDURANCE_TICK_MINUTES,
            )
        except Exception as exc:
            logger.warning("GreedyEnduranceScheduler failed to start: %s", exc)

    if settings.greedy_survival_digest_scheduler_active:
        try:
            from app.services.hermes.greedy_survival_digest_scheduler import (
                greedy_survival_digest_scheduler as _gd,
            )
            greedy_survival_digest_scheduler = _gd
            greedy_survival_digest_scheduler.start()
            logger.info(
                "GreedySurvivalDigestScheduler started weekday=%s hour=%s tz=%s",
                settings.HERMES_GREEDY_DIGEST_WEEKDAY,
                settings.HERMES_GREEDY_DIGEST_HOUR,
                settings.HERMES_GREEDY_DIGEST_TIMEZONE,
            )
        except Exception as exc:
            logger.warning("GreedySurvivalDigestScheduler failed to start: %s", exc)

    return (
        nvidia_probe_scheduler,
        hermes_patrol_scheduler,
        greedy_revenue_scheduler,
        greedy_endurance_scheduler,
        greedy_survival_digest_scheduler,
    )


def _lifespan_start_greedy_bootstrap():
    """按需启动 Greedy 发布租户引导（仅副作用，无需要停止的句柄）。"""
    if settings.greedy_bootstrap_on_startup and settings.HERMES_GREEDY_AVATAR_ENABLED:
        try:
            from app.core.database import SessionLocal
            from app.services.hermes.greedy_production_readiness_service import (
                bootstrap_publish_platform_accounts,
                ensure_greedy_publish_tenant,
            )
            if not (settings.HERMES_GREEDY_PUBLISH_TENANT_ID or "").strip():
                sdb = SessionLocal()
                try:
                    tenant = ensure_greedy_publish_tenant(sdb)
                    if tenant.get("tenant_id"):
                        bootstrap_publish_platform_accounts(
                            sdb,
                            tenant_id=str(tenant["tenant_id"]),
                            locale=str(settings.HERMES_GREEDY_DEFAULT_LOCALE or "global"),
                        )
                        logger.info(
                            "Greedy publish tenant bootstrap on startup: %s",
                            tenant.get("tenant_id"),
                        )
                finally:
                    sdb.close()
        except Exception as exc:
            logger.warning("Greedy publish tenant bootstrap skipped: %s", exc)


def _lifespan_start_extra_schedulers():
    """启动 Ops 自动驾驶 / 指挥中枢预热 / Deerflow / 交易情报 / 每日自主运营闭环。"""
    ops_autopilot_scheduler = None
    command_center_prewarm_scheduler = None
    deerflow_scheduler = None
    trade_intel_scheduler = None
    daily_autonomous_cycle_scheduler = None
    if settings.ops_autopilot_dev_active:
        try:
            from app.services.ops_autopilot_scheduler import ops_autopilot_scheduler as _ops_ap
            ops_autopilot_scheduler = _ops_ap
            ops_autopilot_scheduler.start()
            logger.info(
                "OpsAutopilotScheduler started interval=%smin env=%s",
                settings.OPS_AUTOPILOT_INTERVAL_MINUTES,
                settings.ENVIRONMENT,
            )
        except Exception as exc:
            logger.warning("OpsAutopilotScheduler failed to start: %s", exc)

    if settings.command_center_prewarm_active:
        try:
            from app.services.hermes.command_center_cache import (
                command_center_prewarm_scheduler as _cc_prewarm,
            )
            command_center_prewarm_scheduler = _cc_prewarm
            command_center_prewarm_scheduler.start()
            logger.info(
                "CommandCenterPrewarmScheduler started interval=%ss env=%s",
                command_center_prewarm_scheduler.interval_seconds,
                settings.ENVIRONMENT,
            )
        except Exception as exc:
            logger.warning("CommandCenterPrewarmScheduler failed to start: %s", exc)

    if settings.deerflow_scheduler_active:
        try:
            from app.services.ubrain.deerflow_scheduler import deerflow_scheduler as _df
            deerflow_scheduler = _df
            deerflow_scheduler.start(bootstrap=True)
            logger.info(
                "DeerflowScheduler started (auto=%s env=%s at %02d:%02d)",
                settings.DEERFLOW_SCHEDULER_ENABLED is None,
                settings.ENVIRONMENT,
                settings.DEERFLOW_SCHEDULE_HOUR,
                settings.DEERFLOW_SCHEDULE_MINUTE,
            )
        except Exception as exc:
            logger.warning("DeerflowScheduler failed to start: %s", exc)

    if settings.trade_intel_scheduler_active:
        try:
            from app.services.trade_intel_scheduler import trade_intel_scheduler as _ti
            trade_intel_scheduler = _ti
            trade_intel_scheduler.start(bootstrap=True)
            logger.info(
                "TradeIntelScheduler started (auto=%s env=%s weekday=%s %02d:%02d)",
                settings.TRADE_INTEL_SCHEDULER_ENABLED is None,
                settings.ENVIRONMENT,
                settings.TRADE_INTEL_REFRESH_WEEKDAY,
                settings.TRADE_INTEL_REFRESH_HOUR,
                settings.TRADE_INTEL_REFRESH_MINUTE,
            )
        except Exception as exc:
            logger.warning("TradeIntelScheduler failed to start: %s", exc)

    # 每日自主运营闭环（串联 tech_radar → geo_probe → content_gen → publish → inquiry → attribution → feedback）
    if settings.daily_autonomous_cycle_active:
        try:
            from app.services.hermes.daily_autonomous_cycle import (
                daily_autonomous_cycle_scheduler as _dac,
            )
            daily_autonomous_cycle_scheduler = _dac
            daily_autonomous_cycle_scheduler.start(bootstrap=True)
            logger.info(
                "DailyAutonomousCycleScheduler started (auto=%s env=%s at %02d:%02d)",
                settings.DAILY_AUTONOMOUS_CYCLE_ENABLED is None,
                settings.ENVIRONMENT,
                settings.DAILY_AUTONOMOUS_CYCLE_HOUR,
                settings.DAILY_AUTONOMOUS_CYCLE_MINUTE,
            )
        except Exception as exc:
            logger.warning("DailyAutonomousCycleScheduler failed to start: %s", exc)

    return (
        ops_autopilot_scheduler,
        command_center_prewarm_scheduler,
        deerflow_scheduler,
        trade_intel_scheduler,
        daily_autonomous_cycle_scheduler,
    )


def _lifespan_start_nurture_and_storage():
    """启动养号互动 Worker 并执行平台存储启动检查。"""
    nurture_worker_scheduler = None
    try:
        from app.services.nurture_execution_scheduler import nurture_execution_scheduler as _new
        nurture_worker_scheduler = _new
        nurture_worker_scheduler.start()
        logger.info("NurtureExecutionScheduler started (interval=10min)")
    except Exception as exc:
        logger.warning("NurtureExecutionScheduler failed to start: %s", exc)

    try:
        from app.services.platform_storage_provision_service import (
            production_storage_startup_message,
        )
        storage_warn = production_storage_startup_message()
        if storage_warn:
            logger.warning(storage_warn)
    except Exception as exc:
        logger.debug("Platform storage startup check skipped: %s", exc)

    return nurture_worker_scheduler


def _lifespan_stop_schedulers(
    rank_scheduler,
    scenario_health_scheduler,
    media_cleanup_scheduler,
    nvidia_probe_scheduler,
    hermes_patrol_scheduler,
    greedy_revenue_scheduler,
    greedy_endurance_scheduler,
    greedy_survival_digest_scheduler,
    ops_autopilot_scheduler,
    command_center_prewarm_scheduler,
    deerflow_scheduler,
    trade_intel_scheduler,
    daily_autonomous_cycle_scheduler,
    nurture_worker_scheduler,
):
    """按启动顺序反向停止所有已启动的调度器。"""
    if rank_scheduler is not None:
        try:
            rank_scheduler.stop()
        except Exception:
            pass

    if scenario_health_scheduler is not None:
        try:
            scenario_health_scheduler.stop()
        except Exception:
            pass

    if media_cleanup_scheduler is not None:
        try:
            media_cleanup_scheduler.stop()
        except Exception:
            pass

    if nvidia_probe_scheduler is not None:
        try:
            nvidia_probe_scheduler.stop()
        except Exception:
            pass

    if hermes_patrol_scheduler is not None:
        try:
            hermes_patrol_scheduler.stop()
        except Exception:
            pass

    if greedy_revenue_scheduler is not None:
        try:
            greedy_revenue_scheduler.stop()
        except Exception:
            pass

    if greedy_endurance_scheduler is not None:
        try:
            greedy_endurance_scheduler.stop()
        except Exception:
            pass

    if greedy_survival_digest_scheduler is not None:
        try:
            greedy_survival_digest_scheduler.stop()
        except Exception:
            pass

    if ops_autopilot_scheduler is not None:
        try:
            ops_autopilot_scheduler.stop()
        except Exception:
            pass

    if command_center_prewarm_scheduler is not None:
        try:
            command_center_prewarm_scheduler.stop()
        except Exception:
            pass

    if deerflow_scheduler is not None:
        try:
            deerflow_scheduler.stop()
        except Exception:
            pass

    if trade_intel_scheduler is not None:
        try:
            trade_intel_scheduler.stop()
        except Exception:
            pass

    if daily_autonomous_cycle_scheduler is not None:
        try:
            daily_autonomous_cycle_scheduler.stop()
        except Exception:
            pass

    if nurture_worker_scheduler is not None:
        try:
            nurture_worker_scheduler.stop()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    _lifespan_init_core()
    (
        rank_scheduler,
        scenario_health_scheduler,
        media_cleanup_scheduler,
    ) = _lifespan_start_basic_schedulers()
    (
        nvidia_probe_scheduler,
        hermes_patrol_scheduler,
        greedy_revenue_scheduler,
        greedy_endurance_scheduler,
        greedy_survival_digest_scheduler,
    ) = _lifespan_start_hermes_schedulers()
    _lifespan_start_greedy_bootstrap()
    (
        ops_autopilot_scheduler,
        command_center_prewarm_scheduler,
        deerflow_scheduler,
        trade_intel_scheduler,
        daily_autonomous_cycle_scheduler,
    ) = _lifespan_start_extra_schedulers()
    nurture_worker_scheduler = _lifespan_start_nurture_and_storage()
    yield
    _lifespan_stop_schedulers(
        rank_scheduler,
        scenario_health_scheduler,
        media_cleanup_scheduler,
        nvidia_probe_scheduler,
        hermes_patrol_scheduler,
        greedy_revenue_scheduler,
        greedy_endurance_scheduler,
        greedy_survival_digest_scheduler,
        ops_autopilot_scheduler,
        command_center_prewarm_scheduler,
        deerflow_scheduler,
        trade_intel_scheduler,
        daily_autonomous_cycle_scheduler,
        nurture_worker_scheduler,
    )


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP安全响应头（API）
app.add_middleware(APISecurityHeadersMiddleware)

# HTTP安全响应头（HTML页面）
app.add_middleware(SecurityHeadersMiddleware)

# Session中间件（用于CSRF保护）
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# CSRF保护中间件（仅对cookie流程生效，Bearer token豁免）
app.add_middleware(CSRFMiddleware)

# FIX-29: API 请求签名 + 防重放中间件（生产环境强制验证写操作）
from app.core.request_signature import RequestSignatureMiddleware
app.add_middleware(RequestSignatureMiddleware)

# WAF防火墙配置（SQL注入、XSS、路径遍历、命令注入统一检测）
setup_waf(app)

# 安全中间件（路径遍历防护 — WAF白名单路径的额外保护）
app.add_middleware(SecurityMiddleware)

# 限流中间件
app.add_middleware(RateLimitMiddleware)

# 性能监控中间件（同时激活 Prometheus metrics 接线）
app.add_middleware(PerformanceMiddleware)

# 请求 ID / trace_id 贯穿中间件（审计 CLOSE-09）— 放在最外层以覆盖所有请求
app.add_middleware(RequestIdMiddleware)

# 租户识别中间件（Host解析租户）
app.add_middleware(TenantMiddleware)

# 压缩 JSON 等大响应（须在出站扫描之前注册，避免 gzip 后再扫描）
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 租户可见 API 品牌脱敏
app.add_middleware(BrandGuardResponseMiddleware)

# 出站扫描须在 Unify 之后执行：先注册 NoFake（响应链外层），再注册 Unify（内层包装）
app.add_middleware(NoFakeDeliveryResponseMiddleware)
app.add_middleware(UnifyV1ApiResponseMiddleware)

# 静态文件服务（与 files API 共用 backend/uploads）
from app.core.uploads_path import ensure_uploads_dir, migrate_legacy_uploads, uploads_dir as get_uploads_dir

migrate_legacy_uploads()
uploads_dir = get_uploads_dir()
ensure_uploads_dir()
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

media_factory_dir = os.path.join(uploads_dir, "media_factory")
os.makedirs(media_factory_dir, exist_ok=True)

static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 注册API路由
app.include_router(api_router, prefix="/api")
# 注册 Prometheus metrics 导出端点（CLOSE-12：激活现有 record_request/record_error）
app.include_router(metrics_router)


# === 根级探活端点(供 K8s/Nginx 健康检查) ===
@app.get("/", tags=["系统"], include_in_schema=False)
async def root_index():
    """根路径 — 返回服务标识(无敏感信息)"""
    return {
        "name": settings.APP_NAME,
        "version": settings.PROJECT_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.DEBUG else "(disabled in production)",
    }


@app.get("/health", tags=["系统"], include_in_schema=False)
async def root_health():
    """根级健康检查 — K8s liveness/readiness 探针标准路径
    始终返回 200,除非进程已死。
    """
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/health/ready", tags=["系统"], include_in_schema=False)
async def root_health_ready():
    """就绪探针 — 检查 DB / Redis 关键依赖是否可用
    任意依赖异常返回 503(让 K8s 把流量切走)。
    """
    checks = {"db": "unknown", "redis": "unknown"}
    try:
        from app.db.session import engine
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        checks["db"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["db"] = f"fail: {type(exc).__name__}"

    try:
        if settings.REDIS_ENABLED:
            import redis  # type: ignore
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                socket_timeout=2,
            )
            r.ping()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "disabled"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"fail: {type(exc).__name__}"

    all_ok = all(v == "ok" or v == "disabled" for v in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ready" if all_ok else "not_ready", "checks": checks},
    )


@app.exception_handler(NotConfiguredError)
async def not_configured_handler(request: Request, exc: NotConfiguredError):
    """上游未配置 — 503，禁止假成功。"""
    return JSONResponse(
        status_code=503,
        content=APIResponse(
            code=503,
            message=str(exc),
            data={"error_code": exc.code},
        ).dict(),
    )


@app.exception_handler(FakeDeliveryViolation)
async def fake_delivery_handler(request: Request, exc: FakeDeliveryViolation):
    """fake_delivery_handler。

    参数说明：
    :param request: 参数 request
    :param exc: 参数 exc
    :return: 返回处理结果。
    """
    return JSONResponse(
        status_code=503,
        content=APIResponse(
            code=503,
            message=str(exc),
            data={"error_code": exc.code, "violations": exc.violations},
        ).dict(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            code=exc.status_code,
            message=str(
                exc.detail)).dict())


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            code=500,
            message="服务器内部错误").dict())




