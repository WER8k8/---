# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""安全审计服务 - OWASP TOP 10漏洞扫描与检测（AI驱动）"""

import logging
import re
import ast
import os
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logging_config import LogConfig
from app.services.ai_engine import AIEngine

logger = LogConfig.get_logger("security_auditor")


@dataclass
class SecurityIssue:
    """安全问题数据类"""
    category: str  # OWASP类别
    severity: str  # critical, high, medium, low
    title: str
    description: str
    recommendation: str
    cwe_id: Optional[str] = None  # CWE编号
    affected_endpoint: Optional[str] = None
    evidence: Optional[str] = None


class SecurityAuditor:
    """安全审计器 - 检测OWASP TOP 10漏洞"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.issues: List[SecurityIssue] = []
        self.scan_history: List[Dict[str, Any]] = []
        self.ai_engine = AIEngine()  # AI引擎用于代码分析
        # OWASP TOP 10 2021 类别
        self.owasp_categories = {
            "A01": "Broken Access Control",
            "A02": "Cryptographic Failures",
            "A03": "Injection",
            "A04": "Insecure Design",
            "A05": "Security Misconfiguration",
            "A06": "Vulnerable and Outdated Components",
            "A07": "Identification and Authentication Failures",
            "A08": "Software and Data Integrity Failures",
            "A09": "Security Logging and Monitoring Failures",
            "A10": "Server-Side Request Forgery",
        }

    def audit_application(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行全面安全审计"""
        self.issues = []
        # 执行各项安全检查
        self._check_access_control(config)
        self._check_cryptographic_failures(config)
        self._check_injection_vulnerabilities(config)
        self._check_security_misconfiguration(config)
        self._check_authentication_failures(config)
        self._check_logging_monitoring(config)
        self._check_ssrf_protection(config)
        # 记录扫描历史
        scan_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_issues": len(self.issues),
            "critical_count": sum(1 for i in self.issues if i.severity == "critical"),
            "high_count": sum(1 for i in self.issues if i.severity == "high"),
            "medium_count": sum(1 for i in self.issues if i.severity == "medium"),
            "low_count": sum(1 for i in self.issues if i.severity == "low"),
            "issues": [self._issue_to_dict(issue) for issue in self.issues],
        }
        self.scan_history.append(scan_result)
        # 限制历史记录数量
        if len(self.scan_history) > 100:
            self.scan_history = self.scan_history[-100:]

        return scan_result

    def _check_access_control(self, config: Dict[str, Any]):
        """A01: 检查访问控制"""
        # 检查RBAC配置
        if not config.get("rbac_enabled", False):
            self.issues.append(
                SecurityIssue(
                    category="A01:2021",
                    severity="high",
                    title="RBAC权限控制未启用",
                    description="系统未启用基于角色的访问控制，可能导致未授权访问",
                    recommendation="启用RBAC权限系统，确保所有API端点都有适当的权限验证",
                    cwe_id="CWE-284",
                )
            )

        # 检查CORS配置
        cors_origins = config.get("cors_origins", [])
        if "*" in cors_origins:
            self.issues.append(
                SecurityIssue(
                    category="A01:2021",
                    severity="medium",
                    title="CORS配置过于宽松",
                    description="CORS允许所有来源访问，可能遭受跨站请求伪造攻击",
                    recommendation="限制CORS为具体的可信域名",
                    cwe_id="CWE-942",
                )
            )

    def _check_cryptographic_failures(self, config: Dict[str, Any]):
        """A02: 检查加密失败"""
        # 检查JWT密钥强度
        jwt_secret = config.get("jwt_secret", "")
        if len(jwt_secret) < 32:
            self.issues.append(
                SecurityIssue(
                    category="A02:2021",
                    severity="high",
                    title="JWT密钥强度不足",
                    description=f"JWT密钥长度仅为{len(jwt_secret)}字符，建议至少32字符",
                    recommendation="使用强随机字符串作为JWT密钥，长度至少32字符",
                    cwe_id="CWE-328",
                )
            )

        # 检查HTTPS配置
        if not config.get("https_enabled", False):
            self.issues.append(
                SecurityIssue(
                    category="A02:2021",
                    severity="critical",
                    title="HTTPS未启用",
                    description="生产环境未启用HTTPS，数据传输存在被窃听风险",
                    recommendation="在生产环境强制启用HTTPS，配置SSL证书",
                    cwe_id="CWE-319",
                )
            )

    def _check_injection_vulnerabilities(self, config: Dict[str, Any]):
        """A03: 检查注入漏洞"""
        # 检查SQLAlchemy ORM使用
        if not config.get("orm_enabled", False):
            self.issues.append(
                SecurityIssue(
                    category="A03:2021",
                    severity="high",
                    title="未使用ORM防护SQL注入",
                    description="数据库查询未使用ORM，可能存在SQL注入风险",
                    recommendation="使用SQLAlchemy ORM或参数化查询防止SQL注入",
                    cwe_id="CWE-89",
                )
            )

        # 检查输入验证
        if not config.get("input_validation_enabled", False):
            self.issues.append(
                SecurityIssue(
                    category="A03:2021",
                    severity="medium",
                    title="输入验证未全面启用",
                    description="部分API端点可能缺少输入验证",
                    recommendation="对所有用户输入进行严格验证和清理",
                    cwe_id="CWE-20",
                )
            )

    def _check_security_misconfiguration(self, config: Dict[str, Any]):
        """A05: 检查安全配置错误"""
        # 检查调试模式
        if config.get("debug_mode", False):
            self.issues.append(
                SecurityIssue(
                    category="A05:2021",
                    severity="high",
                    title="生产环境调试模式启用",
                    description="调试模式在生产环境启用可能泄露敏感信息",
                    recommendation="在生产环境禁用DEBUG模式",
                    cwe_id="CWE-489",
                )
            )

        # 检查默认凭据
        if config.get("default_credentials_used", False):
            self.issues.append(
                SecurityIssue(
                    category="A05:2021",
                    severity="critical",
                    title="使用默认凭据",
                    description="系统使用默认用户名/密码，极易被攻击",
                    recommendation="立即修改所有默认凭据为强密码",
                    cwe_id="CWE-798",
                )
            )

        # 检查安全头配置
        if not config.get("security_headers_enabled", False):
            self.issues.append(
                SecurityIssue(
                    category="A05:2021",
                    severity="medium",
                    title="安全HTTP头未配置",
                    description="缺少X-Frame-Options、CSP等安全头",
                    recommendation="配置完整的安全HTTP头",
                    cwe_id="CWE-693",
                )
            )

    def _check_authentication_failures(self, config: Dict[str, Any]):
        """A07: 检查认证失败"""
        # 检查密码策略
        if not config.get("strong_password_policy", False):
            self.issues.append(
                SecurityIssue(
                    category="A07:2021",
                    severity="medium",
                    title="密码策略不够严格",
                    description="未强制执行强密码策略",
                    recommendation="要求密码至少8位，包含大小写字母、数字和特殊字符",
                    cwe_id="CWE-521",
                )
            )

        # 检查速率限制
        if not config.get("rate_limiting_enabled", False):
            self.issues.append(
                SecurityIssue(
                    category="A07:2021",
                    severity="medium",
                    title="速率限制未启用",
                    description="登录接口缺少速率限制，可能遭受暴力破解",
                    recommendation="启用速率限制，特别是登录和注册接口",
                    cwe_id="CWE-307",
                )
            )

    def _check_logging_monitoring(self, config: Dict[str, Any]):
        """A09: 检查日志和监控"""
        # 检查审计日志
        if not config.get("audit_logging_enabled", False):
            self.issues.append(
                SecurityIssue(
                    category="A09:2021",
                    severity="high",
                    title="审计日志未启用",
                    description="关键操作未记录审计日志，无法追溯安全事件",
                    recommendation="启用完整的审计日志系统",
                    cwe_id="CWE-778",
                )
            )

        # 检查异常监控
        if not config.get("exception_monitoring_enabled", False):
            self.issues.append(
                SecurityIssue(
                    category="A09:2021",
                    severity="medium",
                    title="异常监控未配置",
                    description="缺少异常检测和告警机制",
                    recommendation="配置异常监控和实时告警",
                    cwe_id="CWE-778",
                )
            )

    def _check_ssrf_protection(self, config: Dict[str, Any]):
        """A10: 检查SSRF防护"""
        if not config.get("ssrf_protection_enabled", False):
            self.issues.append(
                SecurityIssue(
                    category="A10:2021",
                    severity="medium",
                    title="SSRF防护未启用",
                    description="外部URL请求缺少SSRF防护",
                    recommendation="实现URL白名单和IP地址过滤",
                    cwe_id="CWE-918",
                )
            )

    # ==================== AI驱动的代码安全分析 ====================
    async def analyze_code(self, code: str, language: str) -> List[SecurityIssue]:
        """使用AI分析代码中的安全漏洞（OWASP Top 10）
        
        Args:
            code: 要分析的代码字符串
            language: 编程语言（python, javascript, java, etc.）
            
        Returns:
            List[SecurityIssue]: 检测到的安全问题列表
        """
        if not self.ai_engine.is_available():
            logger.warning("AI引擎不可用，跳过AI代码分析")
            return []

        prompt = f"""请作为安全专家，分析以下{language}代码中的安全漏洞（基于OWASP Top 10 2021）：

```{language}
{code[:2000]}  # 限制代码长度避免超时
```

请重点检测以下漏洞类型：
1. A01: 失效的访问控制（Broken Access Control）
2. A02: 加密故障（Cryptographic Failures）- 硬编码密钥、弱加密
3. A03: 注入攻击（Injection）- SQL注入、命令注入、XSS
4. A05: 安全配置错误（Security Misconfiguration）
5. A07: 认证失败（Identification and Authentication Failures）
6. A10: 服务端请求伪造（SSRF）

请以JSON数组格式返回检测结果，每个漏洞包含：
- category: OWASP类别（如"A03:2021"）
- severity: 严重程度（critical/high/medium/low）
- title: 漏洞标题
- description: 详细描述
- recommendation: 修复建议
- cwe_id: CWE编号（如"CWE-89"）
- evidence: 漏洞证据代码行

如果未发现漏洞，返回[]。"""

        try:
            response = await self.ai_engine.generate(prompt, model="general", task_complexity="complex")
            content = response.get("content", "")
            # 提取JSON数组
            import json
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                issues_data = json.loads(json_match.group(0))
                issues = []
                for item in issues_data:
                    issues.append(SecurityIssue(
                        category=item.get("category", "Unknown"),
                        severity=item.get("severity", "medium"),
                        title=item.get("title", "未知漏洞"),
                        description=item.get("description", ""),
                        recommendation=item.get("recommendation", ""),
                        cwe_id=item.get("cwe_id"),
                        evidence=item.get("evidence"),
                    ))
                return issues
            else:
                logger.warning(f"AI响应中未找到JSON数组: {content[:200]}")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"解析AI响应JSON失败: {e}")
            return []
        except Exception as e:
            logger.error(f"AI代码分析失败: {e}")
            return []

    async def analyze_file(self, file_path: str) -> List[SecurityIssue]:
        """分析单个代码文件的安全漏洞
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[SecurityIssue]: 检测到的安全问题列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # 检测编程语言
            ext = Path(file_path).suffix.lower()
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.java': 'java',
                '.go': 'go',
                '.rb': 'ruby',
                '.php': 'php',
                '.cs': 'csharp',
            }
            language = language_map.get(ext, 'unknown')
            return await self.analyze_code(code, language)
            
        except Exception as e:
            logger.error(f"分析文件失败 {file_path}: {e}")
            return []

    async def analyze_project(self, project_path: str, file_extensions: List[str] = None) -> Dict[str, Any]:
        """分析整个项目的安全漏洞
        
        Args:
            project_path: 项目根目录路径
            file_extensions: 要分析的文件扩展名列表（如['.py', '.js']），默认常用代码文件
            
        Returns:
            Dict: 项目安全分析报告
        """
        if file_extensions is None:
            file_extensions = ['.py', '.js', '.ts', '.java', '.go', '.rb', '.php', '.cs']
        
        all_issues = []
        scanned_files = 0
        failed_files = 0
        # 递归扫描项目文件
        for root, dirs, files in os.walk(project_path):
            # 跳过常见非代码目录
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
            for file in files:
                if any(file.endswith(ext) for ext in file_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        issues = await self.analyze_file(file_path)
                        all_issues.extend(issues)
                        scanned_files += 1
                    except Exception as e:
                        logger.error(f"扫描文件失败 {file_path}: {e}")
                        failed_files += 1
        
        # 生成报告
        report = {
            "project_path": project_path,
            "scanned_files": scanned_files,
            "failed_files": failed_files,
            "total_issues": len(all_issues),
            "critical_count": sum(1 for i in all_issues if i.severity == "critical"),
            "high_count": sum(1 for i in all_issues if i.severity == "high"),
            "medium_count": sum(1 for i in all_issues if i.severity == "medium"),
            "low_count": sum(1 for i in all_issues if i.severity == "low"),
            "issues": [self._issue_to_dict(issue) for issue in all_issues],
            "timestamp": datetime.utcnow().isoformat(),
        }
        return report

    def _issue_to_dict(self, issue: SecurityIssue) -> Dict[str, Any]:
        """将安全问题转换为字典"""
        return {
            "category": issue.category,
            "severity": issue.severity,
            "title": issue.title,
            "description": issue.description,
            "recommendation": issue.recommendation,
            "cwe_id": issue.cwe_id,
            "affected_endpoint": issue.affected_endpoint,
            "evidence": issue.evidence,
        }

    def get_security_report(self) -> Dict[str, Any]:
        """生成安全审计报告"""
        if not self.scan_history:
            return {"message": "No security scans performed yet"}

        latest_scan = self.scan_history[-1]
        # 计算安全评分
        total_issues = latest_scan["total_issues"]
        critical_weight = 10
        high_weight = 5
        medium_weight = 2
        low_weight = 1
        risk_score = (
            latest_scan["critical_count"] * critical_weight
            + latest_scan["high_count"] * high_weight
            + latest_scan["medium_count"] * medium_weight
            + latest_scan["low_count"] * low_weight
        )
        # 评分 (100分制，扣分制)
        security_score = max(0, 100 - risk_score)
        # 评级
        if security_score >= 90:
            grade = "A"
        elif security_score >= 80:
            grade = "B"
        elif security_score >= 70:
            grade = "C"
        elif security_score >= 60:
            grade = "D"
        else:
            grade = "F"

        return {
            "latest_scan": latest_scan,
            "security_score": security_score,
            "grade": grade,
            "risk_level": "low" if security_score >= 80 else "medium" if security_score >= 60 else "high",
            "scan_history_count": len(
                self.scan_history),
            "owasp_coverage": f"{len([k for k, v in self.owasp_categories.items() if any(i.category.startswith(k) for i in self.issues)])}/{len(self.owasp_categories)}",
        }


# 全局安全审计实例
security_auditor = SecurityAuditor()
