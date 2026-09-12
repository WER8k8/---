"""代码质量 API — FIX-70~73

- ESLint/Prettier/Vitest 配置生成
- TypeScript 严格类型合规追踪
- 自动化代码审查
- SonarQube 集成
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends

from app.core.security import get_current_user
from app.core.response import success_response
from app.services.ubrain.code_quality_service import (
    frontend_config_generator,
    type_compliance_tracker,
    code_review_engine,
    sonarqube_integration,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["代码质量"]

router = APIRouter(prefix="/code-quality", tags=["代码质量"])


# ═══════════════════════════════════════════════════════════
# FIX-70: 前端代码质量配置
# ═══════════════════════════════════════════════════════════

@router.get("/config/eslint")
def get_eslint_config(current_user=Depends(get_current_user)):
    """获取 ESLint 配置（Vue 3 + TypeScript）。"""
    return success_response(data=frontend_config_generator.generate_eslint_config())


@router.get("/config/prettier")
def get_prettier_config(current_user=Depends(get_current_user)):
    """获取 Prettier 配置。"""
    return success_response(data=frontend_config_generator.generate_prettier_config())


@router.get("/config/vitest")
def get_vitest_config(current_user=Depends(get_current_user)):
    """获取 Vitest 配置。"""
    return success_response(data=frontend_config_generator.generate_vitest_config())


@router.get("/config/all")
def get_all_configs(current_user=Depends(get_current_user)):
    """获取全部前端代码质量配置。"""
    return success_response(data=frontend_config_generator.generate_all_configs())


# ═══════════════════════════════════════════════════════════
# FIX-71: 全栈严格类型化
# ═══════════════════════════════════════════════════════════

@router.get("/type-compliance/report")
def get_type_compliance_report(current_user=Depends(get_current_user)):
    """获取 TypeScript 严格类型合规报告。"""
    report = type_compliance_tracker.scan_project()
    return success_response(data=report.to_dict())


@router.get("/type-compliance/tsconfig")
def get_strict_tsconfig(current_user=Depends(get_current_user)):
    """获取严格模式 tsconfig.json 模板。"""
    return success_response(data=type_compliance_tracker.generate_tsconfig_strict())


# ═══════════════════════════════════════════════════════════
# FIX-72: 代码审查自动化
# ═══════════════════════════════════════════════════════════

@router.post("/review/file")
def review_file(
    file_path: str = Body(..., description="文件路径"),
    content: str = Body(..., description="文件内容"),
    current_user=Depends(get_current_user),
):
    """审查单个文件。"""
    result = code_review_engine.review_file(file_path, content)
    return success_response(data={
        "file": result.file_path,
        "score": result.score,
        "passed": result.passed,
        "issues": result.issues,
    })


@router.post("/review/batch")
def review_batch(
    files: dict[str, str] = Body(..., description="文件映射 {path: content}"),
    current_user=Depends(get_current_user),
):
    """批量审查文件。"""
    result = code_review_engine.review_batch(files)
    return success_response(data=result)


@router.get("/review/rules")
def get_review_rules(current_user=Depends(get_current_user)):
    """获取审查规则列表。"""
    return success_response(data={
        "security": code_review_engine.SECURITY_RULES,
        "performance": code_review_engine.PERFORMANCE_RULES,
        "style": code_review_engine.STYLE_RULES,
    })


# ═══════════════════════════════════════════════════════════
# FIX-73: SonarQube 集成
# ═══════════════════════════════════════════════════════════

@router.get("/sonarqube/status")
def sonarqube_status(current_user=Depends(get_current_user)):
    """SonarQube 集成状态。"""
    return success_response(data={
        "configured": sonarqube_integration.is_configured(),
    })


@router.post("/sonarqube/scan")
def sonarqube_scan(current_user=Depends(get_current_user)):
    """获取 SonarScanner 扫描命令。"""
    if not sonarqube_integration.is_configured():
        return success_response(data={"error": "SonarQube 未配置"})
    return success_response(data=sonarqube_integration.generate_scan_command())


@router.get("/sonarqube/quality-gate")
def sonarqube_quality_gate(current_user=Depends(get_current_user)):
    """获取质量阈配置建议。"""
    return success_response(data=sonarqube_integration.generate_quality_gate_config())


@router.get("/sonarqube/results")
def sonarqube_results(current_user=Depends(get_current_user)):
    """获取模拟扫描结果（实际环境需调用 SonarQube API）。"""
    return success_response(data=sonarqube_integration.mock_scan_results())