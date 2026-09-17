# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
AI安全扫描服务 - 基于真实LLM调用
功能：
- 代码安全扫描（调用LLM分析代码安全性）
- OWASP Top 10漏洞检测
- 依赖漏洞扫描
- 配置安全审计
- 结构化漏洞报告生成
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from app.services.ai_engine import AIEngine

logger = logging.getLogger(__name__)

OWASP_TOP_10 = [
    "A01:2021 - Broken Access Control（访问控制失效）",
    "A02:2021 - Cryptographic Failures（加密失败）",
    "A03:2021 - Injection（注入）",
    "A04:2021 - Insecure Design（不安全设计）",
    "A05:2021 - Security Misconfiguration（安全配置错误）",
    "A06:2021 - Vulnerable and Outdated Components（脆弱和过时的组件）",
    "A07:2021 - Identification and Authentication Failures（身份识别和认证失败）",
    "A08:2021 - Software and Data Integrity Failures（软件和数据完整性失败）",
    "A09:2021 - Security Logging and Monitoring Failures（安全日志和监控失败）",
    "A10:2021 - Server-Side Request Forgery (SSRF)（服务器端请求伪造）",
]


class SecurityScanRequest:
    """安全扫描请求"""
    code: str
    language: str
    scan_type: str
    def __init__(
        self,
        code: str,
        language: str = "python",
        scan_type: str = "full",
    ) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param code: 参数 code
        :param language: 参数 language
        :param scan_type: 参数 scan_type
        :return: 返回处理结果。
        """
        self.code = code
        self.language = language
        self.scan_type = scan_type


class SecurityIssue:
    """安全漏洞"""
    type: str
    severity: str
    line: Optional[int]
    description: str
    recommendation: str
    def __init__(
        self,
        type: str,
        severity: str,
        line: Optional[int],
        description: str,
        recommendation: str,
    ) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param type: 参数 type
        :param severity: 参数 severity
        :param line: 参数 line
        :param description: 参数 description
        :param recommendation: 参数 recommendation
        :return: 返回处理结果。
        """
        self.type = type
        self.severity = severity
        self.line = line
        self.description = description
        self.recommendation = recommendation


class SecurityScanResult:
    """安全扫描结果"""
    scan_id: str
    status: str
    issues: List[SecurityIssue]
    summary: Dict[str, int]
    def __init__(
        self,
        scan_id: str,
        status: str,
        issues: List[SecurityIssue],
        summary: Dict[str, int],
    ) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param scan_id: 参数 scan_id
        :param status: 参数 status
        :param issues: 参数 issues
        :param summary: 参数 summary
        :return: 返回处理结果。
        """
        self.scan_id = scan_id
        self.status = status
        self.issues = issues
        self.summary = summary


def _build_security_scan_prompt(request: SecurityScanRequest) -> str:
    """构建安全扫描提示词

    Args:
        request: 安全扫描请求

    Returns:
        完整的提示词字符串
    """
    scan_focus = {
        "full": "全面扫描所有安全漏洞类型",
        "injection": "重点扫描注入漏洞（SQL注入、XSS、命令注入、LDAP注入）",
        "dependency": "重点扫描依赖漏洞和过时组件",
        "config": "重点扫描安全配置问题（JWT、CORS、HTTPS、密钥管理）",
    }.get(request.scan_type, "全面扫描所有安全漏洞类型")
    return f"""请对以下{request.language}代码进行安全扫描。

扫描重点：{scan_focus}

参考OWASP Top 10：
{chr(10).join(f'{i+1}. {item}' for i, item in enumerate(OWASP_TOP_10))}

源代码：
```{request.language}
{request.code}
```

请返回JSON格式的扫描结果：
{{
    "issues": [
        {{
            "type": "漏洞类型（如sql_injection, xss, command_injection等）",
            "severity": "严重级别（critical/high/medium/low）",
            "line": 42,
            "description": "漏洞详细描述",
            "recommendation": "修复建议"
        }}
    ],
    "summary": {{
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }}
}}

如果没有发现安全问题，返回空的issues数组。只返回JSON，不要添加其他文本。"""


def _parse_security_response(
    response_text: str, scan_id: str
) -> SecurityScanResult:
    """解析LLM返回的安全扫描JSON

    Args:
        response_text: LLM返回的文本
        scan_id: 扫描ID

    Returns:
        解析后的SecurityScanResult
    """
    try:
        text = response_text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        data = json.loads(text)
        issues = [
            SecurityIssue(
                type=issue.get("type", "unknown"),
                severity=issue.get("severity", "low"),
                line=issue.get("line"),
                description=issue.get("description", ""),
                recommendation=issue.get("recommendation", ""),
            )
            for issue in data.get("issues", [])
        ]
        summary = data.get("summary", {})
        # 确保所有严重级别都有计数值
        for level in ("critical", "high", "medium", "low"):
            summary.setdefault(level, 0)

        return SecurityScanResult(
            scan_id=scan_id,
            status="completed",
            issues=issues,
            summary=summary,
        )
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning(f"Failed to parse security scan response: {e}")
        return SecurityScanResult(
            scan_id=scan_id,
            status="parse_error",
            issues=[],
            summary={"critical": 0, "high": 0, "medium": 0, "low": 0},
        )


async def scan_code_security(request: SecurityScanRequest) -> SecurityScanResult:
    """AI驱动的代码安全扫描

    调用AIEngine分析代码安全性，检测OWASP Top 10漏洞

    Args:
        request: 安全扫描请求，包含代码、语言和扫描类型

    Returns:
        SecurityScanResult包含发现的漏洞和严重程度摘要
    """
    scan_id = f"scan-{uuid.uuid4().hex[:8]}"
    engine = AIEngine()
    if not engine.is_available():
        logger.warning("AIEngine not available, returning empty scan result")
        return SecurityScanResult(
            scan_id=scan_id,
            status="degraded",
            issues=[],
            summary={"critical": 0, "high": 0, "medium": 0, "low": 0},
        )

    try:
        prompt = _build_security_scan_prompt(request)
        result = await engine.generate(
            prompt=prompt,
            max_tokens=3000,
            task_complexity="complex",
        )
        content = result.get("content", "")
        return _parse_security_response(content, scan_id)
    except Exception as e:
        logger.error(f"scan_code_security failed: {e}")
        return SecurityScanResult(
            scan_id=scan_id,
            status="error",
            issues=[],
            summary={"critical": 0, "high": 0, "medium": 0, "low": 0},
        )


async def scan_dependencies(project_path: str) -> SecurityScanResult:
    """依赖漏洞扫描

    读取项目依赖文件（requirements.txt/package.json等），
    调用AIEngine分析是否存在已知漏洞

    Args:
        project_path: 项目路径

    Returns:
        SecurityScanResult包含依赖漏洞和严重程度摘要
    """
    scan_id = f"dep-scan-{uuid.uuid4().hex[:8]}"
    engine = AIEngine()
    if not engine.is_available():
        return SecurityScanResult(
            scan_id=scan_id,
            status="degraded",
            issues=[],
            summary={"critical": 0, "high": 0, "medium": 0, "low": 0},
        )

    # 尝试读取依赖文件
    import os
    dep_content = ""
    dep_files = [
        "requirements.txt",
        "Pipfile",
        "pyproject.toml",
        "package.json",
        "package-lock.json",
        "yarn.lock",
    ]
    for dep_file in dep_files:
        file_path = os.path.join(project_path, dep_file)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    dep_content += f"\n# {dep_file}\n{f.read()[:2000]}\n"
            except Exception as e:
                logger.warning(f"Failed to read {dep_file}: {e}")

    if not dep_content:
        return SecurityScanResult(
            scan_id=scan_id,
            status="completed",
            issues=[],
            summary={"critical": 0, "high": 0, "medium": 0, "low": 0},
        )

    try:
        prompt = f"""分析以下项目依赖是否存在已知安全漏洞。

参考OWASP A06:2021（脆弱和过时的组件）和CVE数据库。

依赖文件内容：
{dep_content[:4000]}

请返回JSON格式：
{{
    "issues": [
        {{
            "type": "vulnerable_dependency",
            "severity": "high",
            "line": null,
            "description": "依赖包xxx存在CVE-2024-xxxx漏洞",
            "recommendation": "升级到xxx版本以上"
        }}
    ],
    "summary": {{
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }}
}}

只返回JSON，不要添加其他文本。"""

        result = await engine.generate(
            prompt=prompt,
            max_tokens=2000,
            task_complexity="medium",
        )
        content = result.get("content", "")
        return _parse_security_response(content, scan_id)
    except Exception as e:
        logger.error(f"scan_dependencies failed: {e}")
        return SecurityScanResult(
            scan_id=scan_id,
            status="error",
            issues=[],
            summary={"critical": 0, "high": 0, "medium": 0, "low": 0},
        )
