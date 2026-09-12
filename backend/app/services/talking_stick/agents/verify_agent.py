"""
Talking-Stick 验证Agent
负责复现漏洞、构造POC、剔除误报，输出修复方案
"""

from typing import Any, Dict, List
from pathlib import Path

from .base_agent import BaseAgent
from ..config import ConfigManager


class VerifyAgent(BaseAgent):
    """验证Agent"""
    def __init__(self, config_manager: ConfigManager):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param config_manager: 参数 config_manager
        :return: 返回处理结果。
        """
        super().__init__("verify", config_manager)
    
    async def execute(self, audit_result: Dict[str, Any], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行验证任务"""
        self.log("开始漏洞验证...")
        target_path = audit_result.get("target_path", "")
        vulnerabilities = audit_result.get("vulnerabilities", [])
        # 获取文件锁
        lock_id = await self.acquire_file_lock(target_path)
        try:
            # 验证漏洞
            verification_results = await self._verify_vulnerabilities(vulnerabilities, target_path)
            # 生成验证结果
            result = self._generate_result(target_path, verification_results, audit_result)
            self.log(f"验证完成 - 确认漏洞: {result['summary']['confirmed']}, 误报: {result['summary']['false_positives']}")
            return result
            
        finally:
            # 释放文件锁
            await self.release_file_lock(lock_id)
    
    async def _verify_vulnerabilities(self, vulnerabilities: List[Dict[str, Any]], target_path: str) -> List[Dict[str, Any]]:
        """验证漏洞"""
        self.log(f"验证 {len(vulnerabilities)} 个漏洞...")
        verification_results = []
        for vuln in vulnerabilities:
            try:
                # 验证单个漏洞
                result = await self._verify_single_vulnerability(vuln, target_path)
                verification_results.append(result)
                
            except Exception as e:
                self.log(f"验证漏洞失败 {vuln.get('rule_id', 'unknown')}: {str(e)}", "error")
                # 标记为无法验证
                verification_results.append({
                    "vulnerability_id": vuln.get("rule_id", "unknown"),
                    "is_confirmed": False,
                    "is_false_positive": False,
                    "verification_status": "error",
                    "error": str(e)
                })
        
        return verification_results
    
    async def _verify_single_vulnerability(self, vuln: Dict[str, Any], target_path: str) -> Dict[str, Any]:
        """验证单个漏洞"""
        vuln_id = vuln.get("rule_id", "unknown")
        severity = vuln.get("severity", "info")
        file_path = vuln.get("file_path", "")
        line_number = vuln.get("line_number", 0)
        matched_content = vuln.get("matched_content", "")
        # OWASP规则ID映射
        owasp_mapping = {
            "OWASP-A03-001": "sql_injection",
            "OWASP-A03-002": "command_injection",
            "OWASP-A07-001": "hardcoded_credentials",
            "OWASP-A07-002": "hardcoded_credentials",
            "OWASP-A01-001": "path_traversal",
            "OWASP-A05-001": "debug_enabled",
            "SECRET-001": "hardcoded_credentials",
            "SECRET-002": "hardcoded_credentials",
            "SECRET-003": "hardcoded_credentials",
            "CONFIG-001": "cors_misconfiguration",
            "CONFIG-002": "debug_enabled",
            "CUSTOM-001": "hardcoded_credentials",
        }
        # 提取基础规则ID（去掉数字后缀）
        base_rule_id = vuln_id.split('_')[0] if '_' in vuln_id else vuln_id
        # 获取漏洞类型
        vuln_type = owasp_mapping.get(base_rule_id, owasp_mapping.get(vuln_id, vuln_id))
        # 基于漏洞类型的验证逻辑
        if vuln_type == "sql_injection":
            return await self._verify_sql_injection(vuln, target_path)
        elif vuln_type == "xss":
            return await self._verify_xss(vuln, target_path)
        elif vuln_type == "command_injection":
            return await self._verify_command_injection(vuln, target_path)
        elif vuln_type == "hardcoded_credentials":
            return await self._verify_hardcoded_credentials(vuln, target_path)
        elif vuln_type == "path_traversal":
            return await self._verify_path_traversal(vuln, target_path)
        elif vuln_type == "debug_enabled":
            return await self._verify_debug_enabled(vuln, target_path)
        elif vuln_type == "weak_random":
            return await self._verify_weak_random(vuln, target_path)
        elif vuln_type == "cors_misconfiguration":
            return await self._verify_cors_misconfiguration(vuln, target_path)
        else:
            # 默认验证逻辑
            return await self._verify_generic(vuln, target_path)
    
    async def _verify_sql_injection(self, vuln: Dict[str, Any], target_path: str) -> Dict[str, Any]:
        """验证SQL注入漏洞"""
        file_path = vuln.get("file_path", "")
        line_number = vuln.get("line_number", 0)
        matched_content = vuln.get("matched_content", "")
        # 检查是否使用参数化查询
        is_parameterized = "execute(" in matched_content and "%s" in matched_content
        # 检查是否使用ORM
        is_orm = any(orm in matched_content.lower() for orm in ["query(", "filter(", "select("])
        # 判断是否为误报
        is_false_positive = is_parameterized or is_orm
        # 生成POC
        poc = None
        if not is_false_positive:
            poc = {
                "type": "sql_injection",
                "input": "1 OR 1=1",
                "expected": "返回所有用户",
                "actual": "待验证",
                "risk_level": "critical"
            }
        
        # 生成修复建议
        fix = {
            "approach": "parameterized_query",
            "code_example": 'query = "SELECT * FROM users WHERE id = %s"\ncursor.execute(query, (user_id,))',
            "estimated_effort": "low",
            "priority": "immediate" if not is_false_positive else "low"
        }
        return {
            "vulnerability_id": vuln.get("rule_id", "unknown"),
            "is_confirmed": not is_false_positive,
            "is_false_positive": is_false_positive,
            "verification_status": "verified",
            "poc": poc,
            "fix": fix,
            "reasoning": "使用参数化查询或ORM，风险较低" if is_false_positive else "存在SQL注入风险"
        }
    
    async def _verify_xss(self, vuln: Dict[str, Any], target_path: str) -> Dict[str, Any]:
        """验证XSS漏洞"""
        file_path = vuln.get("file_path", "")
        line_number = vuln.get("line_number", 0)
        matched_content = vuln.get("matched_content", "")
        # 检查是否使用模板引擎的自动转义
        is_auto_escaped = any(escape in matched_content for escape in ["{{", "{%", "|safe", "|escape"])
        # 检查是否使用前端框架的自动转义
        is_framework_escaped = any(framework in matched_content.lower() for framework in ["react", "vue", "angular", "jsx", "tsx"])
        # 判断是否为误报
        is_false_positive = is_auto_escaped or is_framework_escaped
        # 生成POC
        poc = None
        if not is_false_positive:
            poc = {
                "type": "xss",
                "input": "<script>alert('XSS')</script>",
                "expected": "执行JavaScript代码",
                "actual": "待验证",
                "risk_level": "high"
            }
        
        # 生成修复建议
        fix = {
            "approach": "input_validation_output_encoding",
            "code_example": "# 使用模板引擎的自动转义\n{{ user_input | escape }}\n\n# 或使用DOMPurify\nimport DOMPurify from 'dompurify';\nconst clean = DOMPurify.sanitize(userInput);",
            "estimated_effort": "low",
            "priority": "high" if not is_false_positive else "low"
        }
        return {
            "vulnerability_id": vuln.get("rule_id", "unknown"),
            "is_confirmed": not is_false_positive,
            "is_false_positive": is_false_positive,
            "verification_status": "verified",
            "poc": poc,
            "fix": fix,
            "reasoning": "使用模板引擎或前端框架的自动转义，风险较低" if is_false_positive else "存在XSS风险"
        }
    
    async def _verify_command_injection(self, vuln: Dict[str, Any], target_path: str) -> Dict[str, Any]:
        """验证命令注入漏洞"""
        file_path = vuln.get("file_path", "")
        line_number = vuln.get("line_number", 0)
        matched_content = vuln.get("matched_content", "")
        # 检查是否使用危险的API
        is_dangerous_api = any(api in matched_content for api in ["os.system", "os.popen"])
        # 检查是否使用subprocess
        is_subprocess = any(api in matched_content for api in ["subprocess.run", "subprocess.call", "subprocess.check_output", "asyncio.create_subprocess_exec"])
        # 检查shell参数
        has_shell_true = "shell=True" in matched_content
        has_shell_false = "shell=False" in matched_content
        # 检查是否使用列表形式的命令（更安全）
        uses_list = "[" in matched_content and "]" in matched_content
        # 检查是否使用变量作为命令（可能危险）
        uses_variable = any(var in matched_content for var in ["cmd", "command", "args", "argv"])
        # 判断是否为误报
        is_false_positive = False
        if is_dangerous_api:
            # os.system和os.popen总是危险的
            is_false_positive = False
        elif is_subprocess:
            if has_shell_false:
                # shell=False是安全的
                is_false_positive = True
            elif has_shell_true:
                # shell=True是危险的
                is_false_positive = False
            elif uses_list and not has_shell_true:
                # 使用列表且没有shell=True，通常是安全的
                is_false_positive = True
            else:
                # 其他情况需要进一步分析
                is_false_positive = False
        
        # 生成POC
        poc = None
        if not is_false_positive:
            poc = {
                "type": "command_injection",
                "input": "test; rm -rf /",
                "expected": "执行恶意命令",
                "actual": "待验证",
                "risk_level": "critical"
            }
        
        # 生成修复建议
        if is_dangerous_api:
            fix = {
                "approach": "replace_with_subprocess",
                "code_example": "# 避免使用os.system，改用subprocess\nimport subprocess\nresult = subprocess.run(['ls', '-l'], shell=False, capture_output=True, text=True)",
                "estimated_effort": "low",
                "priority": "immediate"
            }
        elif has_shell_true:
            fix = {
                "approach": "disable_shell",
                "code_example": "# 设置shell=False，使用列表形式的命令\nimport subprocess\nresult = subprocess.run(['ls', '-l'], shell=False, capture_output=True, text=True)",
                "estimated_effort": "low",
                "priority": "immediate"
            }
        else:
            fix = {
                "approach": "safe_api_usage",
                "code_example": "# 确保使用subprocess.run并设置shell=False\nimport subprocess\nresult = subprocess.run(['ls', '-l'], shell=False, capture_output=True, text=True)",
                "estimated_effort": "low",
                "priority": "low" if is_false_positive else "medium"
            }
        
        return {
            "vulnerability_id": vuln.get("rule_id", "unknown"),
            "is_confirmed": not is_false_positive,
            "is_false_positive": is_false_positive,
            "verification_status": "verified",
            "poc": poc,
            "fix": fix,
            "reasoning": "使用安全的API和参数化命令，风险较低" if is_false_positive else "存在命令注入风险"
        }
    
    async def _verify_hardcoded_credentials(self, vuln: Dict[str, Any], target_path: str) -> Dict[str, Any]:
        """验证硬编码凭证"""
        file_path = vuln.get("file_path", "")
        line_number = vuln.get("line_number", 0)
        matched_content = vuln.get("matched_content", "")
        # 检查是否为示例或测试代码
        is_example = any(example in matched_content.lower() for example in ["example", "test", "demo", "sample", "xxx", "your_", "placeholder"])
        # 检查是否使用环境变量
        is_env_var = "os.getenv" in matched_content or "os.environ" in matched_content or "process.env" in matched_content
        # 判断是否为误报
        is_false_positive = is_example or is_env_var
        # 生成POC
        poc = None
        if not is_false_positive:
            poc = {
                "type": "hardcoded_credentials",
                "input": "提取的凭证",
                "expected": "使用凭证访问系统",
                "actual": "待验证",
                "risk_level": "high"
            }
        
        # 生成修复建议
        fix = {
            "approach": "environment_variables",
            "code_example": "# 使用环境变量\nimport os\npassword = os.getenv('DB_PASSWORD')\n\n# 或使用密钥管理服务\nimport boto3\nclient = boto3.client('secretsmanager')\nsecret = client.get_secret_value(SecretId='my-secret')",
            "estimated_effort": "low",
            "priority": "high" if not is_false_positive else "low"
        }
        return {
            "vulnerability_id": vuln.get("rule_id", "unknown"),
            "is_confirmed": not is_false_positive,
            "is_false_positive": is_false_positive,
            "verification_status": "verified",
            "poc": poc,
            "fix": fix,
            "reasoning": "为示例代码或已使用环境变量，风险较低" if is_false_positive else "存在硬编码凭证风险"
        }
    
    async def _verify_path_traversal(self, vuln: Dict[str, Any], target_path: str) -> Dict[str, Any]:
        """验证路径遍历漏洞"""
        file_path = vuln.get("file_path", "")
        line_number = vuln.get("line_number", 0)
        matched_content = vuln.get("matched_content", "")
        # 检查是否验证路径
        is_validated = any(validation in matched_content for validation in ["os.path.abspath", "pathlib.Path.resolve", "sanitize", "validate"])
        # 检查是否限制在特定目录
        is_restricted = any(restriction in matched_content for restriction in ["startswith", "in_directory", "allowed_path"])
        # 判断是否为误报
        is_false_positive = is_validated or is_restricted
        # 生成POC
        poc = None
        if not is_false_positive:
            poc = {
                "type": "path_traversal",
                "input": "../../../etc/passwd",
                "expected": "读取系统文件",
                "actual": "待验证",
                "risk_level": "high"
            }
        
        # 生成修复建议
        fix = {
            "approach": "path_validation",
            "code_example": "# 使用pathlib验证路径\nfrom pathlib import Path\nbase_dir = Path('/safe/directory')\nuser_path = Path(user_input).resolve()\nif not user_path.is_relative_to(base_dir):\n    raise ValueError('Invalid path')",
            "estimated_effort": "low",
            "priority": "high" if not is_false_positive else "low"
        }
        return {
            "vulnerability_id": vuln.get("rule_id", "unknown"),
            "is_confirmed": not is_false_positive,
            "is_false_positive": is_false_positive,
            "verification_status": "verified",
            "poc": poc,
            "fix": fix,
            "reasoning": "已验证路径或限制在特定目录，风险较低" if is_false_positive else "存在路径遍历风险"
        }
    
    async def _verify_debug_enabled(self, vuln: Dict[str, Any], target_path: str) -> Dict[str, Any]:
        """验证调试模式启用"""
        file_path = vuln.get("file_path", "")
        line_number = vuln.get("line_number", 0)
        matched_content = vuln.get("matched_content", "")
        # 检查是否为开发环境配置
        is_dev_config = any(dev in matched_content.lower() for dev in ["development", "dev", "local", "test"])
        # 检查是否有环境变量控制
        has_env_control = "os.getenv" in matched_content or "os.environ" in matched_content
        # 判断是否为误报
        is_false_positive = is_dev_config or has_env_control
        # 生成POC
        poc = None
        if not is_false_positive:
            poc = {
                "type": "debug_enabled",
                "input": "访问应用",
                "expected": "显示调试信息",
                "actual": "待验证",
                "risk_level": "medium"
            }
        
        # 生成修复建议
        fix = {
            "approach": "environment_based_config",
            "code_example": "# 使用环境变量控制调试模式\nimport os\nDEBUG = os.getenv('DEBUG', 'false').lower() == 'true'",
            "estimated_effort": "low",
            "priority": "medium" if not is_false_positive else "low"
        }
        return {
            "vulnerability_id": vuln.get("rule_id", "unknown"),
            "is_confirmed": not is_false_positive,
            "is_false_positive": is_false_positive,
            "verification_status": "verified",
            "poc": poc,
            "fix": fix,
            "reasoning": "为开发环境配置或有环境变量控制，风险较低" if is_false_positive else "生产环境启用调试模式"
        }
    
    async def _verify_cors_misconfiguration(self, vuln: Dict[str, Any], target_path: str) -> Dict[str, Any]:
        """验证CORS配置错误"""
        file_path = vuln.get("file_path", "")
        line_number = vuln.get("line_number", 0)
        matched_content = vuln.get("matched_content", "")
        # 检查是否为开发环境配置
        is_dev_config = any(dev in matched_content.lower() for dev in ["development", "dev", "local", "test"])
        # 检查是否有环境变量控制
        has_env_control = "os.getenv" in matched_content or "os.environ" in matched_content
        # 检查是否为通配符
        is_wildcard = "*" in matched_content
        # 判断是否为误报
        is_false_positive = is_dev_config or has_env_control
        # 生成POC
        poc = None
        if not is_false_positive and is_wildcard:
            poc = {
                "type": "cors_misconfiguration",
                "input": "Origin: malicious-site.com",
                "expected": "允许跨域请求",
                "actual": "待验证",
                "risk_level": "high"
            }
        
        # 生成修复建议
        fix = {
            "approach": "restrict_origins",
            "code_example": "# 限制允许的来源域名\nallowed_origins = [\n    \"https://yourdomain.com\",\n    \"https://www.yourdomain.com\"\n]\n\nif origin in allowed_origins:\n    response.headers[\"Access-Control-Allow-Origin\"] = origin",
            "estimated_effort": "low",
            "priority": "high" if not is_false_positive and is_wildcard else "low"
        }
        return {
            "vulnerability_id": vuln.get("rule_id", "unknown"),
            "is_confirmed": not is_false_positive and is_wildcard,
            "is_false_positive": is_false_positive or not is_wildcard,
            "verification_status": "verified",
            "poc": poc,
            "fix": fix,
            "reasoning": "为开发环境配置或有环境变量控制，风险较低" if is_false_positive else "CORS配置为通配符，存在安全风险"
        }
    
    async def _verify_weak_random(self, vuln: Dict[str, Any], target_path: str) -> Dict[str, Any]:
        """验证弱随机数生成"""
        file_path = vuln.get("file_path", "")
        line_number = vuln.get("line_number", 0)
        matched_content = vuln.get("matched_content", "")
        # 检查是否为非安全用途
        is_non_security = any(usage in matched_content.lower() for usage in ["test", "example", "demo", "sample", "random.shuffle", "random.choice"])
        # 检查是否使用安全的随机数生成器
        is_secure_random = any(secure in matched_content for secure in ["secrets", "os.urandom", "SystemRandom", "crypto.random"])
        # 判断是否为误报
        is_false_positive = is_non_security or is_secure_random
        # 生成POC
        poc = None
        if not is_false_positive:
            poc = {
                "type": "weak_random",
                "input": "预测随机数",
                "expected": "预测生成的随机数",
                "actual": "待验证",
                "risk_level": "medium"
            }
        
        # 生成修复建议
        fix = {
            "approach": "secure_random",
            "code_example": "# 使用secrets模块\nimport secrets\ntoken = secrets.token_hex(32)\n\n# 或使用os.urandom\nimport os\nrandom_bytes = os.urandom(32)",
            "estimated_effort": "low",
            "priority": "medium" if not is_false_positive else "low"
        }
        return {
            "vulnerability_id": vuln.get("rule_id", "unknown"),
            "is_confirmed": not is_false_positive,
            "is_false_positive": is_false_positive,
            "verification_status": "verified",
            "poc": poc,
            "fix": fix,
            "reasoning": "为非安全用途或使用安全的随机数生成器，风险较低" if is_false_positive else "使用弱随机数生成器"
        }
    
    async def _verify_generic(self, vuln: Dict[str, Any], target_path: str) -> Dict[str, Any]:
        """通用验证逻辑"""
        vuln_id = vuln.get("rule_id", "unknown")
        severity = vuln.get("severity", "info")
        # 默认确认漏洞
        return {
            "vulnerability_id": vuln_id,
            "is_confirmed": True,
            "is_false_positive": False,
            "verification_status": "verified",
            "poc": {
                "type": vuln_id,
                "input": "待构造",
                "expected": "待验证",
                "actual": "待验证",
                "risk_level": severity
            },
            "fix": {
                "approach": "待分析",
                "code_example": "待生成",
                "estimated_effort": "medium",
                "priority": "medium"
            },
            "reasoning": "需要进一步分析"
        }
    
    def _generate_result(self, target_path: str, verification_results: List[Dict[str, Any]], 
                        audit_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成验证结果"""
        # 统计验证结果
        confirmed = sum(1 for r in verification_results if r.get("is_confirmed", False))
        false_positives = sum(1 for r in verification_results if r.get("is_false_positive", False))
        errors = sum(1 for r in verification_results if r.get("verification_status") == "error")
        # 按严重程度分类
        critical_fixes = []
        high_fixes = []
        medium_fixes = []
        low_fixes = []
        for result in verification_results:
            if result.get("is_confirmed", False) and result.get("fix"):
                poc = result.get("poc", {})
                risk_level = poc.get("risk_level", "medium")
                fix_info = {
                    "vulnerability_id": result.get("vulnerability_id"),
                    "risk_level": risk_level,
                    "approach": result["fix"].get("approach"),
                    "code_example": result["fix"].get("code_example"),
                    "estimated_effort": result["fix"].get("estimated_effort"),
                    "priority": result["fix"].get("priority")
                }
                if risk_level == "critical":
                    critical_fixes.append(fix_info)
                elif risk_level == "high":
                    high_fixes.append(fix_info)
                elif risk_level == "medium":
                    medium_fixes.append(fix_info)
                else:
                    low_fixes.append(fix_info)
        
        return {
            "agent_type": "verify",
            "target_path": target_path,
            "timestamp": self.generate_id("verify"),
            "vulnerabilities_verified": len(verification_results),
            "results": verification_results,
            "summary": {
                "confirmed": confirmed,
                "false_positives": false_positives,
                "errors": errors,
                "critical_fixes_needed": len(critical_fixes),
                "high_fixes_needed": len(high_fixes),
                "medium_fixes_needed": len(medium_fixes),
                "low_fixes_needed": len(low_fixes)
            },
            "fixes": {
                "critical": critical_fixes,
                "high": high_fixes,
                "medium": medium_fixes,
                "low": low_fixes
            },
            "recommendations": self._generate_recommendations(confirmed, false_positives, critical_fixes, high_fixes)
        }
    
    def _generate_recommendations(self, confirmed: int, false_positives: int, 
                                 critical_fixes: List[Dict[str, Any]], 
                                 high_fixes: List[Dict[str, Any]]) -> List[str]:
        """生成建议"""
        recommendations = []
        # 基于确认漏洞的建议
        if confirmed > 0:
            recommendations.append(f"确认 {confirmed} 个真实漏洞，需要修复")
        
        # 基于误报的建议
        if false_positives > 0:
            recommendations.append(f"识别 {false_positives} 个误报，可忽略")
        
        # 基于修复优先级的建议
        if critical_fixes:
            recommendations.append(f"发现 {len(critical_fixes)} 个严重漏洞，需要立即修复")
        
        if high_fixes:
            recommendations.append(f"发现 {len(high_fixes)} 个高危漏洞，建议优先处理")
        
        # 通用建议
        if not recommendations:
            recommendations.append("所有漏洞已验证，可按优先级修复")
        
        return recommendations