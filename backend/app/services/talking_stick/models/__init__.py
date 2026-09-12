"""
Talking-Stick 数据模型模块
包含扫描结果、漏洞和修复方案的数据模型
"""

from .scan_result import ScanResult, RiskFile, ScanSummary
from .vulnerability import Vulnerability, AuditResult
from .fix import POC, FixSuggestion, VerificationResult, VerificationOutput

__all__ = [
    "ScanResult", "RiskFile", "ScanSummary",
    "Vulnerability", "AuditResult",
    "POC", "FixSuggestion", "VerificationResult", "VerificationOutput"
]
