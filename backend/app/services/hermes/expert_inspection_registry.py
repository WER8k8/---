"""专家巡检注册表 — 基于 ECC (Everything Claude Code) 真实技能体系实现专家功能。

ECC 包含：36个专用子智能体、271+个技能模块、92+个命令
技能分类：coding-standards、backend-patterns、frontend-patterns、security-review、
         tdd-workflow、continuous-learning、api-design、deployment-patterns 等
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.services.hermes.agency.role_loader import load_role

logger = logging.getLogger("uj-admin.expert_inspection")

InspectionResult = dict[str, Any]
InspectionFunc = Callable[[str, Session | None], InspectionResult]


def _safe_fetch(callable_func, *args, default=None):
    """_safe_fetch。

    参数说明：
    :param callable_func: 参数 callable_func
    :param default: 参数 default
    :param *args: 参数 *args
    :return: 返回处理结果。
    """
    try:
        result = callable_func(*args)
        return result if result is not None else default
    except Exception as exc:
        logger.debug("Inspection fetch failed: %s", exc)
        return default


def inspect_seo_specialist(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_seo_specialist。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.seo.rank_scheduler_ops import build_rank_scheduler_ops_snapshot
    from app.services.seo.inclusion_check_service import inclusion_probe_status
    from app.services.seo.seo_matrix_db_health import seo_matrix_db_health
    rank_scheduler = _safe_fetch(build_rank_scheduler_ops_snapshot, db, default={}) if db else {}
    inclusion = _safe_fetch(inclusion_probe_status, default={})
    matrix_health = _safe_fetch(seo_matrix_db_health, default={})
    keyword_count = int(rank_scheduler.get("keyword_count") or 0)
    tracked_count = int(rank_scheduler.get("tracked_keywords") or 0)
    rank_ok_count = int(rank_scheduler.get("rank_ok_count") or 0)
    probe_enabled = bool(inclusion.get("real_probe_enabled") or False)
    score = 0
    next_actions: list[str] = []
    if keyword_count > 0:
        score += min(keyword_count // 10, 20)
    else:
        next_actions.append("P0: 执行关键词研究（keyword research）")

    if tracked_count > 0:
        score += min(tracked_count // 5, 20)
    else:
        next_actions.append("P0: 配置关键词追踪到 Rank Scheduler")

    if rank_ok_count > 0:
        score += min(rank_ok_count * 2, 25)
    else:
        next_actions.append("P1: 运行技术SEO审计（technical SEO audit）")

    if probe_enabled:
        score += 15
    else:
        next_actions.append("P1: 开启收录探测（inclusion probe）")

    if matrix_health.get("ok"):
        score += 20
    else:
        next_actions.append("P0: 修复SEO矩阵数据库连接")

    return {
        "category": "marketing",
        "inspection_type": "SEO技术审计/关键词策略/排名追踪",
        "score": min(score, 100),
        "stats": {
            "keywords_in_db": keyword_count,
            "tracked_keywords": tracked_count,
            "rank_ok_count": rank_ok_count,
            "inclusion_probe_enabled": probe_enabled,
            "matrix_db_ok": matrix_health.get("ok"),
        },
        "next_actions": next_actions[:6],
        "details": {
            "rank_scheduler": rank_scheduler,
            "inclusion": inclusion,
            "matrix_health": matrix_health,
            "ecc_skills": ["技术SEO审计", "关键词研究框架", "页面优化清单", "外链建设策略"],
        },
    }


def inspect_content_creator(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_content_creator。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.hermes_continuous_iteration_service import iteration_status
    iteration = _safe_fetch(iteration_status, default={})
    inbox_count = int(iteration.get("inbox_count") or 0)
    recent_briefs = iteration.get("recent_briefs") or []
    score = 0
    next_actions: list[str] = []
    if inbox_count == 0:
        score += 30
    else:
        score += min(50 - inbox_count * 5, 10)
        next_actions.append(f"处理 PM Inbox 中 {inbox_count} 条待办")

    if len(recent_briefs) > 0:
        score += 30
    else:
        next_actions.append("P0: 创建内容研究简报（content brief）")

    next_actions.append("P1: 执行SEO内容优化（content optimization）")
    next_actions.append("P1: 检查内容缺口分析（content gap analysis）")
    next_actions.append("P1: 优化标题和Meta标签")
    score += 20
    return {
        "category": "marketing",
        "inspection_type": "内容创作/SEO优化/研究简报",
        "score": min(score, 100),
        "stats": {
            "inbox_count": inbox_count,
            "recent_briefs_count": len(recent_briefs),
        },
        "next_actions": next_actions[:6],
        "details": {
            "iteration": iteration,
            "ecc_skills": ["article-writing", "content-engine", "market-research", "continuous-learning"],
        },
    }


def inspect_growth_hacker(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_growth_hacker。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.ops_autopilot import load_ops_snapshot
    ops = _safe_fetch(load_ops_snapshot, default={})
    flywheel = ops.get("flywheel") or {}
    score = 0
    next_actions: list[str] = []
    flywheel_ok = bool(flywheel.get("ok"))
    if flywheel_ok:
        score += 40
    else:
        next_actions.append("P0: 启动增长飞轮（growth flywheel）")

    recent_run = ops.get("saved_at")
    if recent_run:
        score += 30
    else:
        next_actions.append("P1: 执行运营循环（ops cycle）")

    next_actions.append("P1: 设置增长实验（growth experiments）")
    next_actions.append("P1: 分析用户行为漏斗（funnel analysis）")
    next_actions.append("P1: 优化转化路径（conversion optimization）")
    score += 20
    return {
        "category": "marketing",
        "inspection_type": "增长黑客/用户增长/实验驱动",
        "score": min(score, 100),
        "stats": {
            "flywheel_running": flywheel_ok,
            "last_ops_run": recent_run,
        },
        "next_actions": next_actions[:6],
        "details": {
            "ops": ops,
            "ecc_skills": ["autonomous-loops", "continuous-learning", "eval-harness", "verification-loop"],
        },
    }


def inspect_cross_border_ecommerce(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_cross_border_ecommerce。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.platform_survival_service import survival_status
    survival = _safe_fetch(survival_status, db, default={}) if db else {}
    runway_days = int(survival.get("runway_days") or 0)
    recent_settlements = survival.get("recent_settlements") or []
    score = 0
    next_actions: list[str] = []
    if runway_days >= 30:
        score += 30
    else:
        score += 5
        next_actions.append("P0: 紧急处理跨境结算问题")

    if len(recent_settlements) > 0:
        score += 30
    else:
        next_actions.append("P1: 确认跨境收款渠道")

    next_actions.append("P1: 检查汇率风险管理")
    next_actions.append("P1: 配置多币种定价策略")
    next_actions.append("P1: 验证跨境物流设置")
    score += 30
    return {
        "category": "marketing",
        "inspection_type": "跨境电商/结算/多币种",
        "score": min(score, 100),
        "stats": {
            "runway_days": runway_days,
            "recent_settlements_count": len(recent_settlements),
        },
        "next_actions": next_actions[:6],
        "details": {
            "survival": survival,
            "ecc_skills": ["finance-fpa-analyst", "currency-strategy", "cross-border-compliance"],
        },
    }


def inspect_paid_media(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_paid_media。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.ops_autopilot import load_ops_snapshot
    ops = _safe_fetch(load_ops_snapshot, default={})
    score = 50
    next_actions: list[str] = []
    next_actions.append("P0: 配置付费广告账户（PPC accounts）")
    next_actions.append("P1: 设置广告跟踪（ad tracking）")
    next_actions.append("P1: 执行广告账户审计（account audit）")
    next_actions.append("P1: 优化广告投放策略（bidding strategy）")
    next_actions.append("P1: 分析广告ROI（performance analysis）")
    return {
        "category": "paid-media",
        "inspection_type": "付费媒体/PPC/广告优化",
        "score": min(score, 100),
        "stats": {},
        "next_actions": next_actions[:6],
        "details": {
            "ops": ops,
            "ecc_skills": ["paid-media-strategy", "analytics-reporting", "budget-optimization"],
        },
    }


def inspect_engineering(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_engineering。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    try:
        from app.services.hermes.site_patrol_service import patrol_status
        from app.services.hermes.write_boundary_audit_service import audit_write_boundaries
        from app.services.hermes.ops_autopilot import load_ops_snapshot
        patrol = _safe_fetch(patrol_status, db, default={}) if db else {}
        boundary = _safe_fetch(audit_write_boundaries, default={})
        ops = _safe_fetch(load_ops_snapshot, default={})
        pass_count = int(patrol.get("pass_count") or 0)
        fail_count = int(patrol.get("fail_count") or 0)
        boundary_ok = bool(boundary.get("ok"))
        violations = int(boundary.get("violations_count") or 0)
        score = 0
        next_actions: list[str] = []
        total_checks = pass_count + fail_count
        if total_checks > 0:
            pass_rate = (pass_count / total_checks) * 100
            score += min(round(pass_rate), 30)
            if fail_count > 0:
                next_actions.append(f"P0: 修复 {fail_count} 项系统健康检查失败")
        else:
            next_actions.append("P1: 运行系统巡站检查（site patrol）")

        if boundary_ok:
            score += 30
        else:
            score += max(0, 30 - violations * 5)
            next_actions.append(f"P0: 修复 {violations} 项写库边界违规")

        last_run = ops.get("saved_at")
        if last_run:
            score += 20
        else:
            next_actions.append("P1: 执行技术栈审计（tech stack audit）")

        score += 20
        return {
            "category": "engineering",
            "inspection_type": "系统健康/安全/运维/架构",
            "score": min(score, 100),
            "stats": {
                "patrol_pass": pass_count,
                "patrol_fail": fail_count,
                "boundary_ok": boundary_ok,
                "boundary_violations": violations,
                "last_ops_run": last_run,
            },
            "next_actions": next_actions[:6],
            "details": {
                "patrol": patrol,
                "boundary": boundary,
                "ops_snapshot": ops,
                "ecc_skills": ["backend-patterns", "api-design", "deployment-patterns", "docker-patterns"],
            },
        }
    except Exception:
        return {
            "category": "engineering",
            "inspection_type": "系统健康/安全/运维/架构",
            "score": 35,
            "stats": {
                "patrol_pass": 0,
                "patrol_fail": 0,
                "boundary_ok": False,
                "boundary_violations": 0,
            },
            "next_actions": ["P1: 运行系统巡站检查", "P1: 执行安全扫描（security scan）"],
            "details": {
                "note": "工程服务暂不可用",
                "ecc_skills": ["backend-patterns", "api-design", "deployment-patterns", "security-scan"],
            },
        }


def inspect_code_reviewer(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_code_reviewer。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    score = 50
    next_actions: list[str] = []
    next_actions.append("P1: 执行代码审查（code review）")
    next_actions.append("P1: 检查安全漏洞（security vulnerabilities）")
    next_actions.append("P1: 验证编码规范（coding standards）")
    next_actions.append("P1: 评估架构设计（architecture review）")
    next_actions.append("P1: 检查测试覆盖率（test coverage）")
    return {
        "category": "engineering",
        "inspection_type": "代码审查/安全审查/质量保障",
        "score": min(score, 100),
        "stats": {},
        "next_actions": next_actions[:6],
        "details": {
            "ecc_skills": ["code-reviewer", "security-reviewer", "cpp-reviewer", "python-reviewer", "typescript-reviewer"],
        },
    }


def inspect_build_resolver(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_build_resolver。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    score = 40
    next_actions: list[str] = []
    next_actions.append("P0: 检查构建错误（build errors）")
    next_actions.append("P1: 验证依赖版本（dependency versions）")
    next_actions.append("P1: 修复编译问题（compilation issues）")
    next_actions.append("P1: 配置CI/CD流水线（CI/CD pipeline）")
    return {
        "category": "engineering",
        "inspection_type": "构建错误修复/CI/CD/依赖管理",
        "score": min(score, 100),
        "stats": {},
        "next_actions": next_actions[:6],
        "details": {
            "ecc_skills": ["build-error-resolver", "go-build-resolver", "rust-build-resolver", "java-build-resolver"],
        },
    }


def inspect_security_engineer(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_security_engineer。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.write_boundary_audit_service import audit_write_boundaries
    boundary = _safe_fetch(audit_write_boundaries, default={})
    boundary_ok = bool(boundary.get("ok"))
    violations = int(boundary.get("violations_count") or 0)
    score = 0
    next_actions: list[str] = []
    if boundary_ok:
        score += 30
    else:
        score += max(0, 30 - violations * 5)
        next_actions.append(f"P0: 修复 {violations} 项写库边界违规")

    next_actions.append("P1: 执行安全代码审查（security code review）")
    next_actions.append("P1: 检查OWASP Top 10漏洞（OWASP vulnerabilities）")
    next_actions.append("P1: 验证认证系统安全（authentication security）")
    next_actions.append("P1: 评估API授权机制（authorization mechanism）")
    next_actions.append("P1: 运行依赖漏洞扫描（dependency vulnerability scan）")
    score += 40
    return {
        "category": "engineering",
        "inspection_type": "安全工程师/威胁建模/漏洞评估/安全架构",
        "score": min(score, 100),
        "stats": {
            "boundary_ok": boundary_ok,
            "boundary_violations": violations,
        },
        "next_actions": next_actions[:6],
        "details": {
            "boundary": boundary,
            "ecc_skills": ["security-reviewer", "security-review", "security-scan", "backend-patterns", "api-design"],
        },
    }


def inspect_sre(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_sre。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.site_patrol_service import patrol_status
    patrol = _safe_fetch(patrol_status, db, default={}) if db else {}
    pass_count = int(patrol.get("pass_count") or 0)
    fail_count = int(patrol.get("fail_count") or 0)
    score = 0
    next_actions: list[str] = []
    total_checks = pass_count + fail_count
    if total_checks > 0:
        pass_rate = (pass_count / total_checks) * 100
        score += min(round(pass_rate), 40)
        if fail_count > 0:
            next_actions.append(f"P0: 修复 {fail_count} 项系统健康检查失败")
    else:
        next_actions.append("P1: 运行系统巡站检查（site patrol）")

    next_actions.append("P1: 定义SLO和错误预算（SLO/error budget）")
    next_actions.append("P1: 检查可观测性指标（observability metrics）")
    next_actions.append("P1: 评估告警配置（alerting configuration）")
    next_actions.append("P1: 执行混沌工程实验（chaos engineering）")
    score += 40
    return {
        "category": "engineering",
        "inspection_type": "SRE/站点可靠性/SLO/可观测性/混沌工程",
        "score": min(score, 100),
        "stats": {
            "patrol_pass": pass_count,
            "patrol_fail": fail_count,
            "pass_rate": round((pass_count / (pass_count + fail_count)) * 100) if (pass_count + fail_count) > 0 else 0,
        },
        "next_actions": next_actions[:6],
        "details": {
            "patrol": patrol,
            "ecc_skills": ["deployment-patterns", "docker-patterns", "continuous-learning", "eval-harness"],
        },
    }


def inspect_devops_automator(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_devops_automator。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.ops_autopilot import load_ops_snapshot
    ops = _safe_fetch(load_ops_snapshot, default={})
    last_run = ops.get("saved_at")
    score = 0
    next_actions: list[str] = []
    if last_run:
        score += 30
    else:
        next_actions.append("P1: 执行Ops自动化运行（ops automation run）")

    next_actions.append("P1: 配置CI/CD流水线（CI/CD pipeline）")
    next_actions.append("P1: 部署基础设施即代码（infrastructure as code）")
    next_actions.append("P1: 设置容器编排（container orchestration）")
    next_actions.append("P1: 配置监控和告警（monitoring & alerting）")
    next_actions.append("P1: 实施零停机部署（zero-downtime deployment）")
    score += 50
    return {
        "category": "engineering",
        "inspection_type": "DevOps/CI/CD/基础设施自动化/云运维",
        "score": min(score, 100),
        "stats": {
            "last_ops_run": last_run,
        },
        "next_actions": next_actions[:6],
        "details": {
            "ops": ops,
            "ecc_skills": ["deployment-patterns", "docker-patterns", "api-design", "backend-patterns"],
        },
    }


def inspect_frontend_developer(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_frontend_developer。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    score = 55
    next_actions: list[str] = []
    next_actions.append("P1: 检查前端构建状态（frontend build status）")
    next_actions.append("P1: 验证组件样式一致性（component style consistency）")
    next_actions.append("P1: 测试响应式设计（responsive design testing）")
    next_actions.append("P1: 优化页面性能（page performance optimization）")
    next_actions.append("P1: 检查无障碍合规（accessibility compliance）")
    return {
        "category": "engineering",
        "inspection_type": "前端开发/组件设计/性能优化/无障碍",
        "score": min(score, 100),
        "stats": {},
        "next_actions": next_actions[:6],
        "details": {
            "ecc_skills": ["frontend-patterns", "coding-standards", "e2e-testing", "frontend-slides"],
        },
    }


def inspect_database_optimizer(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_database_optimizer。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.site_patrol_service import patrol_status
    patrol = _safe_fetch(patrol_status, db, default={}) if db else {}
    pass_count = int(patrol.get("pass_count") or 0)
    fail_count = int(patrol.get("fail_count") or 0)
    score = 0
    next_actions: list[str] = []
    total_checks = pass_count + fail_count
    if total_checks > 0:
        pass_rate = (pass_count / total_checks) * 100
        score += min(round(pass_rate), 30)
    else:
        next_actions.append("P1: 运行数据库健康检查（database health check）")

    next_actions.append("P1: 分析慢查询日志（slow query analysis）")
    next_actions.append("P1: 优化数据库索引（index optimization）")
    next_actions.append("P1: 评估查询性能（query performance evaluation）")
    next_actions.append("P1: 检查数据库连接池（connection pool status）")
    score += 50
    return {
        "category": "engineering",
        "inspection_type": "数据库优化/索引设计/查询性能/连接池",
        "score": min(score, 100),
        "stats": {
            "patrol_pass": pass_count,
            "patrol_fail": fail_count,
        },
        "next_actions": next_actions[:6],
        "details": {
            "patrol": patrol,
            "ecc_skills": ["database-reviewer", "postgres-patterns", "clickhouse-io", "database-migrations"],
        },
    }


def inspect_data_engineer(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_data_engineer。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    score = 50
    next_actions: list[str] = []
    next_actions.append("P1: 检查数据管道状态（data pipeline status）")
    next_actions.append("P1: 验证数据质量（data quality validation）")
    next_actions.append("P1: 评估ETL流程（ETL process evaluation）")
    next_actions.append("P1: 优化数据存储（data storage optimization）")
    next_actions.append("P1: 配置数据监控（data monitoring）")
    return {
        "category": "engineering",
        "inspection_type": "数据工程/数据管道/ETL/数据质量",
        "score": min(score, 100),
        "stats": {},
        "next_actions": next_actions[:6],
        "details": {
            "ecc_skills": ["clickhouse-io", "database-migrations", "continuous-learning", "python-patterns"],
        },
    }


def inspect_technical_writer(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_technical_writer。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    score = 55
    next_actions: list[str] = []
    next_actions.append("P1: 检查API文档完整性（API documentation completeness）")
    next_actions.append("P1: 验证文档与代码同步（docs-code synchronization）")
    next_actions.append("P1: 更新技术文档（technical documentation update）")
    next_actions.append("P1: 编写用户指南（user guide creation）")
    next_actions.append("P1: 创建代码示例（code examples）")
    return {
        "category": "engineering",
        "inspection_type": "技术写作/API文档/用户指南/文档维护",
        "score": min(score, 100),
        "stats": {},
        "next_actions": next_actions[:6],
        "details": {
            "ecc_skills": ["article-writing", "docs-lookup", "doc-updater", "content-engine"],
        },
    }


def inspect_finance(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_finance。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.platform_survival_service import survival_status
    from app.services.hermes.a2a_skill_marketplace_service import revenue_pulse
    survival = _safe_fetch(survival_status, db, default={}) if db else {}
    pulse = _safe_fetch(revenue_pulse, db, default={}) if db else {}
    runway_days = int(survival.get("runway_days") or 0)
    balance_cny = float(survival.get("balance_cny") or 0)
    today_target = float((pulse.get("daily_target") or {}).get("cny") or 0)
    today_actual = float((pulse.get("today") or {}).get("cny") or 0)
    score = 0
    next_actions: list[str] = []
    if runway_days >= 90:
        score += 30
    elif runway_days >= 30:
        score += 20
        next_actions.append("P1: 拓展收入来源")
    else:
        score += 5
        next_actions.append("P0: 紧急处理资金问题")

    if balance_cny > 0:
        score += min(int(balance_cny // 1000), 25)

    if today_target > 0:
        progress = (today_actual / today_target) * 100
        score += min(round(progress), 25)
        if progress < 50:
            next_actions.append(f"P1: 今日目标完成 {round(progress)}%")
    else:
        next_actions.append("P1: 设置每日收入目标")

    recent_settlements = survival.get("recent_settlements") or []
    if len(recent_settlements) > 0:
        score += 20
    else:
        next_actions.append("P1: 确认收款渠道")

    return {
        "category": "finance",
        "inspection_type": "资金管理/收入追踪/财务分析",
        "score": min(score, 100),
        "stats": {
            "runway_days": runway_days,
            "balance_cny": round(balance_cny, 2),
            "today_target_cny": round(today_target, 2),
            "today_actual_cny": round(today_actual, 2),
            "recent_settlements_count": len(recent_settlements),
        },
        "next_actions": next_actions[:6],
        "details": {
            "survival": survival,
            "revenue_pulse": pulse,
            "ecc_skills": ["finance-fpa-analyst", "investor-materials", "cost-aware-llm-pipeline"],
        },
    }


def inspect_sales(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_sales。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    try:
        from app.services.hermes.a2a_skill_marketplace_service import a2a_status, list_open_tasks
        from app.services.hermes.ops_autopilot import load_ops_snapshot
        a2a = _safe_fetch(a2a_status, db, default={}) if db else {}
        tasks = _safe_fetch(list_open_tasks, limit=10, default=[])
        ops = _safe_fetch(load_ops_snapshot, default={})
        agent_count = len(a2a.get("agents") or [])
        skill_count = len(a2a.get("skills") or [])
        open_task_count = len(tasks)
        recent_flywheel = ops.get("flywheel") or {}
        score = 0
        next_actions: list[str] = []
        if agent_count >= 5:
            score += 20
        elif agent_count > 0:
            score += 10
        else:
            next_actions.append("P1: 配置销售代理")

        if skill_count >= 10:
            score += 20
        elif skill_count > 0:
            score += 10
        else:
            next_actions.append("P1: 注册销售技能")

        if open_task_count > 0:
            score += min(open_task_count * 5, 25)
            next_actions.append(f"处理 {open_task_count} 个待执行销售任务")
        else:
            next_actions.append("P1: 创建销售任务")

        flywheel_ok = bool(recent_flywheel.get("ok"))
        if flywheel_ok:
            score += 20
        else:
            next_actions.append("P1: 检查销售飞轮状态")

        score += 15
        return {
            "category": "sales",
            "inspection_type": "销售管理/客户跟进/交易策略",
            "score": min(score, 100),
            "stats": {
                "agent_count": agent_count,
                "skill_count": skill_count,
                "open_task_count": open_task_count,
                "flywheel_running": flywheel_ok,
            },
            "next_actions": next_actions[:6],
            "details": {
                "a2a_status": a2a,
                "open_tasks": tasks[:5],
                "flywheel": recent_flywheel,
                "ecc_skills": ["sales-outbound", "deal-strategy", "customer-billing-ops"],
            },
        }
    except Exception:
        return {
            "category": "sales",
            "inspection_type": "销售管理/客户跟进/交易策略",
            "score": 30,
            "stats": {
                "agent_count": 0,
                "skill_count": 0,
                "open_task_count": 0,
            },
            "next_actions": ["P1: 配置销售代理", "P1: 注册销售技能", "P1: 创建销售任务"],
            "details": {
                "note": "销售服务暂不可用",
                "ecc_skills": ["sales-outbound", "deal-strategy"],
            },
        }


def inspect_support(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_support。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    try:
        from app.services.hermes.site_patrol_service import patrol_status
        from app.services.hermes.ops_autopilot import load_ops_snapshot
        patrol = _safe_fetch(patrol_status, db, default={}) if db else {}
        ops = _safe_fetch(load_ops_snapshot, default={})
        pass_count = int(patrol.get("pass_count") or 0)
        fail_count = int(patrol.get("fail_count") or 0)
        remediation = ops.get("remediation") or {}
        score = 0
        next_actions: list[str] = []
        total_checks = pass_count + fail_count
        if total_checks > 0:
            pass_rate = (pass_count / total_checks) * 100
            score += round(pass_rate)
            if fail_count > 0:
                next_actions.append(f"修复 {fail_count} 项系统检查失败")
        else:
            next_actions.append("执行系统巡站检查")

        if remediation:
            score += 10

        return {
            "category": "support",
            "inspection_type": "系统支持/运维状态/问题处理",
            "score": min(score, 100),
            "stats": {
                "patrol_pass": pass_count,
                "patrol_fail": fail_count,
                "has_remediation": bool(remediation),
            },
            "next_actions": next_actions[:6],
            "details": {
                "patrol": patrol,
                "remediation": remediation,
                "ecc_skills": ["build-error-resolver", "chief-of-staff", "docs-lookup"],
            },
        }
    except Exception:
        return {
            "category": "support",
            "inspection_type": "系统支持/运维状态/问题处理",
            "score": 40,
            "stats": {
                "patrol_pass": 0,
                "patrol_fail": 0,
                "has_remediation": False,
            },
            "next_actions": ["执行系统巡站检查"],
            "details": {
                "note": "系统支持服务暂不可用",
                "ecc_skills": ["build-error-resolver", "chief-of-staff"],
            },
        }


def inspect_product(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_product。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.hermes_continuous_iteration_service import iteration_status
    iteration = _safe_fetch(iteration_status, default={})
    inbox_count = int(iteration.get("inbox_count") or 0)
    recent_briefs = iteration.get("recent_briefs") or []
    department_routing = iteration.get("department_routing") or []
    score = 0
    next_actions: list[str] = []
    if inbox_count == 0:
        score += 30
    elif inbox_count < 5:
        score += 20
    else:
        score += 5
        next_actions.append(f"处理 PM Inbox 中 {inbox_count} 条待办")

    if len(recent_briefs) > 0:
        score += 30
    else:
        next_actions.append("创建产品研究简报（product brief）")

    if len(department_routing) > 0:
        score += 20
    else:
        next_actions.append("配置部门路由规则")

    next_actions.append("P1: 执行产品规划（product planning）")
    next_actions.append("P1: 进行竞品分析（competitive analysis）")
    score += 20
    return {
        "category": "product",
        "inspection_type": "产品管理/需求分析/迭代规划",
        "score": min(score, 100),
        "stats": {
            "inbox_count": inbox_count,
            "recent_briefs_count": len(recent_briefs),
            "department_routing_count": len(department_routing),
        },
        "next_actions": next_actions[:6],
        "details": {
            "iteration": iteration,
            "ecc_skills": ["planner", "architect", "continuous-learning", "verification-loop"],
        },
    }


def inspect_design(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_design。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    score = 65
    next_actions: list[str] = []
    next_actions.append("P1: 运行品牌合规扫描（brand compliance scan）")
    next_actions.append("P1: 检查产品图片资源配置")
    next_actions.append("P1: 验证前端组件样式一致性")
    next_actions.append("P1: 执行设计系统审计（design system audit）")
    next_actions.append("P1: 优化UI/UX设计（UI/UX optimization）")
    return {
        "category": "design",
        "inspection_type": "品牌设计/UI/UX/视觉规范",
        "score": min(score, 100),
        "stats": {
            "brand_audit_pending": True,
        },
        "next_actions": next_actions[:6],
        "details": {
            "ecc_skills": ["brand-voice", "liquid-glass-design", "frontend-patterns"],
        },
    }


def inspect_testing(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_testing。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.site_patrol_service import patrol_status
    patrol = _safe_fetch(patrol_status, db, default={}) if db else {}
    pass_count = int(patrol.get("pass_count") or 0)
    fail_count = int(patrol.get("fail_count") or 0)
    score = 0
    next_actions: list[str] = []
    total_checks = pass_count + fail_count
    if total_checks > 0:
        pass_rate = (pass_count / total_checks) * 100
        score += round(pass_rate)
        if fail_count > 0:
            next_actions.append(f"修复 {fail_count} 项测试失败")
    else:
        next_actions.append("执行测试检查（test execution）")

    next_actions.append("P1: 设置TDD工作流（TDD workflow）")
    next_actions.append("P1: 编写端到端测试（E2E testing）")
    next_actions.append("P1: 分析测试覆盖率（test coverage analysis）")
    return {
        "category": "testing",
        "inspection_type": "测试执行/质量保障/TDD",
        "score": min(score, 100),
        "stats": {
            "checks_pass": pass_count,
            "checks_fail": fail_count,
        },
        "next_actions": next_actions[:6],
        "details": {
            "patrol": patrol,
            "ecc_skills": ["tdd-workflow", "e2e-testing", "eval-harness", "verification-loop"],
        },
    }


def inspect_strategy(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_strategy。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.hermes_continuous_iteration_service import iteration_status
    iteration = _safe_fetch(iteration_status, default={})
    score = 55
    next_actions: list[str] = []
    next_actions.append("P1: 执行战略规划（strategic planning）")
    next_actions.append("P1: 分析市场趋势（market trend analysis）")
    next_actions.append("P1: 制定竞争策略（competitive strategy）")
    next_actions.append("P1: 创建执行计划（execution plan）")
    return {
        "category": "strategy",
        "inspection_type": "战略规划/市场分析/竞争策略",
        "score": min(score, 100),
        "stats": {},
        "next_actions": next_actions[:6],
        "details": {
            "iteration": iteration,
            "ecc_skills": ["strategic-compact", "market-research", "investor-materials", "investor-outreach"],
        },
    }


def inspect_specialized(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_specialized。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.ops_autopilot import load_ops_snapshot
    ops = _safe_fetch(load_ops_snapshot, default={})
    last_run = ops.get("saved_at")
    score = 45
    next_actions: list[str] = []
    if last_run:
        score += 30
    else:
        next_actions.append("执行专项检查")

    role = load_role(role_id)
    if role:
        name = role.get("name") or role_id
        next_actions.append(f"为「{name}」专家配置专项技能")

    return {
        "category": "specialized",
        "inspection_type": "专项技能检查",
        "score": min(score, 100),
        "stats": {
            "last_ops_run": last_run,
        },
        "next_actions": next_actions[:6],
        "details": {
            "ops": ops,
            "ecc_skills": ["specialized-workflow", "continuous-learning", "iterative-retrieval"],
        },
    }


def inspect_project_management(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_project_management。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.hermes_continuous_iteration_service import iteration_status
    iteration = _safe_fetch(iteration_status, default={})
    inbox_count = int(iteration.get("inbox_count") or 0)
    score = 50
    next_actions: list[str] = []
    if inbox_count == 0:
        score += 20
    else:
        next_actions.append(f"处理 {inbox_count} 个项目待办")

    next_actions.append("P1: 创建项目计划（project planning）")
    next_actions.append("P1: 设置里程碑（milestone setting）")
    next_actions.append("P1: 分配任务（task assignment）")
    next_actions.append("P1: 跟踪进度（progress tracking）")
    score += 20
    return {
        "category": "project-management",
        "inspection_type": "项目管理/进度跟踪/里程碑",
        "score": min(score, 100),
        "stats": {
            "inbox_count": inbox_count,
        },
        "next_actions": next_actions[:6],
        "details": {
            "iteration": iteration,
            "ecc_skills": ["planner", "multi-workflow", "verification-loop"],
        },
    }


def inspect_game_development(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_game_development。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    score = 45
    next_actions: list[str] = []
    next_actions.append("P1: 检查游戏引擎配置（game engine setup）")
    next_actions.append("P1: 验证图形渲染管线（render pipeline）")
    next_actions.append("P1: 设置物理系统（physics system）")
    next_actions.append("P1: 配置多人游戏网络（multiplayer network）")
    next_actions.append("P1: 创建关卡设计（level design）")
    return {
        "category": "game-development",
        "inspection_type": "游戏开发/引擎配置/关卡设计",
        "score": min(score, 100),
        "stats": {},
        "next_actions": next_actions[:6],
        "details": {
            "ecc_skills": ["game-design", "unity-patterns", "unreal-engine", "godot-patterns"],
        },
    }


def inspect_spatial_computing(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_spatial_computing。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    score = 40
    next_actions: list[str] = []
    next_actions.append("P1: 配置XR环境（XR setup）")
    next_actions.append("P1: 设计空间交互（spatial interaction）")
    next_actions.append("P1: 优化3D渲染（3D rendering optimization）")
    next_actions.append("P1: 设置AR/VR设备（AR/VR device setup）")
    return {
        "category": "spatial-computing",
        "inspection_type": "空间计算/XR/AR/VR",
        "score": min(score, 100),
        "stats": {},
        "next_actions": next_actions[:6],
        "details": {
            "ecc_skills": ["xr-development", "visionos-spatial", "macos-spatial-metal"],
        },
    }


def inspect_academic(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_academic。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    score = 50
    next_actions: list[str] = []
    next_actions.append("P1: 执行学术研究（academic research）")
    next_actions.append("P1: 撰写研究论文（research paper writing）")
    next_actions.append("P1: 分析数据（data analysis）")
    next_actions.append("P1: 创建学术报告（academic report）")
    return {
        "category": "academic",
        "inspection_type": "学术研究/数据分析/论文写作",
        "score": min(score, 100),
        "stats": {},
        "next_actions": next_actions[:6],
        "details": {
            "ecc_skills": ["continuous-learning", "market-research", "article-writing"],
        },
    }


def _get_role_specific_inspector(role_id: str) -> InspectionFunc | None:
    """_get_role_specific_inspector。

    参数说明：
    :param role_id: 参数 role_id
    :return: 返回处理结果。
    """
    patterns: dict[str, InspectionFunc] = {}
    patterns.update(_role_patterns_group1())
    patterns.update(_role_patterns_group2())
    patterns.update(_role_patterns_group3())
    patterns.update(_role_patterns_group4())
    for pattern, func in patterns.items():
        if re.search(pattern, role_id):
            return func
    return None



def inspect_default(role_id: str, db: Session | None) -> InspectionResult:
    """inspect_default。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    role = load_role(role_id)
    if not role:
        return {
            "category": "unknown",
            "inspection_type": "未分类专家",
            "score": 0,
            "stats": {},
            "next_actions": ["未找到该专家角色定义"],
            "details": {},
        }

    name = role.get("name") or role_id
    description = role.get("description") or ""
    score = 30
    next_actions: list[str] = []
    next_actions.append(f"为「{name}」专家配置巡检逻辑")
    if description:
        next_actions.append(f"专家职责：{description[:50]}")

    return {
        "category": "default",
        "inspection_type": "专家角色检查",
        "score": min(score, 100),
        "stats": {
            "role_found": True,
            "role_name": name,
        },
        "next_actions": next_actions[:6],
        "details": {
            "role": role,
            "ecc_skills": ["continuous-learning", "iterative-retrieval"],
        },
    }


INSPECTION_REGISTRY: dict[str, InspectionFunc] = {
    "marketing": inspect_content_creator,
    "paid-media": inspect_paid_media,
    "engineering": inspect_engineering,
    "finance": inspect_finance,
    "sales": inspect_sales,
    "support": inspect_support,
    "product": inspect_product,
    "design": inspect_design,
    "testing": inspect_testing,
    "specialized": inspect_specialized,
    "project-management": inspect_project_management,
    "academic": inspect_academic,
    "game-development": inspect_game_development,
    "spatial-computing": inspect_spatial_computing,
    "strategy": inspect_strategy,
}


def get_category_from_role_id(role_id: str) -> str:
    """get_category_from_role_id。

    参数说明：
    :param role_id: 参数 role_id
    :return: 返回处理结果。
    """
    rid = (role_id or "").strip().strip("/")
    if "/" in rid:
        return rid.split("/")[0]
    return "default"


def inspect_expert(role_id: str, db: Session | None = None) -> InspectionResult:
    """inspect_expert。

    参数说明：
    :param role_id: 参数 role_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    specific_func = _get_role_specific_inspector(role_id)
    if specific_func:
        result = specific_func(role_id, db)
        result["role_id"] = role_id
        result["category"] = get_category_from_role_id(role_id)
        return result

    category = get_category_from_role_id(role_id)
    func = INSPECTION_REGISTRY.get(category, inspect_default)
    result = func(role_id, db)
    result["role_id"] = role_id
    result["category"] = category
    return result


def list_inspection_categories() -> list[dict[str, Any]]:
    """list_inspection_categories。
    :return: 返回处理结果。
    """
    return [
        {"category": cat, "inspection_type": func.__name__.replace("inspect_", "").replace("_", " ").title()}
        for cat, func in INSPECTION_REGISTRY.items()
    ]

def _role_patterns_group1() -> dict[str, InspectionFunc]:
    """_role_patterns_group1。
    :return: 返回处理结果。
    """
    return {
        r"seo-specialist$": inspect_seo_specialist,
        r"content-creator$": inspect_content_creator,
        r"growth-hacker$": inspect_growth_hacker,
        r"cross-border-ecommerce$": inspect_cross_border_ecommerce,
        r"code-reviewer$": inspect_code_reviewer,
        r"build-resolver$": inspect_build_resolver,
        r"security-reviewer$": inspect_security_engineer,
        r"security-engineer$": inspect_security_engineer,
        r"sre$": inspect_sre,
        r"devops-automator$": inspect_devops_automator,
        r"frontend-developer$": inspect_frontend_developer,
        r"database-optimizer$": inspect_database_optimizer,
        r"data-engineer$": inspect_data_engineer,
        r"technical-writer$": inspect_technical_writer,
        r"software-architect$": inspect_engineering,
        r"senior-developer$": inspect_engineering,
        r"incident-response$": inspect_sre,
        r"git-workflow$": inspect_devops_automator,
        r"rapid-prototyper$": inspect_frontend_developer,
        r"mobile-app-builder$": inspect_frontend_developer,
        r"voice-ai-integration$": inspect_data_engineer,
        r"database-reviewer$": inspect_database_optimizer,
        r"python-reviewer$": inspect_code_reviewer,
        r"typescript-reviewer$": inspect_code_reviewer,
        r"cpp-reviewer$": inspect_code_reviewer,
        r"go-reviewer$": inspect_code_reviewer,
        r"java-reviewer$": inspect_code_reviewer,
        r"rust-reviewer$": inspect_code_reviewer,
        r"go-build-resolver$": inspect_build_resolver,
        r"rust-build-resolver$": inspect_build_resolver,
        r"java-build-resolver$": inspect_build_resolver,
        r"cpp-build-resolver$": inspect_build_resolver,
        r"kotlin-reviewer$": inspect_code_reviewer,
        r"kotlin-build-resolver$": inspect_build_resolver,
        r"pytorch-build-resolver$": inspect_build_resolver,
        r"e2e-runner$": inspect_testing,
        r"tdd-guide$": inspect_testing,
        r"architect$": inspect_engineering,
        r"planner$": inspect_product,
        r"chief-of-staff$": inspect_support,
        r"refactor-cleaner$": inspect_code_reviewer,
        r"doc-updater$": inspect_technical_writer,
        r"docs-lookup$": inspect_technical_writer,
        r"harness-optimizer$": inspect_sre,
        r"loop-operator$": inspect_sre,
        r"wechat-mini-program$": inspect_frontend_developer,
        r"feishu-integration$": inspect_frontend_developer,
        r"dingtalk-integration$": inspect_frontend_developer,
        r"embedded-linux$": inspect_engineering,
        r"embedded-firmware$": inspect_engineering,
        r"fpga-digital$": inspect_engineering,
        r"iot-solution$": inspect_engineering,
        r"solidity-smart-contract$": inspect_security_engineer,
    }


def _role_patterns_group2() -> dict[str, InspectionFunc]:
    """_role_patterns_group2。
    :return: 返回处理结果。
    """
    return {
        r"email-intelligence$": inspect_data_engineer,
        r"threat-detection$": inspect_security_engineer,
        r"filament-optimization$": inspect_frontend_developer,
        r"codebase-onboarding$": inspect_technical_writer,
        r"minimal-change-engineer$": inspect_engineering,
        r"zhihu-strategist$": inspect_content_creator,
        r"xiaohongshu-specialist$": inspect_content_creator,
        r"xiaohongshu-operator$": inspect_content_creator,
        r"weixin-channels$": inspect_content_creator,
        r"weibo-strategist$": inspect_content_creator,
        r"wechat-operator$": inspect_content_creator,
        r"wechat-official-account$": inspect_content_creator,
        r"video-optimization$": inspect_content_creator,
        r"twitter-engager$": inspect_content_creator,
        r"tiktok-strategist$": inspect_content_creator,
        r"social-media-strategist$": inspect_content_creator,
        r"short-video-editing$": inspect_content_creator,
        r"reddit-community$": inspect_content_creator,
        r"private-domain-operator$": inspect_content_creator,
        r"podcast-strategist$": inspect_content_creator,
        r"livestream-commerce$": inspect_content_creator,
        r"linkedin-content$": inspect_content_creator,
        r"kuaishou-strategist$": inspect_content_creator,
        r"knowledge-commerce$": inspect_content_creator,
        r"instagram-curator$": inspect_content_creator,
        r"ecommerce-operator$": inspect_content_creator,
        r"douyin-strategist$": inspect_content_creator,
        r"china-market-localization$": inspect_content_creator,
        r"china-ecommerce-operator$": inspect_content_creator,
        r"carousel-growth$": inspect_growth_hacker,
        r"book-co-author$": inspect_content_creator,
        r"bilibili-strategist$": inspect_content_creator,
        r"baidu-seo$": inspect_seo_specialist,
        r"app-store-optimizer$": inspect_seo_specialist,
        r"agentic-search-optimizer$": inspect_seo_specialist,
        r"ai-citation-strategist$": inspect_content_creator,
        r"ppc-strategist$": inspect_paid_media,
        r"paid-social-strategist$": inspect_paid_media,
        r"search-query-analyst$": inspect_paid_media,
        r"programmatic-buyer$": inspect_paid_media,
        r"creative-strategist$": inspect_paid_media,
        r"tracking-specialist$": inspect_paid_media,
        r"auditor$": inspect_paid_media,
        r"account-strategist$": inspect_sales,
        r"deal-strategist$": inspect_sales,
        r"discovery-coach$": inspect_sales,
        r"engineer$": inspect_sales,
        r"outbound-strategist$": inspect_sales,
        r"pipeline-analyst$": inspect_sales,
        r"proposal-strategist$": inspect_sales,
        r"coach$": inspect_sales,
        r"feedback-synthesizer$": inspect_product,
        r"behavioral-nudge$": inspect_product,
    }


def _role_patterns_group3() -> dict[str, InspectionFunc]:
    """_role_patterns_group3。
    :return: 返回处理结果。
    """
    return {
        r"trend-researcher$": inspect_product,
        r"sprint-prioritizer$": inspect_product,
        r"voice-ai-integration$": inspect_data_engineer,
        r"xr-interface$": inspect_spatial_computing,
        r"xr-immersive$": inspect_spatial_computing,
        r"visionos-spatial$": inspect_spatial_computing,
        r"macos-spatial$": inspect_spatial_computing,
        r"terminal-integration$": inspect_spatial_computing,
        r"cockpit-interaction$": inspect_spatial_computing,
        r"unity-architect$": inspect_game_development,
        r"unity-multiplayer$": inspect_game_development,
        r"unity-shader$": inspect_game_development,
        r"unity-editor$": inspect_game_development,
        r"unreal-world$": inspect_game_development,
        r"unreal-technical$": inspect_game_development,
        r"unreal-systems$": inspect_game_development,
        r"unreal-multiplayer$": inspect_game_development,
        r"godot-shader$": inspect_game_development,
        r"godot-multiplayer$": inspect_game_development,
        r"godot-gameplay$": inspect_game_development,
        r"roblox-systems$": inspect_game_development,
        r"roblox-experience$": inspect_game_development,
        r"roblox-avatar$": inspect_game_development,
        r"blender-addon$": inspect_game_development,
        r"level-designer$": inspect_game_development,
        r"narrative-designer$": inspect_game_development,
        r"game-designer$": inspect_game_development,
        r"game-audio$": inspect_game_development,
        r"technical-artist$": inspect_game_development,
        r"financial-analyst$": inspect_finance,
        r"financial-forecaster$": inspect_finance,
        r"fpa-analyst$": inspect_finance,
        r"fraud-detector$": inspect_finance,
        r"investment-researcher$": inspect_finance,
        r"invoice-manager$": inspect_finance,
        r"tax-strategist$": inspect_finance,
        r"bookkeeper-controller$": inspect_finance,
        r"support-responder$": inspect_support,
        r"analytics-reporter$": inspect_support,
        r"executive-summary$": inspect_support,
        r"finance-tracker$": inspect_support,
        r"infrastructure-maintainer$": inspect_support,
        r"legal-compliance$": inspect_support,
        r"recruitment-specialist$": inspect_support,
        r"supply-chain$": inspect_support,
        r"accessibility-auditor$": inspect_testing,
        r"api-tester$": inspect_testing,
        r"embedded-qa$": inspect_testing,
        r"evidence-collector$": inspect_testing,
        r"performance-benchmarker$": inspect_testing,
        r"reality-checker$": inspect_testing,
        r"test-results-analyzer$": inspect_testing,
        r"tool-evaluator$": inspect_testing,
    }


def _role_patterns_group4() -> dict[str, InspectionFunc]:
    """_role_patterns_group4。
    :return: 返回处理结果。
    """
    return {
        r"workflow-optimizer$": inspect_testing,
        r"project-manager-senior$": inspect_project_management,
        r"project-shepherd$": inspect_project_management,
        r"jira-workflow$": inspect_project_management,
        r"experiment-tracker$": inspect_project_management,
        r"studio-producer$": inspect_project_management,
        r"studio-operations$": inspect_project_management,
        r"salesforce-architect$": inspect_specialized,
        r"korean-business$": inspect_specialized,
        r"french-consulting$": inspect_specialized,
        r"zk-steward$": inspect_specialized,
        r"technical-translator$": inspect_specialized,
        r"study-abroad$": inspect_specialized,
        r"workflow-architect$": inspect_specialized,
        r"risk-assessor$": inspect_specialized,
        r"pricing-optimizer$": inspect_specialized,
        r"model-qa$": inspect_specialized,
        r"meeting-assistant$": inspect_specialized,
        r"mcp-builder$": inspect_specialized,
        r"document-generator$": inspect_specialized,
        r"developer-advocate$": inspect_specialized,
        r"cultural-intelligence$": inspect_specialized,
        r"civil-engineer$": inspect_specialized,
        r"chief-of-staff$": inspect_specialized,
        r"ai-policy-writer$": inspect_specialized,
        r"sales-data-extraction$": inspect_specialized,
        r"retail-customer-returns$": inspect_specialized,
        r"report-distribution$": inspect_specialized,
        r"real-estate$": inspect_specialized,
        r"prompt-engineer$": inspect_specialized,
        r"lsp-index-engineer$": inspect_specialized,
        r"loan-officer$": inspect_specialized,
        r"legal-document-review$": inspect_specialized,
        r"legal-client-intake$": inspect_specialized,
        r"legal-billing$": inspect_specialized,
        r"language-translator$": inspect_specialized,
        r"identity-graph$": inspect_specialized,
        r"hr-onboarding$": inspect_specialized,
        r"hospitality-guest$": inspect_specialized,
        r"healthcare-marketing$": inspect_specialized,
        r"healthcare-customer$": inspect_specialized,
        r"government-digital$": inspect_specialized,
        r"gaokao-college$": inspect_specialized,
        r"data-consolidation$": inspect_specialized,
        r"corporate-training$": inspect_specialized,
        r"compliance-auditor$": inspect_specialized,
        r"blockchain-security$": inspect_specialized,
        r"automation-governance$": inspect_specialized,
        r"agents-orchestrator$": inspect_specialized,
        r"agentic-identity$": inspect_specialized,
        r"accounts-payable$": inspect_specialized,
    }

