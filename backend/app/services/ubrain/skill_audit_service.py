"""技能安全审核服务 — 参考 CocoLoop BSS安全扫描体系。

CocoLoop 采用全链路安全审核：
- BSS安全扫描检测恶意代码、权限泄露、非法调用
- 风险等级划分为 S/A/B/C/D 五级
- VM级隔离执行环境，零信任代码运行

本服务实现类似的安全审核机制，为技能提供安全评分和风险评估。
"""

from __future__ import annotations

from typing import Any, Literal

from app.services.ubrain.accio_skill_catalog import load_skill_catalog


RiskLevel = Literal["S", "A", "B", "C", "D"]
AuditStatus = Literal["approved", "partial", "pending", "rejected"]


_RISK_LEVEL_DESCRIPTIONS: dict[RiskLevel, str] = {
    "S": "最高安全等级，经过严格审核，无任何安全风险",
    "A": "高安全等级，经过审核，基本无安全风险",
    "B": "中等安全等级，存在一些潜在风险，建议谨慎使用",
    "C": "较低安全等级，存在明显风险，需要人工审核",
    "D": "危险等级，存在严重安全风险，禁止使用",
}

_RISK_LEVEL_COLORS: dict[RiskLevel, str] = {
    "S": "#52c41a",
    "A": "#1890ff",
    "B": "#faad14",
    "C": "#ff7875",
    "D": "#ff4d4f",
}

_AUDIT_STATUS_DESCRIPTIONS: dict[AuditStatus, str] = {
    "approved": "已通过审核",
    "partial": "部分功能已审核",
    "pending": "审核中",
    "rejected": "审核未通过",
}


def analyze_skill_risk(skill_id: str) -> dict[str, Any]:
    """分析技能的安全风险等级"""
    catalog = load_skill_catalog()
    for group in catalog.get("groups", []):
        for skill in group.get("skills", []):
            if skill.get("id") == skill_id:
                risk_level = skill.get("risk_level", "B")
                audit_status = skill.get("audit_status", "pending")
                return {
                    "skill_id": skill_id,
                    "skill_name": skill.get("accio_analog", skill_id),
                    "risk_level": risk_level,
                    "risk_description": _RISK_LEVEL_DESCRIPTIONS.get(risk_level, ""),
                    "risk_color": _RISK_LEVEL_COLORS.get(risk_level, "#999"),
                    "audit_status": audit_status,
                    "audit_description": _AUDIT_STATUS_DESCRIPTIONS.get(audit_status, ""),
                    "rating": skill.get("rating", 0),
                    "users_count": skill.get("users_count", 0),
                    "implemented": skill.get("implemented", False),
                    "api": skill.get("api", ""),
                    "description": skill.get("description", ""),
                    "group_id": group.get("id", ""),
                    "group_name": group.get("name", ""),
                }
    
    return {
        "skill_id": skill_id,
        "skill_name": skill_id,
        "risk_level": "C",
        "risk_description": "技能未找到或未审核",
        "risk_color": "#ff7875",
        "audit_status": "pending",
        "audit_description": "等待审核",
        "rating": 0,
        "users_count": 0,
        "implemented": False,
        "api": "",
        "description": "",
        "group_id": "",
        "group_name": "",
    }


def scan_skill_code(skill_code: str) -> dict[str, Any]:
    """扫描技能代码中的安全风险（模拟实现）
    
    实际生产环境应集成：
    - 静态代码分析工具（如 Bandit、Semgrep）
    - 恶意代码检测
    - 权限泄露检测
    - 依赖安全扫描
    """
    issues: list[dict[str, Any]] = []
    score = 100
    code_lower = skill_code.lower()
    # 检测敏感操作
    sensitive_patterns = [
        ("os.system", "危险：直接执行系统命令", "high"),
        ("subprocess.", "警告：子进程调用", "medium"),
        ("exec(", "危险：动态代码执行", "high"),
        ("eval(", "警告：动态表达式求值", "medium"),
        ("__import__", "警告：动态导入", "low"),
        ("open(", "注意：文件操作", "low"),
        ("socket.", "注意：网络操作", "low"),
        ("requests.", "注意：HTTP请求", "low"),
    ]
    for pattern, message, severity in sensitive_patterns:
        if pattern in code_lower:
            issues.append({
                "pattern": pattern,
                "message": message,
                "severity": severity,
                "line": skill_code.lower().count("\n", 0, code_lower.find(pattern)) + 1,
            })
            if severity == "high":
                score -= 30
            elif severity == "medium":
                score -= 15
            else:
                score -= 5
    
    if score >= 90:
        risk_level: RiskLevel = "S"
    elif score >= 75:
        risk_level = "A"
    elif score >= 60:
        risk_level = "B"
    elif score >= 40:
        risk_level = "C"
    else:
        risk_level = "D"
    
    return {
        "score": score,
        "risk_level": risk_level,
        "risk_description": _RISK_LEVEL_DESCRIPTIONS.get(risk_level, ""),
        "risk_color": _RISK_LEVEL_COLORS.get(risk_level, "#999"),
        "issues_count": len(issues),
        "issues": issues,
        "scan_summary": f"检测到 {len(issues)} 个潜在安全问题",
    }


def get_skill_catalog_with_security() -> dict[str, Any]:
    """获取包含安全信息的完整技能目录"""
    catalog = load_skill_catalog()
    for group in catalog.get("groups", []):
        for skill in group.get("skills", []):
            risk_level = skill.get("risk_level", "B")
            skill["risk_description"] = _RISK_LEVEL_DESCRIPTIONS.get(risk_level, "")
            skill["risk_color"] = _RISK_LEVEL_COLORS.get(risk_level, "#999")
            audit_status = skill.get("audit_status", "pending")
            skill["audit_description"] = _AUDIT_STATUS_DESCRIPTIONS.get(audit_status, "")
    
    catalog["risk_level_descriptions"] = _RISK_LEVEL_DESCRIPTIONS
    catalog["risk_level_colors"] = _RISK_LEVEL_COLORS
    return catalog


def search_skills(
    query: str = "",
    risk_level: str = "",
    audit_status: str = "",
    group_id: str = "",
    sort_by: str = "rating",
    sort_order: str = "desc",
) -> list[dict[str, Any]]:
    """搜索和筛选技能"""
    catalog = load_skill_catalog()
    skills: list[dict[str, Any]] = []
    for group in catalog.get("groups", []):
        if group_id and group.get("id") != group_id:
            continue
        
        for skill in group.get("skills", []):
            # 搜索关键词
            if query:
                query_lower = query.lower()
                match = (
                    query_lower in skill.get("id", "").lower()
                    or query_lower in skill.get("accio_analog", "").lower()
                    or query_lower in skill.get("description", "").lower()
                )
                if not match:
                    continue
            
            # 风险等级筛选
            if risk_level and skill.get("risk_level") != risk_level:
                continue
            
            # 审核状态筛选
            if audit_status and skill.get("audit_status") != audit_status:
                continue
            
            skills.append({
                **skill,
                "group_id": group.get("id"),
                "group_name": group.get("name"),
                "risk_description": _RISK_LEVEL_DESCRIPTIONS.get(skill.get("risk_level", "B"), ""),
                "risk_color": _RISK_LEVEL_COLORS.get(skill.get("risk_level", "B"), "#999"),
                "audit_description": _AUDIT_STATUS_DESCRIPTIONS.get(skill.get("audit_status", "pending"), ""),
            })
    
    # 排序
    if sort_by == "rating":
        skills.sort(key=lambda x: x.get("rating", 0), reverse=(sort_order == "desc"))
    elif sort_by == "users":
        skills.sort(key=lambda x: x.get("users_count", 0), reverse=(sort_order == "desc"))
    elif sort_by == "name":
        skills.sort(key=lambda x: x.get("accio_analog", x.get("id", "")), reverse=(sort_order == "desc"))
    
    return skills


def get_featured_collections() -> list[dict[str, Any]]:
    """获取精选技能集合"""
    catalog = load_skill_catalog()
    collections = catalog.get("featured_collections", [])
    for collection in collections:
        skill_ids = collection.get("skill_ids", [])
        collection["skills"] = []
        for group in catalog.get("groups", []):
            for skill in group.get("skills", []):
                if skill.get("id") in skill_ids:
                    collection["skills"].append({
                        **skill,
                        "group_id": group.get("id"),
                        "group_name": group.get("name"),
                    })
    
    return collections


def get_top_rated_skills(limit: int = 5) -> list[dict[str, Any]]:
    """获取评分最高的技能"""
    catalog = load_skill_catalog()
    top_ids = catalog.get("top_rated_skills", [])[:limit]
    top_skills: list[dict[str, Any]] = []
    for group in catalog.get("groups", []):
        for skill in group.get("skills", []):
            if skill.get("id") in top_ids:
                top_skills.append({
                    **skill,
                    "group_id": group.get("id"),
                    "group_name": group.get("name"),
                    "risk_description": _RISK_LEVEL_DESCRIPTIONS.get(skill.get("risk_level", "B"), ""),
                    "risk_color": _RISK_LEVEL_COLORS.get(skill.get("risk_level", "B"), "#999"),
                })
    
    top_skills.sort(key=lambda x: x.get("rating", 0), reverse=True)
    return top_skills
