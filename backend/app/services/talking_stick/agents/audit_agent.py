"""
Talking-Stick 审计Agent
负责精读风险代码，寻找已知漏洞（OWASP Top10、命令注入、XSS、SSRF、权限缺陷）
"""

from typing import Any, Dict, List
from pathlib import Path

from .base_agent import BaseAgent
from ..config import ConfigManager
from ..utils.rule_engine import RuleEngine


class AuditAgent(BaseAgent):
    """审计Agent"""
    def __init__(self, config_manager: ConfigManager):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param config_manager: 参数 config_manager
        :return: 返回处理结果。
        """
        super().__init__("audit", config_manager)
        # 初始化规则引擎
        self.rule_engine = None
        self._init_rule_engine()
    
    def _init_rule_engine(self) -> None:
        """初始化规则引擎"""
        self.rule_engine = RuleEngine()
    
    async def execute(self, recon_result: Dict[str, Any], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行审计任务"""
        self.log("开始代码审计...")
        target_path = recon_result.get("target_path", "")
        risk_files = recon_result.get("risk_files", [])
        # 获取文件锁
        lock_id = await self.acquire_file_lock(target_path)
        try:
            # 审计风险文件
            vulnerabilities = await self._audit_risk_files(risk_files, target_path)
            # 生成审计结果
            result = self._generate_result(target_path, vulnerabilities, recon_result)
            self.log(f"审计完成 - 发现漏洞: {len(vulnerabilities)}")
            return result
            
        finally:
            # 释放文件锁
            await self.release_file_lock(lock_id)
    
    async def _audit_risk_files(self, risk_files: List[Dict[str, Any]], target_path: str) -> List[Dict[str, Any]]:
        """审计风险文件"""
        self.log(f"审计 {len(risk_files)} 个风险文件...")
        vulnerabilities = []
        for risk_file in risk_files:
            file_path = risk_file["path"]
            try:
                # 读取文件内容
                content = await self._read_file(file_path)
                # 使用规则引擎检测漏洞（返回Vulnerability对象列表）
                file_vulnerabilities = self.rule_engine.scan_file(file_path, content)
                # 转换为字典格式并添加风险文件信息
                for vuln in file_vulnerabilities:
                    vuln_dict = {
                        "rule_id": vuln.id,
                        "file_path": vuln.file,
                        "line_number": vuln.line,
                        "severity": vuln.severity,
                        "owasp_category": vuln.category,
                        "title": vuln.title,
                        "message": vuln.description,
                        "cwe_id": vuln.cwe_id,
                        "matched_content": vuln.evidence or "",
                        "recommendation": vuln.recommendation,
                        "risk_file_info": {
                            "risk_score": risk_file.get("risk_score", 0),
                            "risk_reasons": risk_file.get("risk_reasons", [])
                        }
                    }
                    vulnerabilities.append(vuln_dict)
                
            except Exception as e:
                self.log(f"审计文件失败 {file_path}: {str(e)}", "error")
        
        # 按严重程度排序
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        vulnerabilities.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 4))
        return vulnerabilities
    
    async def _read_file(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"无法读取文件 {file_path}: {str(e)}")
    
    def _generate_result(self, target_path: str, vulnerabilities: List[Dict[str, Any]], 
                        recon_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成审计结果"""
        # 统计漏洞类型
        vulnerability_types = {}
        for vuln in vulnerabilities:
            vuln_type = vuln.get("rule_id", "unknown")
            vulnerability_types[vuln_type] = vulnerability_types.get(vuln_type, 0) + 1
        
        # 统计严重程度
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "info")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # 按OWASP分类
        owasp_categories = {}
        for vuln in vulnerabilities:
            owasp_category = vuln.get("owasp_category", "Other")
            if owasp_category not in owasp_categories:
                owasp_categories[owasp_category] = []
            owasp_categories[owasp_category].append(vuln)
        
        # 生成OWASP摘要
        owasp_summary = {}
        for category, vulns in owasp_categories.items():
            owasp_summary[category] = {
                "count": len(vulns),
                "critical": sum(1 for v in vulns if v.get("severity") == "critical"),
                "high": sum(1 for v in vulns if v.get("severity") == "high"),
                "medium": sum(1 for v in vulns if v.get("severity") == "medium"),
                "low": sum(1 for v in vulns if v.get("severity") == "low")
            }
        
        # 生成建议
        recommendations = self._generate_recommendations(vulnerabilities, severity_counts)
        return {
            "agent_type": "audit",
            "target_path": target_path,
            "timestamp": self.generate_id("audit"),
            "summary": {
                "total_vulnerabilities": len(vulnerabilities),
                "severity_counts": severity_counts,
                "vulnerability_types": vulnerability_types,
                "owasp_summary": owasp_summary
            },
            "vulnerabilities": vulnerabilities,
            "owasp_categories": owasp_categories,
            "recommendations": recommendations,
            "recon_summary": recon_result.get("summary", {})
        }
    
    def _generate_recommendations(self, vulnerabilities: List[Dict[str, Any]], 
                                 severity_counts: Dict[str, int]) -> List[str]:
        """生成建议"""
        recommendations = []
        # 基于严重程度的建议
        if severity_counts["critical"] > 0:
            recommendations.append(f"发现 {severity_counts['critical']} 个严重漏洞，需要立即修复")
        
        if severity_counts["high"] > 0:
            recommendations.append(f"发现 {severity_counts['high']} 个高危漏洞，建议优先处理")
        
        # 基于漏洞类型的建议
        vuln_types = set(vuln.get("rule_id") for vuln in vulnerabilities)
        if "sql_injection" in vuln_types:
            recommendations.append("发现SQL注入漏洞，建议使用参数化查询")
        
        if "xss" in vuln_types:
            recommendations.append("发现XSS漏洞，建议实施输入验证和输出编码")
        
        if "command_injection" in vuln_types:
            recommendations.append("发现命令注入漏洞，建议避免使用shell命令或使用安全的API")
        
        if "hardcoded_credentials" in vuln_types:
            recommendations.append("发现硬编码凭证，建议使用环境变量或密钥管理服务")
        
        if "path_traversal" in vuln_types:
            recommendations.append("发现路径遍历漏洞，建议验证和限制文件路径")
        
        # 通用建议
        if not recommendations:
            recommendations.append("建议进行深度代码审查和安全测试")
        
        return recommendations
    
    async def audit_specific_file(self, file_path: str) -> Dict[str, Any]:
        """审计特定文件"""
        self.log(f"审计特定文件: {file_path}")
        try:
            # 读取文件内容
            content = await self._read_file(file_path)
            # 使用规则引擎检测漏洞
            vulnerabilities = self.rule_engine.scan_file(file_path, content)
            return {
                "file_path": file_path,
                "vulnerabilities": vulnerabilities,
                "total_vulnerabilities": len(vulnerabilities),
                "severity_counts": {
                    "critical": sum(1 for v in vulnerabilities if v.get("severity") == "critical"),
                    "high": sum(1 for v in vulnerabilities if v.get("severity") == "high"),
                    "medium": sum(1 for v in vulnerabilities if v.get("severity") == "medium"),
                    "low": sum(1 for v in vulnerabilities if v.get("severity") == "low")
                }
            }
            
        except Exception as e:
            return {
                "file_path": file_path,
                "error": str(e),
                "vulnerabilities": []
            }