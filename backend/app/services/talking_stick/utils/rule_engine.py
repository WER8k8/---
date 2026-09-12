"""
Talking-Stick 规则引擎
负责应用检测规则并识别漏洞
"""

import re
import logging
from typing import Any, Dict, List, Optional, Pattern
from dataclasses import dataclass

logger = logging.getLogger(__name__)

from ..models.vulnerability import Vulnerability

@dataclass
class DetectionRule:
    """检测规则"""
    id: str
    name: str
    category: str
    severity: str
    pattern: str
    description: str
    cwe_id: Optional[str] = None
    recommendation: Optional[str] = None
    false_positive_patterns: Optional[List[str]] = None

class RuleEngine:
    """规则引擎"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.rules: List[DetectionRule] = []
        self._init_default_rules()
    
    def _init_default_rules(self) -> None:
        """初始化默认规则"""
        # OWASP Top 10 规则
        _init_owasp_rules(self)
        # 硬编码凭证规则
        _init_secret_rules(self)
        # 配置安全规则
        self.rules.extend([
            DetectionRule(
                id="CONFIG-001",
                name="CORS全开放",
                category="config_security",
                severity="high",
                pattern=r"(?i)(cors|access-control-allow-origin)\s*[=:]\s*['\"]?\*['\"]?",
                description="检测CORS全开放配置",
                cwe_id="CWE-942",
                recommendation="限制允许的来源域名",
                false_positive_patterns=[
                    r"(?i)(development|dev|local)"
                ]
            ),
            DetectionRule(
                id="CONFIG-002",
                name="调试模式开启",
                category="config_security",
                severity="medium",
                pattern=r"(?i)(debug|debug_mode)\s*[=:]\s*(true|1|on|yes)",
                description="检测调试模式是否开启",
                cwe_id="CWE-489",
                recommendation="生产环境关闭调试模式",
                false_positive_patterns=[
                    r"(?i)(development|dev|local)"
                ]
            ),
        ])
        # 自定义规则
        self.rules.extend([
            DetectionRule(
                id="CUSTOM-001",
                name="数据库连接字符串",
                category="hardcoded_secrets",
                severity="critical",
                pattern=r"(?i)(mysql|postgresql|mongodb|redis)://[^:]+:[^@]+@[^/]+",
                description="检测硬编码的数据库连接字符串",
                cwe_id="CWE-798",
                recommendation="使用环境变量或密钥管理服务",
                false_positive_patterns=[
                    r"(?i)(os\.getenv|os\.environ|settings\.)",
                    r"(?i)(example|demo|test|placeholder|your_)",
                    r"quote_plus",
                    r"SQL_MATRIX"
                ]
            ),
        ])

    def _init_owasp_rules(self):
        """初始化 OWASP Top 10 相关检测规则。"""
        self.rules.extend([
            self._owasp_sql_injection_rule(),
            self._owasp_command_injection_rule(),
            self._owasp_hardcoded_password_rule(),
            self._owasp_hardcoded_api_key_rule(),
        ])

    def _owasp_sql_injection_rule(self) -> DetectionRule:
        """构造 SQL 注入检测规则（OWASP-A03-001）。"""
        return DetectionRule(
            id="OWASP-A03-001",
            name="SQL注入",
            category="A03:2021",
            severity="critical",
            pattern=r"(?i)(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE)\s+.*\s*(WHERE|FROM|INTO|SET)\s+.*['\"]?\s*\+",
            description="检测SQL注入漏洞",
            cwe_id="CWE-89",
            recommendation="使用参数化查询或ORM",
            false_positive_patterns=[
                r"(?i)(text\(|params\(|bind\(|filter\(|query\()"
            ]
        )

    def _owasp_command_injection_rule(self) -> DetectionRule:
        """构造命令注入检测规则（OWASP-A03-002）。"""
        return DetectionRule(
            id="OWASP-A03-002",
            name="命令注入",
            category="A03:2021",
            severity="critical",
            pattern=r"(?i)(os\.system\s*\(|os\.popen\s*\(|subprocess\.(call|run|check_output|check_call|Popen)\s*\(\s*[\"']|exec\s*\(\s*[\"']|eval\s*\(\s*[\"'])",
            description="检测命令注入漏洞 - 仅检测直接使用字符串的调用",
            cwe_id="CWE-78",
            recommendation="使用安全的API，避免直接执行用户输入",
            false_positive_patterns=[
                r"shell=False",
                r"(?i)(example|demo|test|placeholder)",
                r"sensitive_patterns",
                r"scan_skill_code",
                r"risk_pattern",
                r"detection_rule",
                r"security_scan",
                r"code_analysis",
                r"pattern.*message.*severity",
                r"def\s+scan_",
                r"def\s+audit_",
                r"def\s+detect_",
            ]
        )

    def _owasp_hardcoded_password_rule(self) -> DetectionRule:
        """构造硬编码密码检测规则（OWASP-A07-001）。"""
        return DetectionRule(
            id="OWASP-A07-001",
            name="硬编码密码",
            category="A07:2021",
            severity="critical",
            pattern=r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]+['\"]",
            description="检测硬编码密码",
            cwe_id="CWE-798",
            recommendation="使用环境变量或密钥管理服务",
            false_positive_patterns=[
                r"(?i)(os\.getenv|os\.environ|settings\.)",
                r"(?i)(example|demo|test|placeholder|your_)",
                r"(?i)(hash|hashed|encrypted|decrypted)",
                r"password_hash",
                r"verify_password",
                r"db_password",
            ]
        )

    def _owasp_hardcoded_api_key_rule(self) -> DetectionRule:
        """构造硬编码 API 密钥检测规则（OWASP-A07-002）。"""
        return DetectionRule(
            id="OWASP-A07-002",
            name="硬编码API密钥",
            category="A07:2021",
            severity="critical",
            pattern=r"(?i)(api_key|apikey|api-key|secret_key|secret-key|access_key|access-key)\s*[=:]\s*['\"][^'\"]+['\"]",
            description="检测硬编码API密钥",
            cwe_id="CWE-798",
            recommendation="使用环境变量或密钥管理服务",
            false_positive_patterns=[
                r"(?i)(os\.getenv|os\.environ|settings\.)",
                r"(?i)(example|demo|test|placeholder|your_)",
                r"QINIU_ACCESS_KEY",
                r"QINIU_SECRET_KEY",
                r"MEDIA_R2_SECRET_ACCESS_KEY",
                r"MEDIA_R2_ACCESS_KEY_ID",
                r"if\s+r\s+else",
                r"f[\"'].*=.*['\"]",
                r"\.env",
                r"FILE_STORAGE",
            ]
        )

    def _init_secret_rules(self):
        """_init_secret_rules。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.rules.extend([

            DetectionRule(

                id="SECRET-001",
                name="AWS访问密钥",
                category="hardcoded_secrets",
                severity="critical",
                pattern=r"AKIA[0-9A-Z]{16}",
                description="检测AWS访问密钥",
                cwe_id="CWE-798",
                recommendation="使用IAM角色或环境变量",
                false_positive_patterns=[

                    r"(?i)(example|demo|test|placeholder)"

                ]

            ),
            DetectionRule(

                id="SECRET-002",
                name="GitHub令牌",
                category="hardcoded_secrets",
                severity="critical",
                pattern=r"(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}",
                description="检测GitHub个人访问令牌",
                cwe_id="CWE-798",
                recommendation="使用GitHub Secrets或环境变量",
                false_positive_patterns=[

                    r"(?i)(example|demo|test|placeholder)"

                ]

            ),
            DetectionRule(

                id="SECRET-003",
                name="JWT密钥",
                category="hardcoded_secrets",
                severity="critical",
                pattern=r"(?i)(jwt_secret|jwt-secret|jwt_key|jwt-key)\s*[=:]\s*['\"][^'\"]+['\"]",
                description="检测JWT密钥",
                cwe_id="CWE-798",
                recommendation="使用环境变量或密钥管理服务",
                false_positive_patterns=[

                    r"(?i)(os\.getenv|os\.environ|settings\.)",
                    r"(?i)(example|demo|test|placeholder|your_)"

                ]

            ),

        ])

    def add_rule(self, rule: DetectionRule) -> None:
        """添加自定义规则"""
        self.rules.append(rule)
    
    def _is_false_positive(self, rule: DetectionRule, content: str, match: re.Match) -> bool:
        """检查是否为误报"""
        if not rule.false_positive_patterns:
            return False
        
        start = max(0, match.start() - 200)
        end = min(len(content), match.end() + 200)
        context = content[start:end]
        for fp_pattern in rule.false_positive_patterns:
            if re.search(fp_pattern, context, re.IGNORECASE):
                return True
        
        return False
    
    def scan_file(self, filepath: str, content: str) -> List[Vulnerability]:
        """扫描文件内容"""
        vulnerabilities = []
        for rule in self.rules:
            try:
                pattern = re.compile(rule.pattern, re.IGNORECASE | re.MULTILINE)
                matches = pattern.finditer(content)
                for match in matches:
                    # 检查是否为误报
                    if self._is_false_positive(rule, content, match):
                        continue
                    
                    # 计算行号
                    line_number = content[:match.start()].count('\n') + 1
                    # 获取匹配的上下文
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    context = content[start:end]
                    vulnerability = Vulnerability(
                        id=f"{rule.id}_{len(vulnerabilities) + 1}",
                        file=filepath,
                        line=line_number,
                        severity=rule.severity,
                        category=rule.category,
                        title=rule.name,
                        description=rule.description,
                        cwe_id=rule.cwe_id,
                        evidence=context,
                        recommendation=rule.recommendation
                    )
                    vulnerabilities.append(vulnerability)
            except re.error as e:
                logger.error("正则表达式错误 %s: %s", rule.id, e)
        
        return vulnerabilities
    
    def get_rules_by_category(self, category: str) -> List[DetectionRule]:
        """按类别获取规则"""
        return [rule for rule in self.rules if rule.category == category]
    
    def get_rules_by_severity(self, severity: str) -> List[DetectionRule]:
        """按严重程度获取规则"""
        return [rule for rule in self.rules if rule.severity == severity]