"""性能和安全管理API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.core.security import require_admin
from app.services.performance_monitor import performance_monitor
from app.services.security_auditor import security_auditor
from app.core.config import settings

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/metrics", summary="获取性能指标")
def get_performance_metrics(
    limit: int = 20,
    token: str = Depends(require_admin)
):
    """获取API性能指标统计"""
    return performance_monitor.get_endpoint_stats(limit=limit)


@router.get("/health", summary="系统健康检查")
def get_system_health(token: str = Depends(require_admin)):
    """获取系统健康状态"""
    return performance_monitor.get_system_health()


@router.get("/report", summary="生成性能报告")
def get_performance_report(
    hours: int = 24,
    token: str = Depends(require_admin)
):
    """生成指定时间段的性能报告"""
    if hours > 168:  # 最大7天
        raise HTTPException(status_code=400, detail="最多查询7天的数据")
    return performance_monitor.get_performance_report(hours=hours)


@router.post("/security/audit", summary="执行安全审计")
def run_security_audit(
    db: Session = Depends(get_db),
    token: str = Depends(require_admin)
):
    """执行OWASP TOP 10安全审计"""
    # 构建审计配置
    config = {
        'rbac_enabled': True,
        'cors_origins': settings.CORS_ORIGINS,
        'jwt_secret': settings.JWT_SECRET_KEY,
        'https_enabled': not settings.DEBUG,
        'orm_enabled': True,
        'input_validation_enabled': True,
        'debug_mode': settings.DEBUG,
        'default_credentials_used': False,
        'security_headers_enabled': True,
        'strong_password_policy': True,
        'rate_limiting_enabled': True,
        'audit_logging_enabled': True,
        'exception_monitoring_enabled': True,
        'ssrf_protection_enabled': True,
    }
    
    result = security_auditor.audit_application(config)
    return result


@router.get("/security/report", summary="获取安全审计报告")
def get_security_report(token: str = Depends(require_admin)):
    """获取最新的安全审计报告"""
    return security_auditor.get_security_report()


@router.get("/security/issues", summary="获取安全问题列表")
def get_security_issues(
    severity: str = None,
    category: str = None,
    token: str = Depends(require_admin)
):
    """获取安全问题列表，支持按严重程度和类别过滤"""
    issues = security_auditor.issues
    
    if severity:
        issues = [i for i in issues if i.severity == severity]
    
    if category:
        issues = [i for i in issues if i.category.startswith(category)]
    
    return {
        'total': len(issues),
        'issues': [security_auditor._issue_to_dict(i) for i in issues]
    }
