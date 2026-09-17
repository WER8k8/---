# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""生产上线就绪检查（Sprint I）。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import Platform
from app.services.platform_catalog import PLATFORMS_CN, PLATFORMS_GLOBAL


@dataclass
class ReadinessCheck:
    id: str
    category: str
    title: str
    status: str  # pass | warn | fail
    message: str
    required: bool = True
    def to_dict(self) -> dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "id": self.id,
            "category": self.category,
            "title": self.title,
            "status": self.status,
            "message": self.message,
            "required": self.required,
        }


@dataclass
class ReadinessReport:
    checks: list[ReadinessCheck] = field(default_factory=list)
    def add(self, check: ReadinessCheck) -> None:
        """add。

        参数说明：
        :param self: 参数 self
        :param check: 参数 check
        :return: 返回处理结果。
        """
        self.checks.append(check)

    @property
    def ready(self) -> bool:
        """ready。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return all(c.status != "fail" for c in self.checks if c.required)

    @property
    def score(self) -> dict[str, int]:
        """score。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "pass": sum(1 for c in self.checks if c.status == "pass"),
            "warn": sum(1 for c in self.checks if c.status == "warn"),
            "fail": sum(1 for c in self.checks if c.status == "fail"),
        }

    def to_dict(self) -> dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "ready": self.ready,
            "environment": settings.ENVIRONMENT,
            "score": self.score,
            "checks": [c.to_dict() for c in self.checks],
        }


def _is_production() -> bool:
    """_is_production。
    :return: 返回处理结果。
    """
    return (settings.ENVIRONMENT or "").lower() == "production"


def _is_mvp_launch() -> bool:
    """主站商用 MVP：AI/AccioWork 二期，核心询盘+流量可先上。"""
    return settings.MVP_LAUNCH


def _check_jwt(report: ReadinessReport) -> None:
    """_check_jwt。

    参数说明：
    :param report: 参数 report
    :return: 返回处理结果。
    """
    key = settings.JWT_SECRET_KEY or settings.SECRET_KEY or ""
    if len(key) < 32:
        report.add(
            ReadinessCheck(
                "jwt_secret",
                "security",
                "JWT 密钥强度",
                "fail" if _is_production() else "warn",
                "JWT_SECRET_KEY 长度应 ≥ 32",
            )
        )
    else:
        report.add(
            ReadinessCheck(
                "jwt_secret",
                "security",
                "JWT 密钥强度",
                "pass",
                "已配置",
            )
        )


def _check_oauth_dev_bypass(report: ReadinessReport) -> None:
    """_check_oauth_dev_bypass。

    参数说明：
    :param report: 参数 report
    :return: 返回处理结果。
    """
    bypass = os.getenv("OAUTH_DEV_BYPASS", "").lower() in ("1", "true", "yes")
    if bypass and _is_production():
        report.add(
            ReadinessCheck(
                "oauth_dev_bypass",
                "security",
                "OAuth 开发绕过",
                "fail",
                "生产环境必须关闭 OAUTH_DEV_BYPASS",
            )
        )
    elif bypass:
        report.add(
            ReadinessCheck(
                "oauth_dev_bypass",
                "security",
                "OAuth 开发绕过",
                "warn",
                "开发环境已开启 OAUTH_DEV_BYPASS",
                required=False,
            )
        )
    else:
        report.add(
            ReadinessCheck(
                "oauth_dev_bypass",
                "security",
                "OAuth 开发绕过",
                "pass",
                "已关闭",
            )
        )


def _check_database(report: ReadinessReport, db: Session | None) -> None:
    """_check_database。

    参数说明：
    :param report: 参数 report
    :param db: 参数 db
    :return: 返回处理结果。
    """
    url = (settings.DATABASE_URL or "").lower()
    if _is_production() and "sqlite" in url:
        report.add(
            ReadinessCheck(
                "database_url",
                "database",
                "生产数据库",
                "fail",
                "生产环境不应使用 SQLite",
            )
        )
    elif "sqlite" in url:
        report.add(
            ReadinessCheck(
                "database_url",
                "database",
                "数据库类型",
                "warn",
                "当前为 SQLite（仅开发）",
                required=False,
            )
        )
    else:
        report.add(
            ReadinessCheck(
                "database_url",
                "database",
                "数据库类型",
                "pass",
                "非 SQLite",
            )
        )

    if db is None:
        report.add(
            ReadinessCheck(
                "database_ping",
                "database",
                "数据库连通",
                "warn",
                "未提供 Session，跳过 SELECT 1",
                required=False,
            )
        )
        return
    try:
        db.execute(text("SELECT 1"))
        report.add(
            ReadinessCheck(
                "database_ping",
                "database",
                "数据库连通",
                "pass",
                "SELECT 1 成功",
            )
        )
    except Exception as exc:
        report.add(
            ReadinessCheck(
                "database_ping",
                "database",
                "数据库连通",
                "fail",
                str(exc),
            )
        )


def _check_logistics(report: ReadinessReport) -> None:
    """_check_logistics。

    参数说明：
    :param report: 参数 report
    :return: 返回处理结果。
    """
    provider = (settings.LOGISTICS_PROVIDER or "demo").lower()
    if provider == "kuaidi100":
        if settings.KUAIDI100_API_KEY and settings.KUAIDI100_CUSTOMER:
            report.add(
                ReadinessCheck(
                    "logistics",
                    "integrations",
                    "快递100",
                    "pass",
                    "已配置 customer/key",
                )
            )
        else:
            report.add(
                ReadinessCheck(
                    "logistics",
                    "integrations",
                    "快递100",
                    "fail" if _is_production() else "warn",
                    "LOGISTICS_PROVIDER=kuaidi100 但缺少 KUAIDI100_*",
                )
            )
    else:
        report.add(
            ReadinessCheck(
                "logistics",
                "integrations",
                "物流",
                "warn" if _is_production() else "pass",
                f"当前为 {provider}（生产建议 kuaidi100）",
                required=False,
            )
        )


def _check_platforms(report: ReadinessReport, db: Session | None) -> None:
    """_check_platforms。

    参数说明：
    :param report: 参数 report
    :param db: 参数 db
    :return: 返回处理结果。
    """
    if db is None:
        return
    try:
        cn = (
            db.query(func.count(Platform.id))
            .filter(Platform.region == "cn", Platform.is_active)
            .scalar()
            or 0
        )
        gl = (
            db.query(func.count(Platform.id))
            .filter(Platform.region == "global", Platform.is_active)
            .scalar()
            or 0
        )
    except (OperationalError, ProgrammingError) as exc:
        report.add(
            ReadinessCheck(
                "platforms_40",
                "data",
                "40 平台主数据",
                "warn" if not _is_production() else "fail",
                f"无法查询 platforms：{exc}；请执行 migrate_production / seed_platforms_full",
                required=_is_production(),
            )
        )
        return
    ready = cn >= len(PLATFORMS_CN) and gl >= len(PLATFORMS_GLOBAL)
    report.add(
        ReadinessCheck(
            "platforms_40",
            "data",
            "40 平台主数据",
            "pass" if ready else ("warn" if not _is_production() else "fail"),
            f"cn={cn}/{len(PLATFORMS_CN)}, global={gl}/{len(PLATFORMS_GLOBAL)}",
            required=_is_production(),
        )
    )


def _check_backup_dir(report: ReadinessReport) -> None:
    """_check_backup_dir。

    参数说明：
    :param report: 参数 report
    :return: 返回处理结果。
    """
    backup_root = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "backups",
    )
    try:
        os.makedirs(backup_root, exist_ok=True)
        test_file = os.path.join(backup_root, ".write_test")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test_file)
        report.add(
            ReadinessCheck(
                "backup_dir",
                "ops",
                "备份目录可写",
                "pass",
                backup_root,
            )
        )
    except OSError as exc:
        report.add(
            ReadinessCheck(
                "backup_dir",
                "ops",
                "备份目录可写",
                "fail",
                str(exc),
            )
        )


def _check_frontend_url(report: ReadinessReport) -> None:
    """_check_frontend_url。

    参数说明：
    :param report: 参数 report
    :return: 返回处理结果。
    """
    url = os.getenv("FRONTEND_URL", "")
    if not url:
        report.add(
            ReadinessCheck(
                "frontend_url",
                "config",
                "FRONTEND_URL",
                "warn",
                "未设置，OAuth 回调可能异常",
                required=False,
            )
        )
    else:
        report.add(
            ReadinessCheck(
                "frontend_url",
                "config",
                "FRONTEND_URL",
                "pass",
                url,
            )
        )


def _check_crawl_webhook_secret(report: ReadinessReport) -> None:
    """_check_crawl_webhook_secret。

    参数说明：
    :param report: 参数 report
    :return: 返回处理结果。
    """
    secret = (settings.CRAWL_WEBHOOK_SECRET or "").strip()
    is_prod = (settings.ENVIRONMENT or "").lower() == "production"
    if secret:
        report.add(
            ReadinessCheck(
                "crawl_webhook_secret",
                "integrations",
                "国际爬虫 Webhook",
                "pass",
                "CRAWL_WEBHOOK_SECRET 已配置",
                required=False,
            )
        )
    elif is_prod:
        report.add(
            ReadinessCheck(
                "crawl_webhook_secret",
                "integrations",
                "国际爬虫 Webhook",
                "warn",
                "生产未配置 CRAWL_WEBHOOK_SECRET",
                required=False,
            )
        )
    else:
        report.add(
            ReadinessCheck(
                "crawl_webhook_secret",
                "integrations",
                "国际爬虫 Webhook",
                "warn",
                "开发环境可暂不配置",
                required=False,
            )
        )


def _check_celery_broker(report: ReadinessReport) -> None:
    """_check_celery_broker。

    参数说明：
    :param report: 参数 report
    :return: 返回处理结果。
    """
    broker = (os.getenv("CELERY_BROKER_URL") or settings.REDIS_URL or "").strip()
    if broker:
        report.add(
            ReadinessCheck(
                "celery_broker",
                "integrations",
                "Celery Broker",
                "pass",
                broker[:80],
                required=False,
            )
        )
    else:
        report.add(
            ReadinessCheck(
                "celery_broker",
                "integrations",
                "Celery Broker",
                "warn",
                "未配置 CELERY_BROKER_URL",
                required=False,
            )
        )


def _check_redis(report: ReadinessReport) -> None:
    """_check_redis。

    参数说明：
    :param report: 参数 report
    :return: 返回处理结果。
    """
    if not settings.REDIS_ENABLED:
        report.add(
            ReadinessCheck(
                "redis",
                "integrations",
                "Redis",
                "warn",
                "REDIS_ENABLED=false",
                required=False,
            )
        )
        return
    try:
        import redis
        connect_timeout = 0.4 if not _is_production() else 2
        client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=connect_timeout)
        client.ping()
        report.add(
            ReadinessCheck(
                "redis",
                "integrations",
                "Redis",
                "pass",
                "PING 成功",
                required=False,
            )
        )
    except Exception as exc:
        report.add(
            ReadinessCheck(
                "redis",
                "integrations",
                "Redis",
                "warn",
                str(exc),
                required=False,
            )
        )


def _check_payment_strict(report: ReadinessReport) -> None:
    """_check_payment_strict。

    参数说明：
    :param report: 参数 report
    :return: 返回处理结果。
    """
    strict = os.getenv("PAYMENT_STRICT_VERIFY", "").lower() in ("1", "true", "yes")
    if _is_production() and not strict and not _is_mvp_launch():
        report.add(
            ReadinessCheck(
                "payment_strict",
                "security",
                "支付回调验签",
                "fail",
                "生产请设置 PAYMENT_STRICT_VERIFY=1",
            )
        )
    elif strict:
        report.add(
            ReadinessCheck(
                "payment_strict",
                "security",
                "支付回调验签",
                "pass",
                "PAYMENT_STRICT_VERIFY 已开启",
            )
        )
    elif _is_production() and _is_mvp_launch():
        report.add(
            ReadinessCheck(
                "payment_strict",
                "security",
                "支付回调验签（MVP）",
                "warn",
                "MVP 未开验签；开通收款前务必 PAYMENT_STRICT_VERIFY=1",
                required=False,
            )
        )
    else:
        report.add(
            ReadinessCheck(
                "payment_strict",
                "security",
                "支付回调验签",
                "warn",
                "开发环境未强制验签",
                required=False,
            )
        )


def _check_ai_provider(report: ReadinessReport) -> None:
    """_check_ai_provider。

    参数说明：
    :param report: 参数 report
    :return: 返回处理结果。
    """
    keys = [
        settings.AI_DEEPSEEK_API_KEY,
        settings.AI_OPENAI_API_KEY,
        settings.AI_NVIDIA_API_KEY,
        settings.AI_ANTHROPIC_API_KEY,
        settings.AI_GEMINI_API_KEY,
    ]
    has_key = any(k for k in keys if k)
    mvp = _is_mvp_launch()
    if has_key:
        report.add(
            ReadinessCheck(
                "ai_provider",
                "integrations",
                "AI 提供商",
                "pass",
                "已配置至少一个 API Key",
                required=not mvp,
            )
        )
    elif _is_production() and not mvp:
        report.add(
            ReadinessCheck(
                "ai_provider",
                "integrations",
                "AI 提供商",
                "fail",
                "生产需配置 AI Key，或设置 MVP_LAUNCH=1",
            )
        )
    elif _is_production() and mvp:
        report.add(
            ReadinessCheck(
                "ai_provider",
                "integrations",
                "AI 提供商（MVP）",
                "warn",
                "MVP_LAUNCH=1：AI 路由可用 mock，二期再配 Key",
                required=False,
            )
        )
    else:
        report.add(
            ReadinessCheck(
                "ai_provider",
                "integrations",
                "AI 提供商",
                "warn",
                "未配置（开发环境）",
                required=False,
            )
        )


def _check_mvp_flag(report: ReadinessReport) -> None:
    """_check_mvp_flag。

    参数说明：
    :param report: 参数 report
    :return: 返回处理结果。
    """
    if _is_mvp_launch():
        report.add(
            ReadinessCheck(
                "mvp_launch",
                "config",
                "主站商用 MVP 模式",
                "pass",
                "MVP_LAUNCH=1（AI/AccioWork 二期）",
                required=False,
            )
        )


def _check_smtp(report: ReadinessReport) -> None:
    """P1-07：生产 SMTP 发信就绪（验证码/询盘通知）。"""
    from app.services.email_service import email_service
    status = email_service.smtp_status()
    configured = bool(status.get("configured"))
    if configured:
        report.add(
            ReadinessCheck(
                "smtp_email",
                "integrations",
                "SMTP 发信",
                "pass",
                f"{status.get('server')}:{status.get('port')}",
                required=False,
            )
        )
    elif _is_production():
        report.add(
            ReadinessCheck(
                "smtp_email",
                "integrations",
                "SMTP 发信",
                "fail",
                "生产须配置 SMTP_SERVER / SMTP_USERNAME / SMTP_PASSWORD",
            )
        )
    else:
        report.add(
            ReadinessCheck(
                "smtp_email",
                "integrations",
                "SMTP 发信",
                "warn",
                "开发环境可 mock；生产须配置",
                required=False,
            )
        )


def _check_ssl_provider(report: ReadinessReport) -> None:
    """_check_ssl_provider。

    参数说明：
    :param report: 参数 report
    :return: 返回处理结果。
    """
    provider = (
        getattr(settings, "SSL_PROVIDER", None) or os.getenv("SSL_PROVIDER", "mock")
    ).lower()
    if _is_production() and provider == "mock" and not _is_mvp_launch():
        report.add(
            ReadinessCheck(
                "ssl_provider",
                "security",
                "SSL 签发",
                "fail",
                "生产请使用 certbot 或 ssl_worker，勿用 mock",
            )
        )
    elif provider == "certbot":
        email = os.getenv("CERTBOT_EMAIL", "").strip()
        status = "pass" if email else ("fail" if _is_production() else "warn")
        report.add(
            ReadinessCheck(
                "ssl_provider",
                "security",
                "SSL certbot",
                status,
                "CERTBOT_EMAIL 已配置" if email else "缺少 CERTBOT_EMAIL",
            )
        )
    else:
        report.add(
            ReadinessCheck(
                "ssl_provider",
                "security",
                "SSL 签发",
                "warn" if _is_production() else "pass",
                f"当前 SSL_PROVIDER={provider}",
                required=False,
            )
        )


def _check_ubrain_stack(report: ReadinessReport) -> None:
    """_check_ubrain_stack。

    参数说明：
    :param report: 参数 report
    :return: 返回处理结果。
    """
    try:
        from app.main import app
        paths = [getattr(r, "path", "") or "" for r in app.routes]
        needed = ["/api/v1/ubrain/chat", "/api/v1/trade-intel/feasibility"]
        missing = [p for p in needed if p not in paths]
        if missing:
            status = "warn" if (_is_mvp_launch() or not _is_production()) else "fail"
            report.add(
                ReadinessCheck(
                    "ubrain_api",
                    "product",
                    "UBrain / 出海参谋 API",
                    status,
                    f"缺失: {', '.join(missing)}",
                    required=_is_production() and not _is_mvp_launch(),
                )
            )
        else:
            report.add(
                ReadinessCheck(
                    "ubrain_api",
                    "product",
                    "UBrain / 出海参谋 API",
                    "pass",
                    "已挂载",
                )
            )
    except Exception as exc:
        report.add(
            ReadinessCheck(
                "ubrain_api",
                "product",
                "UBrain API",
                "warn",
                str(exc),
                required=False,
            )
        )


def run_readiness_checks(db: Session | None = None) -> ReadinessReport:
    """run_readiness_checks。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    report = ReadinessReport()
    _check_jwt(report)
    _check_oauth_dev_bypass(report)
    _check_database(report, db)
    _check_logistics(report)
    _check_platforms(report, db)
    _check_backup_dir(report)
    _check_frontend_url(report)
    _check_redis(report)
    _check_celery_broker(report)
    _check_crawl_webhook_secret(report)
    _check_payment_strict(report)
    _check_smtp(report)
    _check_ssl_provider(report)
    _check_ai_provider(report)
    _check_mvp_flag(report)
    _check_ubrain_stack(report)
    return report


def check_mounted_routes() -> ReadinessCheck:
    """关键 API 前缀挂载检查。"""
    required = [
        "/api/v1/referral",
        "/api/v1/super-admin",
        "/api/v1/logistics/track",
        "/api/v1/ops/readiness",
        "/api/v1/platforms/catalog",
        "/api/v1/ubrain/chat",
        "/api/v1/bff/client/bootstrap",
        "/api/v1/app/v1/home",
        "/api/v1/app/v1/config",
        "/api/v1/app/v1/today",
        "/api/v1/app/v1/assistant/chat",
        "/api/v1/trade-intel/feasibility",
        "/api/v1/inquiries/channels/wecom",
        "/api/v1/finance/import/commit",
        "/api/v1/ops/seven-steps/audit",
        "/api/v1/analytics/event",
        "/api/v1/analytics/site-context",
        "/api/v1/analytics/traffic-board",
    ]
    seo_any = ["/api/v1/seo/site-audit", "/api/v1/seo/run-audit"]
    try:
        from app.main import app
        paths = [getattr(r, "path", "") or "" for r in app.routes]
        missing = [
            p for p in required if not any(x.startswith(p) for x in paths)
        ]
        if not any(any(x.startswith(s) for x in paths) for s in seo_any):
            missing.append("seo_advanced")
        if missing:
            return ReadinessCheck(
                "routes_mounted",
                "ops",
                "关键 API 挂载",
                "fail",
                f"缺失: {', '.join(missing)}",
            )
        try:
            from app.services.super_admin_path_audit import run_super_admin_path_audit
            audit = run_super_admin_path_audit()
            if not audit.get("ok"):
                return ReadinessCheck(
                    "super_admin_paths",
                    "ops",
                    "超管路径对齐 P0-08",
                    "fail",
                    f"前端引用缺失 {audit.get('missing_count')} 条",
                )
        except Exception as exc:
            return ReadinessCheck(
                "super_admin_paths",
                "ops",
                "超管路径对齐 P0-08",
                "warn",
                str(exc)[:200],
            )
        return ReadinessCheck(
            "routes_mounted",
            "ops",
            "关键 API 挂载",
            "pass",
            "关键前缀已挂载",
        )
    except Exception as exc:
        return ReadinessCheck(
            "routes_mounted",
            "ops",
            "关键 API 挂载",
            "warn",
            str(exc),
            required=False,
        )
