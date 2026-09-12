"""
Talking-Stick 修复方案数据模型
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class POC:
    """概念验证"""
    type: str
    input: str
    expected: str
    actual: str
    risk_level: str


@dataclass
class FixSuggestion:
    """修复建议"""
    approach: str
    code_example: str
    estimated_effort: str  # low, medium, high
    priority: str  # immediate, high, medium, low


@dataclass
class VerificationResult:
    """验证结果"""
    vulnerability_id: str
    is_confirmed: bool
    is_false_positive: bool
    poc: Optional[POC] = None
    fix: Optional[FixSuggestion] = None
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "vulnerability_id": self.vulnerability_id,
            "is_confirmed": self.is_confirmed,
            "is_false_positive": self.is_false_positive
        }
        if self.poc:
            result["poc"] = {
                "type": self.poc.type,
                "input": self.poc.input,
                "expected": self.poc.expected,
                "actual": self.poc.actual,
                "risk_level": self.poc.risk_level
            }
        
        if self.fix:
            result["fix"] = {
                "approach": self.fix.approach,
                "code_example": self.fix.code_example,
                "estimated_effort": self.fix.estimated_effort,
                "priority": self.fix.priority
            }
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VerificationResult':
        """从字典创建实例"""
        poc = None
        if 'poc' in data:
            poc_data = data['poc']
            poc = POC(
                type=poc_data.get('type', ''),
                input=poc_data.get('input', ''),
                expected=poc_data.get('expected', ''),
                actual=poc_data.get('actual', ''),
                risk_level=poc_data.get('risk_level', 'low')
            )
        
        fix = None
        if 'fix' in data:
            fix_data = data['fix']
            fix = FixSuggestion(
                approach=fix_data.get('approach', ''),
                code_example=fix_data.get('code_example', ''),
                estimated_effort=fix_data.get('estimated_effort', 'medium'),
                priority=fix_data.get('priority', 'medium')
            )
        
        return cls(
            vulnerability_id=data.get('vulnerability_id', ''),
            is_confirmed=data.get('is_confirmed', False),
            is_false_positive=data.get('is_false_positive', False),
            poc=poc,
            fix=fix
        )


@dataclass
class VerificationOutput:
    """验证输出"""
    verification_id: str
    timestamp: str
    vulnerabilities_verified: int = 0
    results: list = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "verification_id": self.verification_id,
            "timestamp": self.timestamp,
            "vulnerabilities_verified": self.vulnerabilities_verified,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VerificationOutput':
        """从字典创建实例"""
        results = [
            VerificationResult.from_dict(r) for r in data.get('results', [])
        ]
        return cls(
            verification_id=data.get('verification_id', ''),
            timestamp=data.get('timestamp', ''),
            vulnerabilities_verified=data.get('vulnerabilities_verified', 0),
            results=results,
            summary=data.get('summary', {})
        )
