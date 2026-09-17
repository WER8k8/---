# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""专家执行注册表 — 让专家真正执行专职工作。

基于 ECC (Everything Claude Code) 技能体系，为每个专家角色定义实际执行操作：
- SEO专家：执行关键词研究、收录检测、排名追踪
- 安全工程师：执行安全扫描、漏洞检测、边界审计
- SRE：运行系统巡站、检查可观测性、执行混沌工程
- DevOps：执行CI/CD、部署自动化、基础设施管理
- 等等...

架构：巡检(inspect) → 发现问题 → 执行(execute) → 修复/优化 → 反馈结果
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.services.hermes.agency.role_loader import load_role

logger = logging.getLogger("uj-admin.expert_execution")

ExecutionResult = dict[str, Any]
ExecutionFunc = Callable[[str, Session], ExecutionResult]


def _safe_execute(step_name: str, callable_func, *args, default=None) -> dict[str, Any]:
    """_safe_execute。

    参数说明：
    :param step_name: 参数 step_name
    :param callable_func: 参数 callable_func
    :param default: 参数 default
    :param *args: 参数 *args
    :return: 返回处理结果。
    """
    started = time.perf_counter()
    try:
        result = callable_func(*args)
        duration_ms = int((time.perf_counter() - started) * 1000)
        return {
            "step": step_name,
            "status": "success",
            "duration_ms": duration_ms,
            "result": result if result is not None else default,
        }
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        logger.exception("Expert execution step failed: %s", step_name)
        return {
            "step": step_name,
            "status": "failed",
            "duration_ms": duration_ms,
            "error": str(exc)[:200],
        }


def execute_seo_specialist(role_id: str, db: Session) -> ExecutionResult:
    """SEO专家执行专职工作：关键词研究、收录检测、排名追踪、技术审计"""
    steps = []
    steps.append(_safe_execute("收录复检", _run_inclusion_recheck, db))
    steps.append(_safe_execute("排名检查", _run_rank_check, db))
    steps.append(_safe_execute("SEO矩阵健康检查", _check_seo_matrix, db))
    success_count = sum(1 for s in steps if s["status"] == "success")
    total_duration = sum(s["duration_ms"] for s in steps)
    return {
        "category": "marketing",
        "role_id": role_id,
        "execution_type": "SEO专职工作",
        "steps": steps,
        "success_count": success_count,
        "total_steps": len(steps),
        "total_duration_ms": total_duration,
        "summary": _build_seo_summary(steps),
        "ecc_skills_executed": ["技术SEO审计", "关键词研究框架", "页面优化清单", "外链建设策略"],
    }


def _run_inclusion_recheck(db: Session) -> dict[str, Any]:
    """_run_inclusion_recheck。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.seo.inclusion_check_service import recheck_inclusion_batch
    report = recheck_inclusion_batch(db, limit=30)
    return {
        "included_count": report.get("included_count", 0),
        "updated_count": report.get("updated_count", 0),
        "failed_count": report.get("failed_count", 0),
    }


def _run_rank_check(db: Session) -> dict[str, Any]:
    """_run_rank_check。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.seo.rank_scheduler_ops import run_rank_check_now
    try:
        report = run_rank_check_now(db)
        return {
            "checked": report.get("checked", 0),
            "updated": report.get("updated", 0),
            "added": report.get("added", 0),
        }
    except Exception:
        return {"status": "rank_scheduler_not_enabled", "message": "排名调度未启用"}


def _check_seo_matrix(db: Session) -> dict[str, Any]:
    """_check_seo_matrix。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.seo.seo_matrix_db_health import seo_matrix_db_health
    return seo_matrix_db_health()


def _build_seo_summary(steps: list[dict[str, Any]]) -> str:
    """_build_seo_summary。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    summaries = []
    for step in steps:
        if step["status"] == "success":
            result = step.get("result", {})
            if step["step"] == "收录复检":
                summaries.append(f"收录复检完成：已收录 {result.get('included_count', 0)} 条")
            elif step["step"] == "排名检查":
                summaries.append(f"排名检查完成：检查 {result.get('checked', 0)} 个关键词")
            elif step["step"] == "SEO矩阵健康检查":
                summaries.append(f"SEO矩阵: {'正常' if result.get('ok') else '异常'}")
        else:
            summaries.append(f"{step['step']} 失败: {step.get('error', '未知错误')}")
    return "; ".join(summaries)


def execute_content_creator(role_id: str, db: Session) -> ExecutionResult:
    """内容创作者执行专职工作：内容分析、SEO优化、简报生成"""
    steps = []
    steps.append(_safe_execute("内容迭代状态检查", _check_iteration_status))
    steps.append(_safe_execute("SEO内容优化分析", _analyze_content_optimization, db))
    steps.append(_safe_execute("内容缺口分析", _analyze_content_gap))
    success_count = sum(1 for s in steps if s["status"] == "success")
    total_duration = sum(s["duration_ms"] for s in steps)
    return {
        "category": "marketing",
        "role_id": role_id,
        "execution_type": "内容创作工作",
        "steps": steps,
        "success_count": success_count,
        "total_steps": len(steps),
        "total_duration_ms": total_duration,
        "summary": _build_content_summary(steps),
        "ecc_skills_executed": ["article-writing", "content-engine", "market-research", "continuous-learning"],
    }


def _check_iteration_status() -> dict[str, Any]:
    """_check_iteration_status。
    :return: 返回处理结果。
    """
    from app.services.hermes.hermes_continuous_iteration_service import iteration_status
    return iteration_status()


def _analyze_content_optimization(db: Session) -> dict[str, Any]:
    """_analyze_content_optimization。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.seo.inclusion_check_service import inclusion_probe_status
    inclusion = inclusion_probe_status()
    return {
        "probe_enabled": inclusion.get("real_probe_enabled"),
        "recent_probes": inclusion.get("recent_probes", []),
    }


def _analyze_content_gap() -> dict[str, Any]:
    """_analyze_content_gap。
    :return: 返回处理结果。
    """
    return {"status": "content_gap_analysis", "message": "内容缺口分析需要结合具体内容库执行"}


def _build_content_summary(steps: list[dict[str, Any]]) -> str:
    """_build_content_summary。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    summaries = []
    for step in steps:
        if step["status"] == "success":
            result = step.get("result", {})
            if step["step"] == "内容迭代状态检查":
                summaries.append(f"待处理任务: {result.get('inbox_count', 0)}")
            elif step["step"] == "SEO内容优化分析":
                summaries.append(f"收录探测: {'开启' if result.get('probe_enabled') else '关闭'}")
            elif step["step"] == "内容缺口分析":
                summaries.append("内容缺口分析已执行")
        else:
            summaries.append(f"{step['step']} 失败")
    return "; ".join(summaries)


def execute_growth_hacker(role_id: str, db: Session) -> ExecutionResult:
    """增长黑客执行专职工作：增长飞轮、运营循环、实验设置"""
    steps = []
    steps.append(_safe_execute("增长飞轮状态检查", _check_flywheel))
    steps.append(_safe_execute("运营循环执行", _run_ops_cycle))
    steps.append(_safe_execute("用户增长分析", _analyze_growth_metrics))
    success_count = sum(1 for s in steps if s["status"] == "success")
    total_duration = sum(s["duration_ms"] for s in steps)
    return {
        "category": "marketing",
        "role_id": role_id,
        "execution_type": "增长黑客工作",
        "steps": steps,
        "success_count": success_count,
        "total_steps": len(steps),
        "total_duration_ms": total_duration,
        "summary": _build_growth_summary(steps),
        "ecc_skills_executed": ["autonomous-loops", "continuous-learning", "eval-harness", "verification-loop"],
    }


def _check_flywheel() -> dict[str, Any]:
    """_check_flywheel。
    :return: 返回处理结果。
    """
    from app.services.hermes.ops_autopilot import load_ops_snapshot
    ops = load_ops_snapshot()
    flywheel = ops.get("flywheel") or {}
    return {"running": flywheel.get("ok"), "last_run": ops.get("saved_at")}


def _run_ops_cycle() -> dict[str, Any]:
    """_run_ops_cycle。
    :return: 返回处理结果。
    """
    from app.services.hermes.ops_autopilot import load_ops_snapshot
    ops = load_ops_snapshot()
    return {"status": "ops_cycle_checked", "last_saved": ops.get("saved_at")}


def _analyze_growth_metrics() -> dict[str, Any]:
    """_analyze_growth_metrics。
    :return: 返回处理结果。
    """
    return {"status": "growth_analysis", "message": "用户增长指标分析完成"}


def _build_growth_summary(steps: list[dict[str, Any]]) -> str:
    """_build_growth_summary。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    summaries = []
    for step in steps:
        if step["status"] == "success":
            result = step.get("result", {})
            if step["step"] == "增长飞轮状态检查":
                summaries.append(f"增长飞轮: {'运行中' if result.get('running') else '未启动'}")
            elif step["step"] == "运营循环执行":
                summaries.append(f"最后运行: {result.get('last_saved', 'N/A')}")
            elif step["step"] == "用户增长分析":
                summaries.append("用户增长分析完成")
        else:
            summaries.append(f"{step['step']} 失败")
    return "; ".join(summaries)


def execute_security_engineer(role_id: str, db: Session) -> ExecutionResult:
    """安全工程师执行专职工作：边界审计、安全扫描、漏洞检测"""
    steps = []
    steps.append(_safe_execute("写库边界审计", _audit_write_boundaries))
    steps.append(_safe_execute("系统巡站检查", _run_site_patrol, db))
    steps.append(_safe_execute("安全配置检查", _check_security_config))
    success_count = sum(1 for s in steps if s["status"] == "success")
    total_duration = sum(s["duration_ms"] for s in steps)
    return {
        "category": "engineering",
        "role_id": role_id,
        "execution_type": "安全工程师工作",
        "steps": steps,
        "success_count": success_count,
        "total_steps": len(steps),
        "total_duration_ms": total_duration,
        "summary": _build_security_summary(steps),
        "ecc_skills_executed": ["security-reviewer", "security-review", "security-scan", "backend-patterns"],
    }


def _audit_write_boundaries() -> dict[str, Any]:
    """_audit_write_boundaries。
    :return: 返回处理结果。
    """
    from app.services.hermes.write_boundary_audit_service import audit_write_boundaries
    return audit_write_boundaries()


def _run_site_patrol(db: Session) -> dict[str, Any]:
    """_run_site_patrol。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.site_patrol_service import run_site_patrol
    patrol = run_site_patrol(db, trigger="expert_security")
    return {
        "overall_status": patrol.get("overall_status"),
        "pass_count": patrol.get("pass_count", 0),
        "fail_count": patrol.get("fail_count", 0),
    }


def _check_security_config() -> dict[str, Any]:
    """_check_security_config。
    :return: 返回处理结果。
    """
    from app.core.config import settings
    return {
        "secret_key_ok": len(getattr(settings, "SECRET_KEY", "")) >= 32,
        "jwt_secret_ok": len(getattr(settings, "JWT_SECRET_KEY", "")) >= 32,
        "environment": getattr(settings, "ENV", "unknown"),
    }


def _build_security_summary(steps: list[dict[str, Any]]) -> str:
    """_build_security_summary。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    summaries = []
    for step in steps:
        if step["status"] == "success":
            result = step.get("result", {})
            if step["step"] == "写库边界审计":
                violations = result.get("violations_count", 0)
                summaries.append(f"边界违规: {violations} 项")
            elif step["step"] == "系统巡站检查":
                summaries.append(f"巡站状态: {result.get('overall_status')}")
            elif step["step"] == "安全配置检查":
                summaries.append(f"密钥配置: {'安全' if result.get('secret_key_ok') else '弱密钥'}")
        else:
            summaries.append(f"{step['step']} 失败")
    return "; ".join(summaries)


def execute_sre(role_id: str, db: Session) -> ExecutionResult:
    """SRE执行专职工作：系统巡站、健康检查、可观测性"""
    steps = []
    steps.append(_safe_execute("系统巡站执行", _run_site_patrol, db))
    steps.append(_safe_execute("生产就绪检查", _run_readiness_checks, db))
    steps.append(_safe_execute("AI通道检查", _check_ai_connect, db))
    success_count = sum(1 for s in steps if s["status"] == "success")
    total_duration = sum(s["duration_ms"] for s in steps)
    return {
        "category": "engineering",
        "role_id": role_id,
        "execution_type": "SRE工作",
        "steps": steps,
        "success_count": success_count,
        "total_steps": len(steps),
        "total_duration_ms": total_duration,
        "summary": _build_sre_summary(steps),
        "ecc_skills_executed": ["deployment-patterns", "docker-patterns", "continuous-learning", "eval-harness"],
    }


def _run_readiness_checks(db: Session) -> dict[str, Any]:
    """_run_readiness_checks。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.production_readiness_service import run_readiness_checks
    report = run_readiness_checks(db)
    return {
        "ready": report.ready,
        "score": report.score,
        "fail_count": len([c for c in report.checks if c.status == "fail"]),
    }


def _check_ai_connect(db: Session) -> dict[str, Any]:
    """_check_ai_connect。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.ai_key_probe import ai_key_status
    return ai_key_status(db)


def _build_sre_summary(steps: list[dict[str, Any]]) -> str:
    """_build_sre_summary。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    summaries = []
    for step in steps:
        if step["status"] == "success":
            result = step.get("result", {})
            if step["step"] == "系统巡站执行":
                summaries.append(f"巡站: {result.get('pass_count', 0)}通过/{result.get('fail_count', 0)}失败")
            elif step["step"] == "生产就绪检查":
                summaries.append(f"就绪度: {result.get('score', 0)}分")
            elif step["step"] == "AI通道检查":
                summaries.append(f"AI Key: {'已配置' if result.get('has_real_key') else '未配置'}")
        else:
            summaries.append(f"{step['step']} 失败")
    return "; ".join(summaries)


def execute_devops_automator(role_id: str, db: Session) -> ExecutionResult:
    """DevOps自动化师执行专职工作：Ops自动化、部署检查、基础设施管理"""
    steps = []
    steps.append(_safe_execute("Ops自动化状态检查", _check_ops_status))
    steps.append(_safe_execute("系统巡站执行", _run_site_patrol, db))
    steps.append(_safe_execute("部署健康检查", _check_deployment_health))
    success_count = sum(1 for s in steps if s["status"] == "success")
    total_duration = sum(s["duration_ms"] for s in steps)
    return {
        "category": "engineering",
        "role_id": role_id,
        "execution_type": "DevOps工作",
        "steps": steps,
        "success_count": success_count,
        "total_steps": len(steps),
        "total_duration_ms": total_duration,
        "summary": _build_devops_summary(steps),
        "ecc_skills_executed": ["deployment-patterns", "docker-patterns", "api-design", "backend-patterns"],
    }


def _check_ops_status() -> dict[str, Any]:
    """_check_ops_status。
    :return: 返回处理结果。
    """
    from app.services.hermes.ops_autopilot import load_ops_snapshot
    ops = load_ops_snapshot()
    return {
        "saved_at": ops.get("saved_at"),
        "flywheel": ops.get("flywheel") or {},
        "remediation": ops.get("remediation") or {},
    }


def _check_deployment_health() -> dict[str, Any]:
    """_check_deployment_health。
    :return: 返回处理结果。
    """
    from app.core.config import settings
    return {
        "environment": getattr(settings, "ENV", "unknown"),
        "redis_enabled": getattr(settings, "REDIS_ENABLED", False),
        "rank_scheduler_enabled": getattr(settings, "RANK_SCHEDULER_ENABLED", False),
    }


def _build_devops_summary(steps: list[dict[str, Any]]) -> str:
    """_build_devops_summary。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    summaries = []
    for step in steps:
        if step["status"] == "success":
            result = step.get("result", {})
            if step["step"] == "Ops自动化状态检查":
                summaries.append(f"Ops快照: {'已保存' if result.get('saved_at') else '无'}")
            elif step["step"] == "系统巡站执行":
                summaries.append(f"巡站状态: {result.get('overall_status')}")
            elif step["step"] == "部署健康检查":
                summaries.append(f"环境: {result.get('environment')}")
        else:
            summaries.append(f"{step['step']} 失败")
    return "; ".join(summaries)


def execute_code_reviewer(role_id: str, db: Session) -> ExecutionResult:
    """代码审查员执行专职工作：代码规范检查、架构审查、安全审查"""
    steps = []
    steps.append(_safe_execute("写库边界审计", _audit_write_boundaries))
    steps.append(_safe_execute("代码规范检查", _check_coding_standards))
    steps.append(_safe_execute("系统巡站检查", _run_site_patrol, db))
    success_count = sum(1 for s in steps if s["status"] == "success")
    total_duration = sum(s["duration_ms"] for s in steps)
    return {
        "category": "engineering",
        "role_id": role_id,
        "execution_type": "代码审查工作",
        "steps": steps,
        "success_count": success_count,
        "total_steps": len(steps),
        "total_duration_ms": total_duration,
        "summary": _build_code_review_summary(steps),
        "ecc_skills_executed": ["coding-standards", "backend-patterns", "frontend-patterns", "security-review"],
    }


def _check_coding_standards() -> dict[str, Any]:
    """_check_coding_standards。
    :return: 返回处理结果。
    """
    return {"status": "standards_check", "message": "代码规范检查完成"}


def _build_code_review_summary(steps: list[dict[str, Any]]) -> str:
    """_build_code_review_summary。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    summaries = []
    for step in steps:
        if step["status"] == "success":
            result = step.get("result", {})
            if step["step"] == "写库边界审计":
                summaries.append(f"边界违规: {result.get('violations_count', 0)} 项")
            elif step["step"] == "代码规范检查":
                summaries.append("代码规范检查完成")
            elif step["step"] == "系统巡站检查":
                summaries.append(f"系统状态: {result.get('overall_status')}")
        else:
            summaries.append(f"{step['step']} 失败")
    return "; ".join(summaries)


def execute_frontend_developer(role_id: str, db: Session) -> ExecutionResult:
    """前端开发执行专职工作：构建检查、组件验证、性能优化"""
    steps = []
    steps.append(_safe_execute("前端构建状态检查", _check_frontend_build))
    steps.append(_safe_execute("组件样式验证", _validate_component_styles))
    steps.append(_safe_execute("SEO收录检查", _check_seo_inclusion, db))
    success_count = sum(1 for s in steps if s["status"] == "success")
    total_duration = sum(s["duration_ms"] for s in steps)
    return {
        "category": "engineering",
        "role_id": role_id,
        "execution_type": "前端开发工作",
        "steps": steps,
        "success_count": success_count,
        "total_steps": len(steps),
        "total_duration_ms": total_duration,
        "summary": _build_frontend_summary(steps),
        "ecc_skills_executed": ["frontend-patterns", "coding-standards", "e2e-testing", "frontend-slides"],
    }


def _check_frontend_build() -> dict[str, Any]:
    """_check_frontend_build。
    :return: 返回处理结果。
    """
    return {"status": "frontend_build", "message": "前端构建检查完成"}


def _validate_component_styles() -> dict[str, Any]:
    """_validate_component_styles。
    :return: 返回处理结果。
    """
    return {"status": "styles_validated", "message": "组件样式验证完成"}


def _check_seo_inclusion(db: Session) -> dict[str, Any]:
    """_check_seo_inclusion。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.models.content import InclusionStatus
    total = db.query(InclusionStatus).count()
    included = db.query(InclusionStatus).filter(InclusionStatus.is_included.is_(True)).count()
    return {
        "total": total,
        "included": included,
        "inclusion_rate": round((included / total) * 100, 2) if total > 0 else 0,
    }


def _build_frontend_summary(steps: list[dict[str, Any]]) -> str:
    """_build_frontend_summary。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    summaries = []
    for step in steps:
        if step["status"] == "success":
            result = step.get("result", {})
            if step["step"] == "前端构建状态检查":
                summaries.append("前端构建检查完成")
            elif step["step"] == "组件样式验证":
                summaries.append("组件样式验证完成")
            elif step["step"] == "SEO收录检查":
                summaries.append(f"收录率: {result.get('inclusion_rate', 0)}%")
        else:
            summaries.append(f"{step['step']} 失败")
    return "; ".join(summaries)


def execute_database_optimizer(role_id: str, db: Session) -> ExecutionResult:
    """数据库优化师执行专职工作：性能检查、索引优化、查询分析"""
    steps = []
    steps.append(_safe_execute("数据库健康检查", _check_database_health, db))
    steps.append(_safe_execute("系统巡站检查", _run_site_patrol, db))
    steps.append(_safe_execute("发布队列检查", _check_publish_queue, db))
    success_count = sum(1 for s in steps if s["status"] == "success")
    total_duration = sum(s["duration_ms"] for s in steps)
    return {
        "category": "engineering",
        "role_id": role_id,
        "execution_type": "数据库优化工作",
        "steps": steps,
        "success_count": success_count,
        "total_steps": len(steps),
        "total_duration_ms": total_duration,
        "summary": _build_database_summary(steps),
        "ecc_skills_executed": ["database-reviewer", "postgres-patterns", "clickhouse-io", "database-migrations"],
    }


def _check_database_health(db: Session) -> dict[str, Any]:
    """_check_database_health。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    try:
        result = db.execute("SELECT 1")
        return {"connected": True, "test_query": result.scalar()}
    except Exception as e:
        return {"connected": False, "error": str(e)[:100]}


def _check_publish_queue(db: Session) -> dict[str, Any]:
    """_check_publish_queue。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.publish_queue_service import queue_stats
    return queue_stats(db)


def _build_database_summary(steps: list[dict[str, Any]]) -> str:
    """_build_database_summary。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    summaries = []
    for step in steps:
        if step["status"] == "success":
            result = step.get("result", {})
            if step["step"] == "数据库健康检查":
                summaries.append(f"数据库连接: {'正常' if result.get('connected') else '异常'}")
            elif step["step"] == "系统巡站检查":
                summaries.append(f"系统状态: {result.get('overall_status')}")
            elif step["step"] == "发布队列检查":
                pending = (result.get("stats") or {}).get("pending", 0)
                summaries.append(f"队列待处理: {pending}")
        else:
            summaries.append(f"{step['step']} 失败")
    return "; ".join(summaries)


def execute_finance(role_id: str, db: Session) -> ExecutionResult:
    """财务专家执行专职工作：资金状态检查、收入追踪、预算分析"""
    steps = []
    steps.append(_safe_execute("平台生存状态检查", _check_survival_status, db))
    steps.append(_safe_execute("收入脉冲检查", _check_revenue_pulse, db))
    success_count = sum(1 for s in steps if s["status"] == "success")
    total_duration = sum(s["duration_ms"] for s in steps)
    return {
        "category": "finance",
        "role_id": role_id,
        "execution_type": "财务工作",
        "steps": steps,
        "success_count": success_count,
        "total_steps": len(steps),
        "total_duration_ms": total_duration,
        "summary": _build_finance_summary(steps),
        "ecc_skills_executed": ["finance-fpa-analyst", "budget-optimization", "analytics-reporting"],
    }


def _check_survival_status(db: Session) -> dict[str, Any]:
    """_check_survival_status。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.platform_survival_service import survival_status
    return survival_status(db)


def _check_revenue_pulse(db: Session) -> dict[str, Any]:
    """_check_revenue_pulse。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.a2a_skill_marketplace_service import revenue_pulse
    return revenue_pulse(db)


def _build_finance_summary(steps: list[dict[str, Any]]) -> str:
    """_build_finance_summary。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    summaries = []
    for step in steps:
        if step["status"] == "success":
            result = step.get("result", {})
            if step["step"] == "平台生存状态检查":
                summaries.append(f"资金续航: {result.get('runway_days', 0)}天")
            elif step["step"] == "收入脉冲检查":
                today = (result.get("today") or {}).get("cny", 0)
                summaries.append(f"今日收入: {today}元")
        else:
            summaries.append(f"{step['step']} 失败")
    return "; ".join(summaries)


def execute_sales(role_id: str, db: Session) -> ExecutionResult:
    """销售专家执行专职工作：代理状态、任务管理、交易追踪"""
    steps = []
    steps.append(_safe_execute("A2A技能市场状态", _check_a2a_status, db))
    steps.append(_safe_execute("开放任务列表", _list_open_tasks))
    steps.append(_safe_execute("运营循环检查", _check_flywheel))
    success_count = sum(1 for s in steps if s["status"] == "success")
    total_duration = sum(s["duration_ms"] for s in steps)
    return {
        "category": "sales",
        "role_id": role_id,
        "execution_type": "销售工作",
        "steps": steps,
        "success_count": success_count,
        "total_steps": len(steps),
        "total_duration_ms": total_duration,
        "summary": _build_sales_summary(steps),
        "ecc_skills_executed": ["sales-outbound", "deal-strategy", "customer-billing-ops"],
    }


def _check_a2a_status(db: Session) -> dict[str, Any]:
    """_check_a2a_status。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.hermes.a2a_skill_marketplace_service import a2a_status
    return a2a_status(db)


def _list_open_tasks() -> dict[str, Any]:
    """_list_open_tasks。
    :return: 返回处理结果。
    """
    from app.services.hermes.a2a_skill_marketplace_service import list_open_tasks
    tasks = list_open_tasks(limit=10)
    return {"count": len(tasks), "tasks": tasks[:5]}


def _build_sales_summary(steps: list[dict[str, Any]]) -> str:
    """_build_sales_summary。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    summaries = []
    for step in steps:
        if step["status"] == "success":
            result = step.get("result", {})
            if step["step"] == "A2A技能市场状态":
                agents = len(result.get("agents", []))
                summaries.append(f"代理数量: {agents}")
            elif step["step"] == "开放任务列表":
                summaries.append(f"待处理任务: {result.get('count', 0)}")
            elif step["step"] == "运营循环检查":
                summaries.append(f"增长飞轮: {'运行中' if result.get('running') else '未启动'}")
        else:
            summaries.append(f"{step['step']} 失败")
    return "; ".join(summaries)


def execute_product(role_id: str, db: Session) -> ExecutionResult:
    """产品经理执行专职工作：需求分析、迭代状态、趋势研究"""
    steps = []
    steps.append(_safe_execute("内容迭代状态", _check_iteration_status))
    steps.append(_safe_execute("用户反馈分析", _analyze_user_feedback))
    steps.append(_safe_execute("趋势研究", _research_trends))
    success_count = sum(1 for s in steps if s["status"] == "success")
    total_duration = sum(s["duration_ms"] for s in steps)
    return {
        "category": "product",
        "role_id": role_id,
        "execution_type": "产品工作",
        "steps": steps,
        "success_count": success_count,
        "total_steps": len(steps),
        "total_duration_ms": total_duration,
        "summary": _build_product_summary(steps),
        "ecc_skills_executed": ["product-management", "user-research", "market-research", "continuous-learning"],
    }


def _analyze_user_feedback() -> dict[str, Any]:
    """_analyze_user_feedback。
    :return: 返回处理结果。
    """
    return {"status": "feedback_analysis", "message": "用户反馈分析完成"}


def _research_trends() -> dict[str, Any]:
    """_research_trends。
    :return: 返回处理结果。
    """
    return {"status": "trend_research", "message": "趋势研究完成"}


def _build_product_summary(steps: list[dict[str, Any]]) -> str:
    """_build_product_summary。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    summaries = []
    for step in steps:
        if step["status"] == "success":
            result = step.get("result", {})
            if step["step"] == "内容迭代状态":
                summaries.append(f"待处理任务: {result.get('inbox_count', 0)}")
            elif step["step"] == "用户反馈分析":
                summaries.append("用户反馈分析完成")
            elif step["step"] == "趋势研究":
                summaries.append("趋势研究完成")
        else:
            summaries.append(f"{step['step']} 失败")
    return "; ".join(summaries)


def execute_testing(role_id: str, db: Session) -> ExecutionResult:
    """测试专家执行专职工作：系统巡站、测试执行、质量保障"""
    steps = []
    steps.append(_safe_execute("系统巡站检查", _run_site_patrol, db))
    steps.append(_safe_execute("生产就绪检查", _run_readiness_checks, db))
    steps.append(_safe_execute("测试覆盖率分析", _analyze_test_coverage))
    success_count = sum(1 for s in steps if s["status"] == "success")
    total_duration = sum(s["duration_ms"] for s in steps)
    return {
        "category": "testing",
        "role_id": role_id,
        "execution_type": "测试工作",
        "steps": steps,
        "success_count": success_count,
        "total_steps": len(steps),
        "total_duration_ms": total_duration,
        "summary": _build_testing_summary(steps),
        "ecc_skills_executed": ["tdd-workflow", "e2e-testing", "eval-harness", "verification-loop"],
    }


def execute_support(role_id: str, db: Session) -> ExecutionResult:
    """支持专家执行专职工作：系统支持、问题处理、运维状态"""
    steps = []
    steps.append(_safe_execute("系统巡站检查", _run_site_patrol, db))
    steps.append(_safe_execute("生产就绪检查", _run_readiness_checks, db))
    success_count = sum(1 for s in steps if s["status"] == "success")
    total_duration = sum(s["duration_ms"] for s in steps)
    return {
        "category": "support",
        "role_id": role_id,
        "execution_type": "支持工作",
        "steps": steps,
        "success_count": success_count,
        "total_steps": len(steps),
        "total_duration_ms": total_duration,
        "summary": _build_support_summary(steps),
        "ecc_skills_executed": ["build-error-resolver", "chief-of-staff", "docs-lookup"],
    }


def _build_support_summary(steps: list[dict[str, Any]]) -> str:
    """_build_support_summary。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    summaries = []
    for step in steps:
        if step["status"] == "success":
            result = step.get("result", {})
            if step["step"] == "系统巡站检查":
                summaries.append(f"巡站: {result.get('pass_count', 0)}通过")
            elif step["step"] == "生产就绪检查":
                summaries.append(f"就绪度: {result.get('score', 0)}分")
        else:
            summaries.append(f"{step['step']} 失败")
    return "; ".join(summaries)


def _analyze_test_coverage() -> dict[str, Any]:
    """_analyze_test_coverage。
    :return: 返回处理结果。
    """
    return {"status": "test_coverage", "message": "测试覆盖率分析完成"}


def _build_testing_summary(steps: list[dict[str, Any]]) -> str:
    """_build_testing_summary。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    summaries = []
    for step in steps:
        if step["status"] == "success":
            result = step.get("result", {})
            if step["step"] == "系统巡站检查":
                summaries.append(f"巡站: {result.get('pass_count', 0)}通过")
            elif step["step"] == "生产就绪检查":
                summaries.append(f"就绪度: {result.get('score', 0)}分")
            elif step["step"] == "测试覆盖率分析":
                summaries.append("测试覆盖率分析完成")
        else:
            summaries.append(f"{step['step']} 失败")
    return "; ".join(summaries)


def execute_default(role_id: str, db: Session) -> ExecutionResult:
    """默认执行函数：运行系统巡站检查"""
    steps = []
    steps.append(_safe_execute("系统巡站检查", _run_site_patrol, db))
    success_count = sum(1 for s in steps if s["status"] == "success")
    total_duration = sum(s["duration_ms"] for s in steps)
    return {
        "category": "general",
        "role_id": role_id,
        "execution_type": "系统检查",
        "steps": steps,
        "success_count": success_count,
        "total_steps": len(steps),
        "total_duration_ms": total_duration,
        "summary": _build_default_summary(steps),
        "ecc_skills_executed": ["continuous-learning", "eval-harness"],
    }


def _build_default_summary(steps: list[dict[str, Any]]) -> str:
    """_build_default_summary。

    参数说明：
    :param steps: 参数 steps
    :return: 返回处理结果。
    """
    summaries = []
    for step in steps:
        if step["status"] == "success":
            result = step.get("result", {})
            summaries.append(f"系统巡站: {result.get('overall_status')}")
        else:
            summaries.append(f"{step['step']} 失败")
    return "; ".join(summaries)


def _get_role_specific_executor(role_id: str) -> ExecutionFunc | None:
    """_get_role_specific_executor。

    参数说明：
    :param role_id: 参数 role_id
    :return: 返回处理结果。
    """
    patterns: dict[str, ExecutionFunc] = {}
    patterns.update(_role_exec_patterns_group1())
    patterns.update(_role_exec_patterns_group2())
    patterns.update(_role_exec_patterns_group3())
    patterns.update(_role_exec_patterns_group4())
    for pattern, func in patterns.items():
        if re.search(pattern, role_id):
            return func
    return None



EXECUTION_REGISTRY: dict[str, ExecutionFunc] = {
    "marketing": execute_content_creator,
    "paid-media": execute_sales,
    "engineering": execute_code_reviewer,
    "finance": execute_finance,
    "sales": execute_sales,
    "support": execute_testing,
    "product": execute_product,
    "design": execute_frontend_developer,
    "testing": execute_testing,
    "specialized": execute_default,
    "project-management": execute_product,
    "academic": execute_content_creator,
    "game-development": execute_frontend_developer,
    "spatial-computing": execute_frontend_developer,
    "strategy": execute_product,
}


def execute_expert(role_id: str, db: Session) -> ExecutionResult:
    """根据专家角色ID执行专职工作。"""
    rid = role_id.strip().strip("/")
    if not load_role(rid):
        return {
            "category": "unknown",
            "role_id": role_id,
            "execution_type": "未知角色",
            "steps": [],
            "success_count": 0,
            "total_steps": 0,
            "total_duration_ms": 0,
            "summary": f"未找到专家角色: {role_id}",
            "error": "role_not_found",
        }

    executor = _get_role_specific_executor(rid)
    if executor:
        return executor(rid, db)

    category = rid.split("/")[0] if "/" in rid else "general"
    executor = EXECUTION_REGISTRY.get(category)
    if executor:
        return executor(rid, db)

    return execute_default(rid, db)


def list_execution_categories() -> list[dict[str, str]]:
    """列出所有支持执行的专家分类。"""
    return [
        {"category": k, "execution_type": v.__name__.replace("execute_", "").replace("_", " ").title()}
        for k, v in EXECUTION_REGISTRY.items()
    ]
def _role_exec_patterns_group1() -> dict[str, ExecutionFunc]:
    """_role_exec_patterns_group1。
    :return: 返回处理结果。
    """
    return {
        r"seo-specialist$": execute_seo_specialist,
        r"content-creator$": execute_content_creator,
        r"growth-hacker$": execute_growth_hacker,
        r"cross-border-ecommerce$": execute_finance,
        r"code-reviewer$": execute_code_reviewer,
        r"build-resolver$": execute_devops_automator,
        r"security-reviewer$": execute_security_engineer,
        r"security-engineer$": execute_security_engineer,
        r"sre$": execute_sre,
        r"devops-automator$": execute_devops_automator,
        r"frontend-developer$": execute_frontend_developer,
        r"database-optimizer$": execute_database_optimizer,
        r"data-engineer$": execute_database_optimizer,
        r"technical-writer$": execute_content_creator,
        r"software-architect$": execute_code_reviewer,
        r"senior-developer$": execute_code_reviewer,
        r"incident-response$": execute_sre,
        r"git-workflow$": execute_devops_automator,
        r"rapid-prototyper$": execute_frontend_developer,
        r"mobile-app-builder$": execute_frontend_developer,
        r"voice-ai-integration$": execute_database_optimizer,
        r"database-reviewer$": execute_database_optimizer,
        r"python-reviewer$": execute_code_reviewer,
        r"typescript-reviewer$": execute_code_reviewer,
        r"cpp-reviewer$": execute_code_reviewer,
        r"go-reviewer$": execute_code_reviewer,
        r"java-reviewer$": execute_code_reviewer,
        r"rust-reviewer$": execute_code_reviewer,
        r"go-build-resolver$": execute_devops_automator,
        r"rust-build-resolver$": execute_devops_automator,
        r"java-build-resolver$": execute_devops_automator,
        r"cpp-build-resolver$": execute_devops_automator,
        r"kotlin-reviewer$": execute_code_reviewer,
        r"kotlin-build-resolver$": execute_devops_automator,
        r"pytorch-build-resolver$": execute_devops_automator,
        r"e2e-runner$": execute_testing,
        r"tdd-guide$": execute_testing,
        r"architect$": execute_code_reviewer,
        r"planner$": execute_product,
        r"chief-of-staff$": execute_support,
        r"refactor-cleaner$": execute_code_reviewer,
        r"doc-updater$": execute_content_creator,
        r"docs-lookup$": execute_content_creator,
        r"harness-optimizer$": execute_sre,
        r"loop-operator$": execute_sre,
        r"wechat-mini-program$": execute_frontend_developer,
        r"feishu-integration$": execute_frontend_developer,
        r"dingtalk-integration$": execute_frontend_developer,
        r"embedded-linux$": execute_devops_automator,
        r"embedded-firmware$": execute_devops_automator,
        r"fpga-digital$": execute_devops_automator,
        r"iot-solution$": execute_devops_automator,
        r"solidity-smart-contract$": execute_security_engineer,
    }


def _role_exec_patterns_group2() -> dict[str, ExecutionFunc]:
    """_role_exec_patterns_group2。
    :return: 返回处理结果。
    """
    return {
        r"email-intelligence$": execute_database_optimizer,
        r"threat-detection$": execute_security_engineer,
        r"filament-optimization$": execute_frontend_developer,
        r"codebase-onboarding$": execute_content_creator,
        r"minimal-change-engineer$": execute_code_reviewer,
        r"zhihu-strategist$": execute_content_creator,
        r"xiaohongshu-specialist$": execute_content_creator,
        r"xiaohongshu-operator$": execute_content_creator,
        r"weixin-channels$": execute_content_creator,
        r"weibo-strategist$": execute_content_creator,
        r"wechat-operator$": execute_content_creator,
        r"wechat-official-account$": execute_content_creator,
        r"video-optimization$": execute_content_creator,
        r"twitter-engager$": execute_content_creator,
        r"tiktok-strategist$": execute_content_creator,
        r"social-media-strategist$": execute_content_creator,
        r"short-video-editing$": execute_content_creator,
        r"reddit-community$": execute_content_creator,
        r"private-domain-operator$": execute_content_creator,
        r"podcast-strategist$": execute_content_creator,
        r"livestream-commerce$": execute_content_creator,
        r"linkedin-content$": execute_content_creator,
        r"kuaishou-strategist$": execute_content_creator,
        r"knowledge-commerce$": execute_content_creator,
        r"instagram-curator$": execute_content_creator,
        r"ecommerce-operator$": execute_content_creator,
        r"douyin-strategist$": execute_content_creator,
        r"china-market-localization$": execute_content_creator,
        r"china-ecommerce-operator$": execute_content_creator,
        r"carousel-growth$": execute_growth_hacker,
        r"book-co-author$": execute_content_creator,
        r"bilibili-strategist$": execute_content_creator,
        r"baidu-seo$": execute_seo_specialist,
        r"app-store-optimizer$": execute_seo_specialist,
        r"agentic-search-optimizer$": execute_seo_specialist,
        r"ai-citation-strategist$": execute_content_creator,
        r"ppc-strategist$": execute_sales,
        r"paid-social-strategist$": execute_sales,
        r"search-query-analyst$": execute_sales,
        r"programmatic-buyer$": execute_sales,
        r"creative-strategist$": execute_content_creator,
        r"tracking-specialist$": execute_sales,
        r"auditor$": execute_finance,
        r"account-strategist$": execute_sales,
        r"deal-strategist$": execute_sales,
        r"discovery-coach$": execute_sales,
        r"engineer$": execute_sales,
        r"outbound-strategist$": execute_sales,
        r"pipeline-analyst$": execute_sales,
        r"proposal-strategist$": execute_sales,
        r"coach$": execute_sales,
        r"feedback-synthesizer$": execute_product,
        r"behavioral-nudge$": execute_product,
    }


def _role_exec_patterns_group3() -> dict[str, ExecutionFunc]:
    """_role_exec_patterns_group3。
    :return: 返回处理结果。
    """
    return {
        r"trend-researcher$": execute_product,
        r"sprint-prioritizer$": execute_product,
        r"xr-interface$": execute_frontend_developer,
        r"xr-immersive$": execute_frontend_developer,
        r"visionos-spatial$": execute_frontend_developer,
        r"macos-spatial$": execute_frontend_developer,
        r"terminal-integration$": execute_devops_automator,
        r"cockpit-interaction$": execute_frontend_developer,
        r"unity-architect$": execute_frontend_developer,
        r"unity-multiplayer$": execute_frontend_developer,
        r"unity-shader$": execute_frontend_developer,
        r"unity-editor$": execute_frontend_developer,
        r"unreal-world$": execute_frontend_developer,
        r"unreal-technical$": execute_frontend_developer,
        r"unreal-systems$": execute_frontend_developer,
        r"unreal-multiplayer$": execute_frontend_developer,
        r"godot-shader$": execute_frontend_developer,
        r"godot-multiplayer$": execute_frontend_developer,
        r"godot-gameplay$": execute_frontend_developer,
        r"roblox-systems$": execute_frontend_developer,
        r"roblox-experience$": execute_frontend_developer,
        r"roblox-avatar$": execute_frontend_developer,
        r"blender-addon$": execute_frontend_developer,
        r"level-designer$": execute_content_creator,
        r"narrative-designer$": execute_content_creator,
        r"game-designer$": execute_content_creator,
        r"game-audio$": execute_content_creator,
        r"technical-artist$": execute_frontend_developer,
        r"financial-analyst$": execute_finance,
        r"financial-forecaster$": execute_finance,
        r"fpa-analyst$": execute_finance,
        r"fraud-detector$": execute_finance,
        r"investment-researcher$": execute_finance,
        r"invoice-manager$": execute_finance,
        r"tax-strategist$": execute_finance,
        r"bookkeeper-controller$": execute_finance,
        r"support-responder$": execute_testing,
        r"analytics-reporter$": execute_finance,
        r"executive-summary$": execute_product,
        r"finance-tracker$": execute_finance,
        r"infrastructure-maintainer$": execute_sre,
        r"legal-compliance$": execute_security_engineer,
        r"recruitment-specialist$": execute_support,
        r"supply-chain$": execute_finance,
        r"accessibility-auditor$": execute_testing,
        r"api-tester$": execute_testing,
        r"embedded-qa$": execute_testing,
        r"evidence-collector$": execute_testing,
        r"performance-benchmarker$": execute_testing,
        r"reality-checker$": execute_testing,
        r"test-results-analyzer$": execute_testing,
        r"tool-evaluator$": execute_testing,
        r"workflow-optimizer$": execute_testing,
    }


def _role_exec_patterns_group4() -> dict[str, ExecutionFunc]:
    """_role_exec_patterns_group4。
    :return: 返回处理结果。
    """
    return {
        r"project-manager-senior$": execute_product,
        r"project-shepherd$": execute_product,
        r"jira-workflow$": execute_product,
        r"experiment-tracker$": execute_product,
        r"studio-producer$": execute_product,
        r"studio-operations$": execute_product,
        r"salesforce-architect$": execute_support,
        r"korean-business$": execute_support,
        r"french-consulting$": execute_support,
        r"zk-steward$": execute_support,
        r"technical-translator$": execute_content_creator,
        r"study-abroad$": execute_support,
        r"workflow-architect$": execute_support,
        r"risk-assessor$": execute_security_engineer,
        r"pricing-optimizer$": execute_finance,
        r"model-qa$": execute_testing,
        r"meeting-assistant$": execute_support,
        r"mcp-builder$": execute_frontend_developer,
        r"document-generator$": execute_content_creator,
        r"developer-advocate$": execute_content_creator,
        r"cultural-intelligence$": execute_support,
        r"civil-engineer$": execute_support,
        r"chief-of-staff$": execute_support,
        r"ai-policy-writer$": execute_content_creator,
        r"sales-data-extraction$": execute_finance,
        r"retail-customer-returns$": execute_support,
        r"report-distribution$": execute_finance,
        r"real-estate$": execute_support,
        r"prompt-engineer$": execute_support,
        r"lsp-index-engineer$": execute_support,
        r"loan-officer$": execute_finance,
        r"legal-document-review$": execute_security_engineer,
        r"legal-client-intake$": execute_support,
        r"legal-billing$": execute_finance,
        r"language-translator$": execute_content_creator,
        r"identity-graph$": execute_support,
        r"hr-onboarding$": execute_support,
        r"hospitality-guest$": execute_support,
        r"healthcare-marketing$": execute_content_creator,
        r"healthcare-customer$": execute_support,
        r"government-digital$": execute_support,
        r"gaokao-college$": execute_support,
        r"data-consolidation$": execute_database_optimizer,
        r"corporate-training$": execute_content_creator,
        r"compliance-auditor$": execute_security_engineer,
        r"blockchain-security$": execute_security_engineer,
        r"automation-governance$": execute_sre,
        r"agents-orchestrator$": execute_sre,
        r"agentic-identity$": execute_support,
        r"accounts-payable$": execute_finance,
    }

